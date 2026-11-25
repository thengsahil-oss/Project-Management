from datetime import date, datetime, timedelta

def _working_day(d):
    return d.weekday() < 5

def add_working_days(start, count):
    """Return end date after count working days; count=1 means start if weekday."""
    current = start
    remaining = max(1, int(count))
    while not _working_day(current):
        current += timedelta(days=1)
    while remaining > 1:
        current += timedelta(days=1)
        if _working_day(current):
            remaining -= 1
    return current

def allocate_resources(tasks, team):
    """Greedy skill matching with a lightweight workload balancing score."""
    workload = {m["name"]: 0 for m in team}
    for task in tasks:
        required = [s.lower() for s in task.get("required_skills", [])]
        best_member, best_score = None, -1
        for member in team:
            skills = [s.lower() for s in member.get("skills", [])]
            overlap = sum(1 for req in required if any(req in skill or skill in req for skill in skills))
            availability = member.get("availability", 100) / 100
            # Skill overlap dominates; workload and availability break ties.
            score = overlap * 10 + availability * 2 - workload[member["name"]] * 0.25
            if score > best_score:
                best_member, best_score = member, score
        if best_member:
            task["assignee"] = best_member["name"]
            task["allocation_match"] = "Skill match" if best_score >= 10 else "Best available match; verify skills"
            workload[best_member["name"]] += max(1, int(task.get("duration_days", 1)))
        else:
            task["assignee"] = "Unassigned"
            task["allocation_match"] = "No team members supplied"
        task.setdefault("status", "Not started")
    return tasks

def validate_dependencies(tasks):
    ids = {t.get("id") for t in tasks}
    for task in tasks:
        task["dependencies"] = [d for d in task.get("dependencies", []) if d in ids and d != task.get("id")]
    return tasks

def build_schedule(tasks, deadline):
    try:
        deadline_date = date.fromisoformat(str(deadline)[:10])
    except Exception:
        deadline_date = date.today() + timedelta(days=30)

    by_id = {t["id"]: t for t in tasks}
    end_dates = {}
    start_dates = {}
    # Repeated passes schedule tasks after their dependencies.
    pending = list(tasks)
    today = date.today()
    cursor = today
    for _ in range(len(tasks) + 2):
        changed = False
        for task in pending[:]:
            deps = task.get("dependencies", [])
            if all(dep in end_dates for dep in deps):
                start = max([today] + [end_dates[d] + timedelta(days=1) for d in deps])
                while start.weekday() >= 5:
                    start += timedelta(days=1)
                duration = max(1, int(task.get("duration_days", 1)))
                end = add_working_days(start, duration)
                start_dates[task["id"]] = start
                end_dates[task["id"]] = end
                task["start_date"] = start.isoformat()
                task["end_date"] = end.isoformat()
                pending.remove(task)
                changed = True
        if not changed:
            break

    # Cyclic or unresolved dependencies are flagged and placed sequentially at the end.
    for task in pending:
        start = max(end_dates.values()) + timedelta(days=1) if end_dates else today
        while start.weekday() >= 5:
            start += timedelta(days=1)
        end = add_working_days(start, max(1, int(task.get("duration_days", 1))))
        task["start_date"], task["end_date"] = start.isoformat(), end.isoformat()
        task["schedule_warning"] = "Dependency cycle or unresolved dependency; review manually."
        end_dates[task["id"]] = end

    project_end = max(end_dates.values()) if end_dates else today
    total_days = sum(max(1, int(t.get("duration_days", 1))) for t in tasks)
    resource_summary = {}
    for task in tasks:
        name = task.get("assignee", "Unassigned")
        resource_summary[name] = resource_summary.get(name, 0) + int(task.get("duration_days", 1))

    feasible = "Yes" if project_end <= deadline_date else "No – deadline at risk"
    meta = {
        "total_duration_days": total_days,
        "projected_end_date": project_end.isoformat(),
        "deadline": deadline_date.isoformat(),
        "deadline_feasible": feasible,
        "resource_summary": resource_summary
    }
    return tasks, meta
