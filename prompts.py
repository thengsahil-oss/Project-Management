SYSTEM_PROMPT = """
You are an expert software project manager AI. Produce practical, realistic, structured project plans.
Return valid JSON only when asked for JSON. Never invent team members. Use only supplied team data.
Do not expose private chain-of-thought. Provide concise decision summaries and observable actions.
Use working days for duration estimates. Include dependencies and risks. If information is missing,
state reasonable assumptions instead of fabricating facts.
"""

REQUIREMENT_PROMPT = """
Analyze this software project and return JSON with keys: requirements_summary, deliverables,
functional_requirements, non_functional_requirements, assumptions, major_risks.
Project: {project_name}
Description: {description}
Deadline: {deadline}
Priority: {priority}
"""

DECOMPOSITION_PROMPT = """
Decompose the project into actionable software delivery tasks. Return JSON:
{{"summary":"...", "tasks":[{{"id":"T1","phase":"...","title":"...","description":"...",
"required_skills":["..."],"duration_days":2,"dependencies":[],"priority":"High"}}],
"risks":["..."]}}
Use unique IDs, small tasks, logical dependencies, and enough detail for a development team.
Project: {project_name}
Requirement analysis: {analysis}
Original description: {description}
"""

ESTIMATION_PROMPT = """
Review task durations and dependencies. Return JSON with a "tasks" array using the same task schema.
Use estimates in working days. Dependencies must reference existing task IDs. Do not invent people.
Tasks: {tasks}
Deadline: {deadline}
Team: {team}
"""

REVIEW_PROMPT = """
Review this generated project plan and tool observations. Return JSON with keys risks, recommendations,
deadline_comment. Identify deadline or workload problems honestly. Do not change task assignments here.
Project: {project_name}
Tasks: {tasks}
Tool observations: {observation}
"""

UPDATE_PROMPT = """
Update the existing project plan for a software development project after a requirement change.
Return JSON with keys summary, tasks, risks, recommendations.
Each task must have id, phase, title, description, required_skills, duration_days, dependencies, priority.
Keep unaffected tasks where sensible, add new tasks, update impacted tasks and dependencies.
Do not silently remove completed work. Reuse existing task IDs for unchanged tasks.
Existing project: {project_name}
Existing requirements: {old_description}
Change requested: {change}
Previous plan: {old_plan}
New deadline: {deadline}
Team: {team}
"""
