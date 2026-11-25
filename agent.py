import os
import json
import re
from datetime import date, datetime, timedelta
from dotenv import load_dotenv
from groq import Groq

from prompts import SYSTEM_PROMPT, REQUIREMENT_PROMPT, DECOMPOSITION_PROMPT, ESTIMATION_PROMPT, REVIEW_PROMPT, UPDATE_PROMPT
from scheduler import allocate_resources, build_schedule, validate_dependencies

load_dotenv()

class ProjectAgent:
    """Project agent: prompt chain + ReAct-style tool execution + deterministic schedule validation."""

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.client = Groq(api_key=self.api_key) if self.api_key else None

    def parse_team(self, raw):
        members = []
        for line in raw.splitlines():
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 2:
                continue
            name = parts[0]
            skills = [s.strip() for s in parts[1].split(",") if s.strip()]
            try:
                availability = int(parts[2]) if len(parts) > 2 and parts[2] else 100
            except ValueError:
                availability = 100
            members.append({
                "name": name,
                "skills": skills,
                "availability": max(10, min(100, availability))
            })
        return members

    def _chat_json(self, prompt, fallback):
        if not self.client:
            return fallback
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ]
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as exc:
            # A deterministic fallback keeps the project usable if the API is unavailable.
            print("Groq request failed; using fallback:", exc)
            return fallback

    def _fallback_tasks(self, description):
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
                {"id": f"T{i+1}", "phase": "Project delivery", "title": t[0], "description": t[1],
                 "required_skills": t[2], "duration_days": t[3],
                 "dependencies": [f"T{i}"] if i > 1 else [], "priority": "High"}
                for i, t in enumerate(templates)
            ],
            "risks": ["Estimates are initial planning estimates and should be reviewed by the team."]
        }

    def create_plan(self, project_name, description, deadline, team, priority="Normal"):
        fallback = self._fallback_tasks(description)

        # Prompt chain 1: requirement analysis
        analysis = self._chat_json(
            REQUIREMENT_PROMPT.format(project_name=project_name, description=description, deadline=deadline, priority=priority),
            {"requirements_summary": description, "deliverables": ["Working software", "Tested release"], "assumptions": []}
        )

        # Prompt chain 2: task decomposition
        decomposition = self._chat_json(
            DECOMPOSITION_PROMPT.format(project_name=project_name, analysis=json.dumps(analysis), description=description),
            fallback
        )
        tasks = decomposition.get("tasks") or fallback["tasks"]

        # Prompt chain 3: duration and dependency estimation
        estimated = self._chat_json(
            ESTIMATION_PROMPT.format(tasks=json.dumps(tasks), deadline=deadline, team=json.dumps(team)),
            {"tasks": tasks}
        )
        tasks = estimated.get("tasks", tasks)

        # ReAct-style actions: allocate -> schedule -> validate; observations feed final review.
        tasks = allocate_resources(tasks, team)
        tasks = validate_dependencies(tasks)
        tasks, schedule_meta = build_schedule(tasks, deadline)

        observation = {
            "resource_allocation": [{"task": t["id"], "assignee": t.get("assignee")} for t in tasks],
            "schedule": schedule_meta,
            "deadline": deadline
        }
        review = self._chat_json(
            REVIEW_PROMPT.format(project_name=project_name, tasks=json.dumps(tasks), observation=json.dumps(observation)),
            {"risks": decomposition.get("risks", []), "recommendations": ["Review estimates with the assigned team."]}
        )

        return {
            "summary": analysis.get("requirements_summary", decomposition.get("summary", "Project plan generated.")),
            "tasks": tasks,
            "total_duration_days": schedule_meta.get("total_duration_days", 0),
            "deadline_feasible": schedule_meta.get("deadline_feasible", "Review"),
            "resource_summary": schedule_meta.get("resource_summary", {}),
            "risks": review.get("risks", decomposition.get("risks", [])),
            "recommendations": review.get("recommendations", []),
            "assumptions": analysis.get("assumptions", []),
            "agent_observation": observation
        }

    def update_plan(self, current_project, change, new_deadline, team):
        old_plan = current_project.get("plan", {})
        prompt = UPDATE_PROMPT.format(
            project_name=current_project.get("project_name"),
            old_description=current_project.get("description"),
            change=change,
            old_plan=json.dumps(old_plan),
            deadline=new_deadline,
            team=json.dumps(team)
        )
        fallback = self._fallback_tasks(current_project.get("description", "") + " " + change)
        updated = self._chat_json(prompt, fallback)
        tasks = updated.get("tasks") or fallback["tasks"]

        # Preserve completed tasks and their status where task IDs match.
        old_by_id = {t.get("id"): t for t in old_plan.get("tasks", [])}
        for task in tasks:
            previous = old_by_id.get(task.get("id"))
            if previous and previous.get("status") == "Completed":
                task["status"] = "Completed"
        tasks = allocate_resources(tasks, team)
        tasks = validate_dependencies(tasks)
        tasks, meta = build_schedule(tasks, new_deadline)
        return {
            "summary": updated.get("summary", "The plan was revised based on the requirement change."),
            "tasks": tasks,
            "total_duration_days": meta.get("total_duration_days", 0),
            "deadline_feasible": meta.get("deadline_feasible", "Review"),
            "resource_summary": meta.get("resource_summary", {}),
            "risks": updated.get("risks", ["Review changed dependencies and estimates with the team."]),
            "recommendations": updated.get("recommendations", ["Confirm the revised schedule with stakeholders."]),
            "agent_observation": {"change": change, "schedule": meta}
        }
