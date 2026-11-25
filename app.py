import html
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from agent import ProjectAgent
from memory import ProjectMemory

st.set_page_config(page_title="Coders | Project Workspace", page_icon="◒", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

    :root {
        --ink: #171717;
        --muted: #777875;
        --line: #e8e8e5;
        --paper: #f0f0ee;
        --white: #ffffff;
    }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; color: var(--ink); }
    [data-testid="stAppViewContainer"] { background: var(--paper); }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stMain"] { padding-top: 1.3rem; }
    .block-container { max-width: 1540px; padding: 1.4rem 2.2rem 3rem; }
    [data-testid="stSidebar"] { background: #fafaf9; border-right: 1px solid #e6e6e3; }
    [data-testid="stSidebar"] > div:first-child { padding: 1.35rem 1rem; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #777875; }
    [data-testid="stRadio"] label p { font-size: .9rem; font-weight: 500; }
    [data-testid="stRadio"] > div { gap: .3rem; }
    h1, h2, h3 { font-family: 'Manrope', sans-serif !important; color: var(--ink); letter-spacing: -.045em; }
    h1 { font-size: 2rem !important; font-weight: 600 !important; }
    h2 { font-size: 1.25rem !important; font-weight: 600 !important; }
    h3 { font-size: 1rem !important; font-weight: 600 !important; }
    [data-testid="stVerticalBlockBorderWrapper"] { background: white; border-color: var(--line); border-radius: 20px; }
    [data-testid="stMetric"] { background: #fff; padding: .85rem 1rem; border: 1px solid var(--line); border-radius: 16px; }
    [data-testid="stMetricLabel"] { color: #777875; font-size: .78rem; }
    [data-testid="stMetricValue"] { font-family: 'Manrope', sans-serif; font-size: 1.5rem; font-weight: 600; }
    [data-testid="stButton"] button, [data-testid="stFormSubmitButton"] button {
        border-radius: 999px; min-height: 2.55rem; font-weight: 600; border-color: #dededb;
    }
    [data-testid="stButton"] button[kind="primary"], [data-testid="stFormSubmitButton"] button[kind="primary"] {
        background: #171717; color: #fff; border-color: #171717;
    }
    [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea, [data-testid="stDateInput"] input,
    [data-testid="stSelectbox"] [data-baseweb="select"] > div { border-radius: 12px; }
    [data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 14px; overflow: hidden; }
    .brand { display:flex; align-items:center; gap:10px; padding: .25rem .4rem 1.8rem; }
    .brand-symbol { display:grid; place-items:center; width:34px; height:34px; border-radius:12px; background:#171717; color:#fff; font-size:20px; }
    .brand-name { font-family:'Manrope',sans-serif; font-size:1rem; font-weight:800; letter-spacing:-.04em; color:#171717; }
    .eyebrow { color:#858681; font-size:.68rem; font-weight:700; letter-spacing:.13em; text-transform:uppercase; }
    .page-kicker { color:#82837f; font-size:.8rem; margin-top:-.6rem; }
    .project-chip { display:inline-flex; align-items:center; gap:7px; padding:7px 11px; border:1px solid #e5e5e2; border-radius:999px; background:#fff; color:#454642; font-size:.77rem; }
    .live-dot { height:7px; width:7px; border-radius:50%; background:#262626; display:inline-block; }
    .timeline-note { color:#777875; font-size:.78rem; }
    .task-label { color:#323330; font-size:.82rem; font-weight:600; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .task-sub { color:#8a8b87; font-size:.7rem; }
    .task-track { height:12px; width:100%; background:#f0f0ee; border-radius:10px; overflow:hidden; }
    .task-bar { height:100%; background:#1b1b1b; border-radius:10px; min-width:8px; }
    .mini-line { height:1px; background:#eeeeeb; margin:.85rem 0; }
    .empty-mark { width:48px; height:48px; border-radius:16px; display:grid; place-items:center; color:white; background:#171717; font-size:23px; margin-bottom:1rem; }
    .empty-copy { color:#777875; max-width:38rem; line-height:1.6; }
    .team-panel { min-height:180px; padding:1.35rem 1.5rem; border-radius:20px; color:#fff; background:radial-gradient(ellipse at 82% 110%, #343434 0, #181818 36%, #101010 75%); }
    .team-panel-head { display:flex; align-items:center; justify-content:space-between; margin-bottom:1.55rem; }
    .team-panel-title { font-family:'Manrope',sans-serif; font-size:1.15rem; font-weight:600; letter-spacing:-.04em; }
    .team-panel-count { font-size:.72rem; color:#d5d5d2; border:1px solid #555; border-radius:999px; padding:4px 9px; }
    .team-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(125px,1fr)); gap:1rem; }
    .team-person { border-top:1px solid #424242; padding-top:.85rem; }
    .team-avatar { display:grid; place-items:center; width:34px; height:34px; border-radius:50%; background:#303030; color:#fff; font-size:.72rem; font-weight:700; margin-bottom:.55rem; }
    .team-person-name { font-size:.8rem; font-weight:600; color:#fff; }
    .team-person-skills { color:#aaa; font-size:.68rem; margin-top:.15rem; }
    @media (max-width: 850px) {
        .block-container { padding: 1rem .8rem 2rem; }
        h1 { font-size:1.65rem !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

memory = ProjectMemory()
agent = ProjectAgent()
project_names = memory.list_projects()

if st.session_state.pop("request_new_project", False):
    st.session_state["workspace_page"] = "New project"
if st.session_state.pop("request_schedule", False):
    st.session_state["workspace_page"] = "Schedule"

with st.sidebar:
    st.markdown(
        '<div class="brand"><div class="brand-symbol">◒</div><div class="brand-name">Coders</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="eyebrow">Workspace</div>', unsafe_allow_html=True)
    page = st.radio(
        "Workspace navigation",
        ["Overview", "Schedule", "New project", "Update requirements", "Project memory"],
        label_visibility="collapsed",
        format_func=lambda item: {
            "Overview": "⌂   Overview",
            "Schedule": "▦   Schedule",
            "New project": "＋   New project",
            "Update requirements": "↻   Update plan",
            "Project memory": "▤   Project memory",
        }[item],
        key="workspace_page",
    )
    page = st.session_state["workspace_page"]
    st.markdown('<div class="mini-line"></div>', unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">Current project</div>', unsafe_allow_html=True)
    if project_names:
        active = st.session_state.get("active_project")
        initial = project_names.index(active) if active in project_names else 0
        selected_name = st.selectbox(
            "Choose a project",
            project_names,
            index=initial,
            label_visibility="collapsed",
        )
        st.session_state["active_project"] = selected_name
    else:
        selected_name = None
        st.caption("Create a project to see its schedule and team.")
    st.markdown('<div class="mini-line"></div>', unsafe_allow_html=True)
    st.caption("AI planning · Resource allocation · Project memory")
    st.markdown("[Get a Groq API key](https://console.groq.com/keys)")

project = memory.get_project(selected_name) if selected_name else None
if project is None and st.session_state.get("active_project") in project_names:
    project = memory.get_project(st.session_state["active_project"])

st.markdown(
    f'<div class="eyebrow">CODERS &nbsp; / &nbsp; PROJECT WORKSPACE</div>',
    unsafe_allow_html=True,
)
header_cols = st.columns([5, 1.15])
with header_cols[0]:
    st.title(
        "Management"
        if page in ("Overview", "Schedule")
        else ("Create a project" if page == "New project" else page)
    )
    st.markdown(
        '<div class="page-kicker">A clear view of your projects, people, and progress.</div>',
        unsafe_allow_html=True,
    )
with header_cols[1]:
    st.markdown(
        f'<div style="text-align:right;padding-top:1.15rem;color:#777875;font-size:.8rem">'
        f'<span class="project-chip"><span class="live-dot"></span>{date.today().strftime("%b %d, %Y")}</span></div>',
        unsafe_allow_html=True,
    )


def create_project_form():
    st.subheader("Start with the project details")
    st.caption("Add requirements, a deadline, and your team. The planner will build a working schedule.")
    with st.form("create_project"):
        project_name = st.text_input("Project name", "Hospital Management System")
        description = st.text_area(
            "Project requirements",
            "Build a web-based hospital management system with patient registration, doctor management, appointment booking, billing, authentication, and an admin dashboard.",
            height=115,
        )
        left, right = st.columns(2)
        with left:
            deadline = st.date_input(
                "Project deadline",
                date.today() + timedelta(days=45),
                min_value=date.today(),
            )
        with right:
            priority = st.selectbox("Project priority", ["Normal", "High", "Critical"])
        team_text = st.text_area(
            "Team members and skills (Name | skill1, skill2 | availability %)",
            "Aarav | Python, FastAPI, SQL | 100\nPriya | React, JavaScript, UI/UX | 100\nRahul | Testing, API testing, QA | 80\nMeera | Database, SQL, DevOps | 70",
            height=105,
        )
        submitted = st.form_submit_button(
            "Generate project schedule", type="primary", use_container_width=True
        )

    if submitted:
        team = agent.parse_team(team_text)
        if not project_name.strip() or not description.strip():
            st.error("Please enter a project name and requirements.")
        elif not team:
            st.error("Add at least one team member using the required format.")
        else:
            try:
                with st.spinner("Analyzing requirements and building your schedule..."):
                    plan = agent.create_plan(
                        project_name=project_name.strip(),
                        description=description.strip(),
                        deadline=deadline.isoformat(),
                        team=team,
                        priority=priority,
                    )
                    memory.save_project(
                        project_name.strip(),
                        {
                            "project_name": project_name.strip(),
                            "description": description.strip(),
                            "deadline": deadline.isoformat(),
                            "team": team,
                            "priority": priority,
                            "plan": plan,
                            "history": [
                                {"event": "Initial plan created", "date": date.today().isoformat()}
                            ],
                        },
                    )
                    st.session_state["active_project"] = project_name.strip()
                st.success("Project schedule generated and saved.")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not generate the plan: {exc}")


def render_schedule(tasks, compact=False):
    if not tasks:
        st.info("No tasks are available for this project yet.")
        return
    max_days = max((max(1, int(task.get("duration_days", 1))) for task in tasks), default=1)
    for task in tasks[:6] if compact else tasks:
        left, bar, days = st.columns([2.35, 4.2, 0.8], vertical_alignment="center")
        with left:
            st.markdown(
                f'<div class="task-label">{html.escape(str(task.get("title", "Task")))}</div>'
                f'<div class="task-sub">{html.escape(str(task.get("assignee", "Unassigned")))}</div>',
                unsafe_allow_html=True,
            )
        with bar:
            st.markdown(
                f'<div class="task-track"><div class="task-bar" style="width:{max(8, int(100 * max(1, int(task.get("duration_days", 1))) / max_days))}%"></div></div>',
                unsafe_allow_html=True,
            )
        with days:
            st.markdown(
                f'<div style="text-align:right;font-size:.76rem;color:#777875">{int(task.get("duration_days", 1))}d</div>',
                unsafe_allow_html=True,
            )
        st.markdown(
            f'<div class="task-sub" style="margin:-.45rem 0 .45rem 0">'
            f'{html.escape(str(task.get("start_date", "")))} &nbsp;—&nbsp; '
            f'{html.escape(str(task.get("end_date", "")))}</div>',
            unsafe_allow_html=True,
        )
    if compact and len(tasks) > 6:
        st.caption(f"+ {len(tasks) - 6} more scheduled tasks")


if page == "New project":
    with st.container(border=True):
        create_project_form()

elif page == "Overview":
    if not project:
        with st.container(border=True):
            st.markdown('<div class="empty-mark">＋</div>', unsafe_allow_html=True)
            st.subheader("Your project workspace starts here")
            st.markdown(
                '<div class="empty-copy">Create a project plan to see its schedule, team allocation, '
                'deadline status, and saved history in one place.</div>',
                unsafe_allow_html=True,
            )
            st.markdown("")
            create_project_form()
    else:
        plan = project.get("plan", {})
        tasks = plan.get("tasks", [])
        completed = sum(1 for task in tasks if str(task.get("status", "")).lower() == "completed")
        completion = round(100 * completed / len(tasks)) if tasks else 0
        st.markdown(
            f'<div style="margin:1rem 0 1rem"><span class="project-chip"><span class="live-dot"></span>'
            f'{html.escape(str(project.get("project_name", "Project")))} &nbsp; · &nbsp; '
            f'Due {html.escape(str(project.get("deadline", "Not set")))}</span></div>',
            unsafe_allow_html=True,
        )
        metrics = st.columns(4)
        metrics[0].metric("Total tasks", len(tasks))
        metrics[1].metric("Estimated effort", f'{plan.get("total_duration_days", 0)} days')
        metrics[2].metric("Tasks completed", f"{completed} / {len(tasks)}")
        metrics[3].metric("Deadline", plan.get("deadline_feasible", "Review"))

        main_col, side_col = st.columns([1.65, 1], gap="medium")
        with main_col:
            with st.container(border=True):
                top = st.columns([3, 1])
                with top[0]:
                    st.subheader("Project schedule")
                    st.caption(plan.get("summary", "Work plan and upcoming tasks"))
                with top[1]:
                    st.markdown(
                        f'<div style="text-align:right;padding-top:.45rem" class="timeline-note">'
                        f'{completion}% complete</div>',
                        unsafe_allow_html=True,
                    )
                render_schedule(tasks, compact=True)
                st.progress(completion, text="Overall completion")
                if len(tasks) > 6 and st.button("View full schedule", use_container_width=True):
                    st.session_state["request_schedule"] = True
                    st.rerun()
        with side_col:
            with st.container(border=True):
                st.subheader("Team workload")
                st.caption("Estimated working days by assignee")
                resource_summary = plan.get("resource_summary", {})
                if resource_summary:
                    max_load = max(resource_summary.values()) or 1
                    for member, workload in resource_summary.items():
                        st.markdown(
                            f'<div style="display:flex;justify-content:space-between;font-size:.8rem;margin:.75rem 0 .25rem">'
                            f'<span>{html.escape(str(member))}</span><span style="color:#858681">{workload} days</span></div>',
                            unsafe_allow_html=True,
                        )
                        st.progress(min(1.0, workload / max_load))
                else:
                    st.caption("No team allocation data yet.")
                st.markdown('<div class="mini-line"></div>', unsafe_allow_html=True)
                st.markdown("**Deadline status**")
                st.write(plan.get("deadline_feasible", "Review"))
                st.caption(
                    f"Projected finish: {plan.get('agent_observation', {}).get('schedule', {}).get('projected_end_date', 'Not available')}"
                )

        lower_left, lower_right = st.columns([1, 1.65], gap="medium")
        with lower_left:
            with st.container(border=True):
                st.subheader("Project files")
                st.caption("Export the current schedule for your team.")
                if tasks:
                    csv = pd.DataFrame(tasks).to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "↓  Download schedule CSV",
                        csv,
                        "project_schedule.csv",
                        "text/csv",
                        use_container_width=True,
                    )
                with st.expander("Risks and recommendations"):
                    st.write(plan.get("risks", []))
                    st.write(plan.get("recommendations", []))
        with lower_right:
            team = project.get("team", [])
            team_cards = []
            for member in team:
                initials = "".join(
                    part[0] for part in str(member.get("name", "?")).split()[:2]
                ).upper()
                skills = ", ".join(member.get("skills", [])[:2])
                team_cards.append(
                    '<div class="team-person">'
                    f'<div class="team-avatar">{html.escape(initials)}</div>'
                    f'<div class="team-person-name">{html.escape(str(member.get("name", "Team member")))}</div>'
                    f'<div class="team-person-skills">{html.escape(skills)}</div></div>'
                )
            st.markdown(
                '<div class="team-panel">'
                '<div class="team-panel-head"><div class="team-panel-title">Project team</div>'
                f'<div class="team-panel-count">{len(team)} members</div></div>'
                f'<div class="team-grid">{"".join(team_cards) if team_cards else "No team members saved."}</div>'
                '</div>',
                unsafe_allow_html=True,
            )
            with st.expander("Full structured plan"):
                st.json(plan)

elif page == "Schedule":
    if not project:
        st.info("Select a saved project or create one to view its schedule.")
        if st.button("Create a project", type="primary"):
            st.session_state["request_new_project"] = True
            st.rerun()
    else:
        plan = project.get("plan", {})
        st.markdown(
            f'<div style="margin:.5rem 0 1rem"><span class="project-chip">'
            f'{html.escape(str(project.get("project_name", "Project")))} &nbsp; · &nbsp; '
            f'Deadline {html.escape(str(project.get("deadline", "Not set")))}</span></div>',
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            st.subheader("Task timeline")
            st.caption(plan.get("summary", "Scheduled work and task ownership"))
            render_schedule(plan.get("tasks", []))
        tasks = plan.get("tasks", [])
        if tasks:
            st.subheader("Task details")
            df = pd.DataFrame(tasks)
            preferred = [
                "id", "phase", "title", "assignee", "duration_days", "start_date",
                "end_date", "priority", "dependencies", "status",
            ]
            df = df[[column for column in preferred if column in df.columns]]
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button(
                "↓  Download schedule CSV",
                df.to_csv(index=False).encode("utf-8"),
                "project_schedule.csv",
                "text/csv",
            )

elif page == "Update requirements":
    if not project:
        st.info("Select a saved project before updating its requirements.")
    else:
        st.markdown(
            f'<div style="margin:.5rem 0 1rem"><span class="project-chip">'
            f'{html.escape(str(project.get("project_name", "Project")))}</span></div>',
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            st.subheader("What changed?")
            st.caption("The agent will revise the task list, preserve completed work, and recalculate dates.")
            change = st.text_area(
                "Requirement change",
                placeholder="Example: Add online payment integration and move the deadline forward by 5 days.",
                height=110,
            )
            left, right = st.columns(2)
            with left:
                stored_deadline = date.fromisoformat(
                    str(project.get("deadline", date.today().isoformat()))[:10]
                )
                new_deadline = st.date_input(
                    "New deadline",
                    max(date.today(), stored_deadline),
                    min_value=date.today(),
                    key="update_deadline",
                )
            with right:
                update_team_text = st.text_area(
                    "Updated team (optional)",
                    placeholder="Name | skill1, skill2 | availability %",
                    height=70,
                )
            if st.button("Update project schedule", type="primary", use_container_width=True):
                if not change.strip():
                    st.warning("Describe what changed before updating.")
                else:
                    try:
                        team = (
                            agent.parse_team(update_team_text)
                            if update_team_text.strip()
                            else project.get("team", [])
                        )
                        with st.spinner("Reviewing project memory and recalculating the schedule..."):
                            updated = agent.update_plan(
                                project, change.strip(), new_deadline.isoformat(), team
                            )
                            project["description"] = (
                                project.get("description", "") + "\n\nChange: " + change.strip()
                            )
                            project["deadline"] = new_deadline.isoformat()
                            project["team"] = team
                            project["plan"] = updated
                            project.setdefault("history", []).append(
                                {"event": change.strip(), "date": date.today().isoformat()}
                            )
                            memory.save_project(selected_name, project)
                        st.success("Schedule updated and saved.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not update the plan: {exc}")

elif page == "Project memory":
    st.subheader("Saved project history")
    if not project_names:
        st.info("No project memory available yet. Create a project to save its plan and changes.")
    else:
        for name in project_names:
            item = memory.get_project(name)
            with st.container(border=True):
                row = st.columns([3, 1])
                with row[0]:
                    st.subheader(item.get("project_name", name))
                    st.caption(f"Deadline: {item.get('deadline', 'Not set')}")
                with row[1]:
                    if st.button("Delete", key=f"delete_{name}"):
                        memory.delete_project(name)
                        if st.session_state.get("active_project") == name:
                            st.session_state.pop("active_project", None)
                        st.rerun()
                st.markdown("**Change history**")
                st.json(item.get("history", []))
