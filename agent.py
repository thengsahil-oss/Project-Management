import copy
import json
import logging
import os
import re
from datetime import date
from typing import Any, Callable

from dotenv import load_dotenv
from groq import Groq, GroqError

from prompts import (
    DECOMPOSITION_PROMPT,
    ESTIMATION_PROMPT,
    PROMPT_DEMO_FEW_SHOT,
    PROMPT_DEMO_ONE_SHOT,
    PROMPT_DEMO_ZERO_SHOT,
    REQUIREMENT_PROMPT,
    REVIEW_PROMPT,
    STEP_BACK_PROMPT,
    SYSTEM_PROMPT,
    UPDATE_PROMPT,
)
from scheduler import allocate_resources, build_schedule, validate_dependencies

load_dotenv()

logger = logging.getLogger(__name__)

MAX_PROJECT_NAME_LENGTH = 120
MAX_DESCRIPTION_LENGTH = 4000
MAX_CHANGE_LENGTH = 2000
MAX_TEAM_MEMBERS = 20
MAX_TASKS = 40
MAX_PROMPT_CONTEXT_LENGTH = 50000
VALID_PRIORITIES = {"Low", "Normal", "Medium", "High", "Critical"}
INSTRUCTION_OVERRIDE = re.compile(
    r"\b(ignore|disregard)\b.{0,40}\b(previous|prior|system)\b"
    r"|\b(reveal|show)\b.{0,30}\b(system prompt|hidden prompt|api key|secret)\b",
    re.IGNORECASE | re.DOTALL,
)


class ModelOutputError(ValueError):
    """Raised when an LLM response does not match the expected JSON contract."""


class ProjectAgent:
    """Prompt-chained project planner with validated LLM output and Python tools."""

    def __init__(self) -> None:
        self.api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
        self.client = Groq(api_key=self.api_key) if self.api_key else None

    @staticmethod
    def _required_text(value: Any, label: str, max_length: int) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{label} is required.")
        cleaned = value.strip()
        if len(cleaned) > max_length:
            raise ValueError(f"{label} must be {max_length} characters or fewer.")
        if "\x00" in cleaned:
            raise ValueError(f"{label} contains an unsupported control character.")
        return cleaned

    @staticmethod
    def _validate_date(value: Any) -> str:
        if isinstance(value, date):
            parsed = value
        elif isinstance(value, str):
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                raise ValueError("Deadline must be a valid ISO date (YYYY-MM-DD).")
            try:
                parsed = date.fromisoformat(value)
            except ValueError as exc:
                raise ValueError("Deadline must be a valid ISO date (YYYY-MM-DD).") from exc
        else:
            raise ValueError("Deadline must be a valid ISO date (YYYY-MM-DD).")
        if parsed < date.today():
            raise ValueError("Deadline cannot be in the past.")
        return parsed.isoformat()

    def _validate_team(self, team: Any) -> list[dict[str, Any]]:
        if not isinstance(team, list) or not team:
            raise ValueError("Add at least one team member.")
        if len(team) > MAX_TEAM_MEMBERS:
            raise ValueError(f"Team size cannot exceed {MAX_TEAM_MEMBERS} members.")

        validated: list[dict[str, Any]] = []
        seen_names: set[str] = set()
        for index, member in enumerate(team, start=1):
            if not isinstance(member, dict):
                raise ValueError(f"Team member {index} must be an object.")
            name = self._required_text(member.get("name"), f"Team member {index} name", 80)
            if any(ord(char) < 32 for char in name):
                raise ValueError(f"Team member {index} name contains an unsupported character.")
            if name.casefold() in seen_names:
                raise ValueError(f"Team member name '{name}' is duplicated.")
            seen_names.add(name.casefold())

            skills = member.get("skills")
            if not isinstance(skills, list) or not skills or len(skills) > 15:
                raise ValueError(f"{name} must have between 1 and 15 skills.")
            clean_skills = []
            for skill in skills:
                clean_skill = self._required_text(skill, f"{name} skill", 60)
                if any(ord(char) < 32 for char in clean_skill):
                    raise ValueError(f"{name} has a skill containing an unsupported character.")
                clean_skills.append(clean_skill)

            availability = member.get("availability", 100)
            if isinstance(availability, bool) or not isinstance(availability, int):
                raise ValueError(f"{name} availability must be a whole number from 1 to 100.")
            if not 1 <= availability <= 100:
                raise ValueError(f"{name} availability must be between 1 and 100.")
            validated.append(
                {"name": name, "skills": clean_skills, "availability": availability}
            )
        return validated

    def parse_team(self, raw: str) -> list[dict[str, Any]]:
        if not isinstance(raw, str):
            raise ValueError("Team input must be text.")
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        if not lines:
            raise ValueError("Add at least one team member using the required format.")
        if len(lines) > MAX_TEAM_MEMBERS:
            raise ValueError(f"Team size cannot exceed {MAX_TEAM_MEMBERS} members.")

        members = []
        for line_number, line in enumerate(lines, start=1):
            parts = [part.strip() for part in line.split("|")]
            if len(parts) not in (2, 3):
                raise ValueError(
                    f"Team line {line_number} must use Name | skill1, skill2 | availability."
                )
            name, skills_text = parts[:2]
            skills = [skill.strip() for skill in skills_text.split(",") if skill.strip()]
            if len(parts) == 3 and parts[2]:
                try:
                    availability = int(parts[2])
                except ValueError as exc:
                    raise ValueError(
                        f"Team line {line_number} availability must be a whole number."
                    ) from exc
            else:
                availability = 100
            members.append(
                {"name": name, "skills": skills, "availability": availability}
            )
        return self._validate_team(members)

    def _validate_project_input(
        self,
        project_name: Any,
        description: Any,
        deadline: Any,
        team: Any,
        priority: Any = "Normal",
    ) -> tuple[str, str, str, list[dict[str, Any]], str]:
        clean_name = self._required_text(
            project_name, "Project name", MAX_PROJECT_NAME_LENGTH
        )
        clean_description = self._required_text(
            description, "Project requirements", MAX_DESCRIPTION_LENGTH
        )
        clean_deadline = self._validate_date(deadline)
        clean_team = self._validate_team(team)
        if not isinstance(priority, str) or priority not in VALID_PRIORITIES:
            raise ValueError("Priority must be Low, Normal, Medium, High, or Critical.")
        return clean_name, clean_description, clean_deadline, clean_team, priority

    @staticmethod
    def _json_context(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

    @staticmethod
    def _validate_string_list(
        data: dict[str, Any], key: str, *, required: bool = False
    ) -> list[str]:
        value = data.get(key)
        if value is None and not required:
            return []
        if not isinstance(value, list) or len(value) > 30:
            raise ModelOutputError(f"'{key}' must be a list of at most 30 strings.")
        clean_values = []
        for item in value:
            if not isinstance(item, str) or not item.strip() or len(item) > 500:
                raise ModelOutputError(f"'{key}' contains an invalid string.")
            clean_values.append(item.strip())
        return clean_values

    @classmethod
    def _validate_analysis(cls, data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise ModelOutputError("Analysis output must be a JSON object.")
        summary = data.get("requirements_summary")
        if not isinstance(summary, str) or not summary.strip() or len(summary) > 1200:
            raise ModelOutputError("'requirements_summary' must be a non-empty string.")
        return {
            "requirements_summary": summary.strip(),
            "deliverables": cls._validate_string_list(data, "deliverables"),
            "functional_requirements": cls._validate_string_list(
                data, "functional_requirements"
            ),
            "non_functional_requirements": cls._validate_string_list(
                data, "non_functional_requirements"
            ),
            "assumptions": cls._validate_string_list(data, "assumptions"),
            "major_risks": cls._validate_string_list(data, "major_risks"),
        }

    @classmethod
    def _validate_step_back(cls, data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise ModelOutputError("Step-back output must be a JSON object.")
        return {
            "principles": cls._validate_string_list(data, "principles", required=True),
            "constraints": cls._validate_string_list(data, "constraints"),
            "questions": cls._validate_string_list(data, "questions"),
        }

    @classmethod
    def _validate_tasks_response(
        cls, data: Any, *, require_summary: bool = False
    ) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise ModelOutputError("Task output must be a JSON object.")
        raw_tasks = data.get("tasks")
        if not isinstance(raw_tasks, list) or not 1 <= len(raw_tasks) <= MAX_TASKS:
            raise ModelOutputError(f"'tasks' must contain between 1 and {MAX_TASKS} tasks.")

        tasks = []
        ids: set[str] = set()
        for index, raw_task in enumerate(raw_tasks, start=1):
            if not isinstance(raw_task, dict):
                raise ModelOutputError(f"Task {index} must be a JSON object.")
            task_id = raw_task.get("id")
            if not isinstance(task_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", task_id):
                raise ModelOutputError(f"Task {index} has an invalid ID.")
            if task_id in ids:
                raise ModelOutputError(f"Task ID '{task_id}' is duplicated.")
            ids.add(task_id)

            task: dict[str, Any] = {"id": task_id}
            for key, maximum in (
                ("phase", 100),
                ("title", 180),
                ("description", 1000),
            ):
                value = raw_task.get(key)
                if not isinstance(value, str) or not value.strip() or len(value) > maximum:
                    raise ModelOutputError(f"Task {task_id} has an invalid '{key}'.")
                task[key] = value.strip()

            skills = raw_task.get("required_skills")
            if not isinstance(skills, list) or len(skills) > 15:
                raise ModelOutputError(
                    f"Task {task_id} 'required_skills' must be a list of at most 15 strings."
                )
            task["required_skills"] = []
            for skill in skills:
                if not isinstance(skill, str) or not skill.strip() or len(skill) > 60:
                    raise ModelOutputError(f"Task {task_id} has an invalid required skill.")
                task["required_skills"].append(skill.strip())

            duration = raw_task.get("duration_days")
            if isinstance(duration, bool) or not isinstance(duration, int) or not 1 <= duration <= 260:
                raise ModelOutputError(
                    f"Task {task_id} duration must be a whole number from 1 to 260."
                )
            task["duration_days"] = duration

            dependencies = raw_task.get("dependencies")
            if not isinstance(dependencies, list) or len(dependencies) > MAX_TASKS:
                raise ModelOutputError(f"Task {task_id} dependencies must be a list of task IDs.")
            if any(not isinstance(dep, str) for dep in dependencies):
                raise ModelOutputError(f"Task {task_id} has an invalid dependency ID.")
            task["dependencies"] = list(dict.fromkeys(dependencies))

            priority = raw_task.get("priority")
            if not isinstance(priority, str) or priority not in VALID_PRIORITIES:
                raise ModelOutputError(f"Task {task_id} has an unsupported priority.")
            task["priority"] = priority
            tasks.append(task)

        for task in tasks:
            for dependency in task["dependencies"]:
                if dependency not in ids or dependency == task["id"]:
                    raise ModelOutputError(
                        f"Task {task['id']} references an unknown or self dependency."
                    )

        graph = {task["id"]: task["dependencies"] for task in tasks}
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(task_id: str) -> None:
            if task_id in visiting:
                raise ModelOutputError("Task dependencies contain a cycle.")
            if task_id in visited:
                return
            visiting.add(task_id)
            for dependency in graph[task_id]:
                visit(dependency)
            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in graph:
            visit(task_id)

        result: dict[str, Any] = {"tasks": tasks}
        summary = data.get("summary")
        if require_summary and (
            not isinstance(summary, str) or not summary.strip() or len(summary) > 1200
        ):
            raise ModelOutputError("'summary' must be a non-empty string.")
        if isinstance(summary, str) and summary.strip():
            result["summary"] = summary.strip()[:1200]
        result["risks"] = cls._validate_string_list(data, "risks")
        result["recommendations"] = cls._validate_string_list(data, "recommendations")
        return result

    @classmethod
    def _validate_review(cls, data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise ModelOutputError("Review output must be a JSON object.")
        comment = data.get("deadline_comment", "")
        if not isinstance(comment, str) or len(comment) > 1200:
            raise ModelOutputError("'deadline_comment' must be a string.")
        return {
            "risks": cls._validate_string_list(data, "risks"),
            "recommendations": cls._validate_string_list(data, "recommendations"),
            "deadline_comment": comment.strip(),
        }

    def _chat_json(
        self,
        stage: str,
        prompt: str,
        fallback: dict[str, Any],
        validator: Callable[[Any], dict[str, Any]],
        warnings: list[str],
    ) -> tuple[dict[str, Any], bool]:
        if self.client is None:
            warnings.append(
                f"{stage}: Groq is not configured; deterministic fallback was used."
            )
            return copy.deepcopy(fallback), False

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            )
            content = response.choices[0].message.content
        except (GroqError, IndexError, AttributeError, TypeError) as exc:
            logger.warning("%s stage failed: %s", stage, type(exc).__name__)
            warnings.append(
                f"{stage}: model request failed ({type(exc).__name__}); deterministic fallback was used."
            )
            return copy.deepcopy(fallback), False

        if not isinstance(content, str):
            warnings.append(
                f"{stage}: model returned no text; deterministic fallback was used."
            )
            return copy.deepcopy(fallback), False
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            warnings.append(
                f"{stage}: model output was not valid JSON; deterministic fallback was used."
            )
            return copy.deepcopy(fallback), False
        try:
            return validator(parsed), True
        except ModelOutputError as exc:
            logger.warning("%s output failed validation: %s", stage, exc)
            warnings.append(
                f"{stage}: model output failed validation ({exc}); deterministic fallback was used."
            )
            return copy.deepcopy(fallback), False

    @staticmethod
    def _prompt_injection_warning(text: str) -> list[str]:
        if INSTRUCTION_OVERRIDE.search(text):
            return [
                "Instruction-like text detected; it was treated as project data, not as an instruction."
            ]
        return []

    @staticmethod
    def _fallback_step_back() -> dict[str, Any]:
        return {
            "principles": [
                "Define a testable first release.",
                "Sequence work around dependencies.",
                "Make assumptions and delivery risks reviewable.",
            ],
            "constraints": ["Use working-day estimates.", "Use only the supplied team."],
            "questions": ["Confirm scope and acceptance criteria with stakeholders."],
        }

    @staticmethod
    def _fallback_analysis(description: str) -> dict[str, Any]:
        return {
            "requirements_summary": description[:700],
            "deliverables": ["Working software", "Tested release"],
            "functional_requirements": [],
            "non_functional_requirements": [],
            "assumptions": ["The supplied project description is the current scope."],
            "major_risks": ["Initial scope and estimates should be reviewed by the team."],
        }

    def _fallback_tasks(self, description: str) -> dict[str, Any]:
        lower = description.lower()
        templates = [
            ("Requirements analysis", "Analyze requirements and define acceptance criteria.", ["analysis", "documentation"], 2),
            ("System design", "Design application architecture, modules and API contracts.", ["architecture", "design"], 3),
            ("Database design", "Create database schema, relationships and migrations.", ["database", "sql"], 2),
            ("Backend development", "Implement business logic, APIs and authentication.", ["python", "backend", "api"], 6),
            ("Frontend development", "Build user interface and connect frontend to APIs.", ["frontend", "react", "ui"], 6),
            ("Integration", "Integrate modules and resolve interface issues.", ["integration", "api"], 3),
            ("Testing and QA", "Test core workflows, fix defects and validate acceptance criteria.", ["testing", "qa"], 4),
            ("Deployment", "Prepare deployment configuration and release the application.", ["devops", "deployment"], 2),
        ]
        if "payment" in lower:
            templates.insert(6, ("Payment integration", "Integrate and test the payment workflow.", ["payment", "api"], 3))
        if "mobile" in lower:
            templates.insert(5, ("Mobile implementation", "Implement responsive or mobile application screens.", ["mobile", "frontend"], 4))
        return {
            "summary": "The project is organized into analysis, design, implementation, integration, testing and release.",
            "tasks": [
                {
                    "id": f"T{i + 1}",
                    "phase": "Project delivery",
                    "title": template[0],
                    "description": template[1],
                    "required_skills": template[2],
                    "duration_days": template[3],
                    "dependencies": [f"T{i}"] if i > 1 else [],
                    "priority": "High",
                }
                for i, template in enumerate(templates)
            ],
            "risks": [
                "Estimates are initial planning estimates and should be reviewed by the team."
            ],
        }

    @staticmethod
    def _stage_record(stage: str, technique: str, used_model: bool) -> dict[str, str]:
        return {
            "stage": stage,
            "technique": technique,
            "source": "Groq LLM" if used_model else "Deterministic fallback",
        }

    @staticmethod
    def evaluate_plan(
        tasks: list[dict[str, Any]],
        team: list[dict[str, Any]],
        schedule_meta: dict[str, Any],
    ) -> dict[str, Any]:
        task_ids = [task.get("id") for task in tasks]
        valid_ids = set(task_ids)
        team_names = {member.get("name") for member in team}
        checks = [
            {
                "name": "Task list is present and within the supported size",
                "passed": 1 <= len(tasks) <= MAX_TASKS,
            },
            {
                "name": "Task IDs are unique",
                "passed": len(task_ids) == len(valid_ids),
            },
            {
                "name": "Durations are positive working-day integers",
                "passed": all(
                    isinstance(task.get("duration_days"), int)
                    and not isinstance(task.get("duration_days"), bool)
                    and 1 <= task.get("duration_days", 0) <= 260
                    for task in tasks
                ),
            },
            {
                "name": "Dependencies reference tasks in this plan",
                "passed": all(
                    dependency in valid_ids and dependency != task.get("id")
                    for task in tasks
                    for dependency in task.get("dependencies", [])
                ),
            },
            {
                "name": "Assignments use supplied team members",
                "passed": all(
                    task.get("assignee") in team_names | {"Unassigned"} for task in tasks
                ),
            },
            {
                "name": "Schedule includes deadline feasibility",
                "passed": schedule_meta.get("deadline_feasible") in {
                    "Yes",
                    "No – deadline at risk",
                },
            },
        ]
        passed = sum(check["passed"] for check in checks)
        return {
            "score": round(100 * passed / len(checks)),
            "passed": passed,
            "total": len(checks),
            "checks": checks,
        }

    def create_plan(
        self,
        project_name: str,
        description: str,
        deadline: str,
        team: list[dict[str, Any]],
        priority: str = "Normal",
    ) -> dict[str, Any]:
        project_name, description, deadline, team, priority = self._validate_project_input(
            project_name, description, deadline, team, priority
        )
        warnings = self._prompt_injection_warning(description)
        context = self._json_context(
            {
                "project_name": project_name,
                "description": description,
                "deadline": deadline,
                "priority": priority,
                "team": team,
            }
        )
        stages = []

        step_back_fallback = self._fallback_step_back()
        step_back, used_model = self._chat_json(
            "Step-back",
            STEP_BACK_PROMPT.format(project_context=context),
            step_back_fallback,
            self._validate_step_back,
            warnings,
        )
        stages.append(self._stage_record("Step-back", "Step-back prompting", used_model))

        analysis_fallback = self._fallback_analysis(description)
        analysis, used_model = self._chat_json(
            "Requirement analysis",
            REQUIREMENT_PROMPT.format(
                project_context=context,
                step_back=self._json_context(step_back),
            ),
            analysis_fallback,
            self._validate_analysis,
            warnings,
        )
        stages.append(
            self._stage_record("Requirement analysis", "Zero-shot + system role", used_model)
        )

        fallback_tasks = self._fallback_tasks(description)
        decomposition, used_model = self._chat_json(
            "Task decomposition",
            DECOMPOSITION_PROMPT.format(
                project_context=context,
                step_back=self._json_context(step_back),
                analysis=self._json_context(analysis),
            ),
            fallback_tasks,
            lambda value: self._validate_tasks_response(value, require_summary=True),
            warnings,
        )
        stages.append(
            self._stage_record("Task decomposition", "One-shot prompting", used_model)
        )

        estimation_fallback = {"tasks": decomposition["tasks"]}
        estimated, used_model = self._chat_json(
            "Effort estimation",
            ESTIMATION_PROMPT.format(
                tasks=self._json_context(decomposition["tasks"]),
                deadline=deadline,
                team=self._json_context(team),
            ),
            estimation_fallback,
            self._validate_tasks_response,
            warnings,
        )
        stages.append(
            self._stage_record("Effort estimation", "Few-shot prompting", used_model)
        )

        tasks = allocate_resources(estimated["tasks"], team)
        tasks = validate_dependencies(tasks)
        tasks, schedule_meta = build_schedule(tasks, deadline)
        dependency_issues = [
            task["schedule_warning"]
            for task in tasks
            if task.get("schedule_warning")
        ]
        react_trace = [
            {
                "action": "allocate_resources",
                "observation": {
                    "assigned": sum(task.get("assignee") != "Unassigned" for task in tasks),
                    "unassigned": sum(task.get("assignee") == "Unassigned" for task in tasks),
                },
            },
            {
                "action": "validate_dependencies",
                "observation": {
                    "dependency_count": sum(len(task.get("dependencies", [])) for task in tasks),
                    "schedule_warnings": dependency_issues,
                },
            },
            {"action": "build_schedule", "observation": schedule_meta},
        ]
        observation = {
            "resource_allocation": [
                {"task": task["id"], "assignee": task.get("assignee")}
                for task in tasks
            ],
            "schedule": schedule_meta,
            "react_trace": react_trace,
            "deadline": deadline,
        }
        review_fallback = {
            "risks": decomposition.get("risks", []),
            "recommendations": ["Review estimates with the assigned team."],
            "deadline_comment": schedule_meta["deadline_feasible"],
        }
        review, used_model = self._chat_json(
            "Plan review",
            REVIEW_PROMPT.format(
                project_name=project_name,
                tasks=self._json_context(tasks),
                observation=self._json_context(observation),
            ),
            review_fallback,
            self._validate_review,
            warnings,
        )
        stages.append(
            self._stage_record("Plan review", "Structured output review", used_model)
        )

        sources = {stage["source"] for stage in stages}
        generation_mode = (
            "Groq LLM"
            if sources == {"Groq LLM"}
            else "Deterministic fallback"
            if sources == {"Deterministic fallback"}
            else "Hybrid LLM and fallback"
        )
        evaluation = self.evaluate_plan(tasks, team, schedule_meta)
        return {
            "summary": analysis.get(
                "requirements_summary",
                decomposition.get("summary", "Project plan generated."),
            ),
            "tasks": tasks,
            "total_duration_days": schedule_meta.get("total_duration_days", 0),
            "deadline_feasible": schedule_meta.get("deadline_feasible", "Review"),
            "resource_summary": schedule_meta.get("resource_summary", {}),
            "risks": list(dict.fromkeys(review.get("risks", []) + analysis["major_risks"])),
            "recommendations": review.get("recommendations", []),
            "assumptions": analysis.get("assumptions", []),
            "generation_mode": generation_mode,
            "warnings": warnings,
            "response_evaluation": evaluation,
            "agent_observation": {
                **observation,
                "step_back_summary": step_back,
                "prompt_chain": stages,
            },
        }

    def demonstrate_prompting(
        self, description: str, technique: str
    ) -> dict[str, Any]:
        description = self._required_text(
            description, "Prompt demo input", MAX_CHANGE_LENGTH
        )
        project_context = self._json_context({"description": description})
        prompts = {
            "Zero-shot": PROMPT_DEMO_ZERO_SHOT,
            "One-shot": PROMPT_DEMO_ONE_SHOT,
            "Few-shot": PROMPT_DEMO_FEW_SHOT,
        }
        if technique not in prompts:
            raise ValueError("Choose Zero-shot, One-shot, or Few-shot prompting.")

        fallback = self._fallback_analysis(description)
        warnings = self._prompt_injection_warning(description)
        result, used_model = self._chat_json(
            f"{technique} demonstration",
            prompts[technique].format(project_context=project_context),
            fallback,
            self._validate_analysis,
            warnings,
        )
        return {
            "technique": technique,
            "source": "Groq LLM" if used_model else "Deterministic fallback",
            "structured_output_valid": True,
            "result": result,
            "warnings": warnings,
        }

    def update_plan(
        self,
        current_project: dict[str, Any],
        change: str,
        new_deadline: str,
        team: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not isinstance(current_project, dict):
            raise ValueError("A saved project is required to update its plan.")
        project_name = self._required_text(
            current_project.get("project_name"), "Project name", MAX_PROJECT_NAME_LENGTH
        )
        old_description = self._required_text(
            current_project.get("description"),
            "Existing project requirements",
            MAX_DESCRIPTION_LENGTH,
        )
        change = self._required_text(change, "Requirement change", MAX_CHANGE_LENGTH)
        new_deadline = self._validate_date(new_deadline)
        team = self._validate_team(team)
        old_plan = current_project.get("plan", {})
        if not isinstance(old_plan, dict):
            raise ValueError("Saved project plan must be a JSON object.")
        old_plan_json = self._json_context(old_plan)
        if len(old_plan_json) > MAX_PROMPT_CONTEXT_LENGTH:
            raise ValueError("Saved plan is too large to safely include in an update prompt.")

        warnings = self._prompt_injection_warning(change)
        fallback = self._fallback_tasks(f"{old_description} {change}")
        updated, used_model = self._chat_json(
            "Requirement update",
            UPDATE_PROMPT.format(
                project_context=self._json_context(
                    {"project_name": project_name, "requirements": old_description}
                ),
                change_context=self._json_context({"change": change}),
                old_plan=old_plan_json,
                deadline=new_deadline,
                team=self._json_context(team),
            ),
            fallback,
            lambda value: self._validate_tasks_response(value, require_summary=True),
            warnings,
        )

        old_by_id = {
            task.get("id"): task
            for task in old_plan.get("tasks", [])
            if isinstance(task, dict)
        }
        tasks = updated["tasks"]
        for task in tasks:
            previous = old_by_id.get(task.get("id"))
            if previous and previous.get("status") == "Completed":
                task["status"] = "Completed"
        tasks = allocate_resources(tasks, team)
        tasks = validate_dependencies(tasks)
        tasks, schedule_meta = build_schedule(tasks, new_deadline)
        evaluation = self.evaluate_plan(tasks, team, schedule_meta)
        return {
            "summary": updated.get(
                "summary", "The plan was revised based on the requirement change."
            ),
            "tasks": tasks,
            "total_duration_days": schedule_meta.get("total_duration_days", 0),
            "deadline_feasible": schedule_meta.get("deadline_feasible", "Review"),
            "resource_summary": schedule_meta.get("resource_summary", {}),
            "risks": updated.get(
                "risks", ["Review changed dependencies and estimates with the team."]
            ),
            "recommendations": updated.get(
                "recommendations", ["Confirm the revised schedule with stakeholders."]
            ),
            "generation_mode": "Groq LLM" if used_model else "Deterministic fallback",
            "warnings": warnings,
            "response_evaluation": evaluation,
            "agent_observation": {
                "change": change,
                "schedule": schedule_meta,
                "react_trace": [
                    {
                        "action": "allocate_resources",
                        "observation": {
                            "assigned": sum(
                                task.get("assignee") != "Unassigned" for task in tasks
                            )
                        },
                    },
                    {"action": "validate_dependencies", "observation": "complete"},
                    {"action": "build_schedule", "observation": schedule_meta},
                ],
                "prompt_chain": [
                    self._stage_record(
                        "Requirement update",
                        "System prompt + structured output",
                        used_model,
                    )
                ],
            },
        }
