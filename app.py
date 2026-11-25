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
        --ink: #f7f3ff;
        --muted: #b7b0ce;
        --line: rgba(207, 190, 245, .16);
        --paper: #100e1a;
        --surface: #1c192c;
        --accent: #ffb38f;
        --lavender: #b8a7ff;
    }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; color: var(--ink); }
    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(ellipse at 78% 0%, rgba(86, 61, 116, .2), transparent 35%),
            radial-gradient(ellipse at 8% 50%, rgba(56, 42, 91, .15), transparent 42%),
            var(--paper);
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stMain"] { padding-top: 1.3rem; }
    .block-container { max-width: 1540px; padding: 1.4rem 2.2rem 3rem; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #171426 0%, #13111f 100%);
        border-right: 1px solid rgba(207, 190, 245, .12);
    }
    [data-testid="stSidebar"] > div:first-child { padding: 1.35rem 1rem; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: var(--muted); }
    [data-testid="stRadio"] label p { color: #d3cde3; font-size: .9rem; font-weight: 500; }
    [data-testid="stRadio"] > div { gap: .3rem; }
    input[type="radio"] { accent-color: var(--accent) !important; }
    h1, h2, h3 { font-family: 'Manrope', sans-serif !important; color: #f7f3ff !important; letter-spacing: -.045em; }
    h1 { font-size: 2rem !important; font-weight: 600 !important; }
    h2 { font-size: 1.25rem !important; font-weight: 600 !important; }
    h3 { font-size: 1rem !important; font-weight: 600 !important; }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(145deg, rgba(34, 30, 52, .98), rgba(25, 23, 41, .98));
        border-color: var(--line);
        border-radius: 20px;
    }
    [data-testid="stMetric"] {
        background: linear-gradient(150deg, #242039, #1a172b);
        padding: .85rem 1rem;
        border: 1px solid var(--line);
        border-radius: 16px;
    }
    [data-testid="stMetricLabel"] { color: var(--muted); font-size: .78rem; }
    [data-testid="stMetricValue"] { font-family: 'Manrope', sans-serif; color: #fff; font-size: 1.5rem; font-weight: 600; }
    [data-testid="stButton"] button, [data-testid="stFormSubmitButton"] button {
        border-radius: 999px;
        min-height: 2.55rem;
        font-weight: 600;
        color: #f6f1ff;
        border-color: rgba(216, 202, 255, .26);
        background: rgba(255, 255, 255, .04);
    }
    [data-testid="stButton"] button[kind="primary"], [data-testid="stFormSubmitButton"] button[kind="primary"] {
        background: linear-gradient(110deg, #ffc19c, #ed9bb7);
        color: #21172b;
        border-color: transparent;
    }
    [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea, [data-testid="stDateInput"] input,
    [data-testid="stSelectbox"] [data-baseweb="select"] > div {
        border-radius: 12px;
        background-color: #211e33;
        border-color: rgba(216, 202, 255, .2);
        color: #f7f3ff;
    }
    [data-testid="stTextInput"] label, [data-testid="stTextArea"] label,
    [data-testid="stDateInput"] label, [data-testid="stSelectbox"] label { color: #d3cde3; }
    [data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 14px; overflow: hidden; }
    [data-testid="stProgressBar"] > div { background-color: rgba(211, 196, 255, .15); }
    [data-testid="stProgressBar"] > div > div { background: linear-gradient(90deg, #b8a7ff, #ffb38f); }
    [data-testid="stExpander"] { border-color: var(--line); border-radius: 14px; }
    [data-testid="stExpander"] summary, [data-testid="stExpander"] p { color: #e5dff2; }
    .brand { display:flex; align-items:center; gap:10px; padding: .25rem .4rem 1.8rem; }
    .brand-symbol { display:grid; place-items:center; width:34px; height:34px; border-radius:12px; background:linear-gradient(145deg,#ffc19c,#dd9fc8); color:#21172b; font-size:20px; }
    .brand-name { font-family:'Manrope',sans-serif; font-size:1rem; font-weight:800; letter-spacing:-.04em; color:#fff; }
    .eyebrow { color:#a99acb; font-size:.68rem; font-weight:700; letter-spacing:.13em; text-transform:uppercase; }
    .page-kicker { color:#aaa3bf; font-size:.8rem; margin-top:-.6rem; }
    .project-chip { display:inline-flex; align-items:center; gap:7px; padding:7px 11px; border:1px solid var(--line); border-radius:999px; background:rgba(34,30,52,.9); color:#e7e1f4; font-size:.77rem; }
    .live-dot { height:7px; width:7px; border-radius:50%; background:var(--accent); display:inline-block; box-shadow:0 0 12px rgba(255,179,143,.8); }
    .timeline-note { color:var(--muted); font-size:.78rem; }
    .task-label { color:#f0ebfb; font-size:.82rem; font-weight:600; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .task-sub { color:#aaa3bf; font-size:.7rem; }
    .task-track { height:12px; width:100%; background:#302b43; border-radius:10px; overflow:hidden; }
    .task-bar { height:100%; background:linear-gradient(90deg,#b8a7ff,#ffb38f); border-radius:10px; min-width:8px; }
    .mini-line { height:1px; background:rgba(207,190,245,.13); margin:.85rem 0; }
    .empty-mark { width:48px; height:48px; border-radius:16px; display:grid; place-items:center; color:#21172b; background:linear-gradient(145deg,#ffc19c,#dd9fc8); font-size:23px; margin-bottom:1rem; }
    .empty-copy { color:var(--muted); max-width:38rem; line-height:1.6; }
    .journey-hero {
        position:relative;
        isolation:isolate;
        overflow:hidden;
        min-height:300px;
        display:flex;
        align-items:center;
        margin:1.35rem 0 1.4rem;
        padding:2.1rem 2.35rem;
        border:1px solid rgba(224,205,255,.2);
        border-radius:26px;
        background:linear-gradient(115deg,#241a3b 0%,#302048 50%,#8d5870 100%);
        box-shadow:0 24px 70px rgba(0,0,0,.24);
    }
    .journey-hero:after {
        content:"";
        position:absolute;
        z-index:1;
        inset:0;
        background:linear-gradient(90deg,rgba(23,18,40,.98) 0%,rgba(28,20,45,.93) 40%,rgba(34,23,49,.16) 100%);
    }
    .hero-art { position:absolute; z-index:0; right:0; bottom:0; width:72%; height:100%; }
    .hero-copy { position:relative; z-index:2; max-width:58%; }
    .hero-overline { color:#e6c6d6; font-size:.67rem; font-weight:700; letter-spacing:.16em; text-transform:uppercase; }
    .hero-title { margin:.75rem 0 .65rem; font-family:'Manrope',sans-serif; color:#fff; font-size:clamp(2.2rem,4vw,3.8rem); font-weight:800; line-height:.98; letter-spacing:-.075em; }
    .hero-title em { color:#ffc09d; font-style:normal; }
    .hero-description { max-width:34rem; color:#d0c6dc; font-size:.88rem; line-height:1.55; }
    .hero-footer { display:flex; gap:1.7rem; margin-top:1.25rem; }
    .hero-date-label { display:block; margin-bottom:.2rem; color:#b7a9c7; font-size:.6rem; font-weight:700; letter-spacing:.15em; }
    .hero-date-value { color:#fff; font-size:.78rem; font-weight:600; }
    .hero-date-divider { width:1px; background:rgba(255,255,255,.25); }
    .team-panel { min-height:180px; padding:1.35rem 1.5rem; border:1px solid rgba(214,191,255,.18); border-radius:20px; color:#fff; background:radial-gradient(ellipse at 82% 110%, #765271 0, #29213d 38%, #1a1729 78%); }
    .team-panel-head { display:flex; align-items:center; justify-content:space-between; margin-bottom:1.55rem; }
    .team-panel-title { font-family:'Manrope',sans-serif; font-size:1.15rem; font-weight:600; letter-spacing:-.04em; }
    .team-panel-count { font-size:.72rem; color:#e0d7e9; border:1px solid rgba(255,255,255,.3); border-radius:999px; padding:4px 9px; }
    .team-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(125px,1fr)); gap:1rem; }
    .team-person { border-top:1px solid rgba(255,255,255,.2); padding-top:.85rem; }
    .team-avatar { display:grid; place-items:center; width:34px; height:34px; border-radius:50%; background:linear-gradient(145deg,#ffc19c,#dd9fc8); color:#21172b; font-size:.72rem; font-weight:700; margin-bottom:.55rem; }
    .team-person-name { font-size:.8rem; font-weight:600; color:#fff; }
    .team-person-skills { color:#c2b8d0; font-size:.68rem; margin-top:.15rem; }
    @media (max-width: 850px) {
        .block-container { padding: 1rem .8rem 2rem; }
        h1 { font-size:1.65rem !important; }
        .journey-hero { min-height:280px; padding:1.5rem; }
        .hero-copy { max-width:80%; }
        .hero-art { width:100%; opacity:.64; }
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


def render_hero(project=None):
    if project:
        project_name = html.escape(str(project.get("project_name", "Active project")))
        description = str(project.get("description", "A plan for the work ahead.")).strip()
        description = html.escape(description[:180] + ("..." if len(description) > 180 else ""))
        overline = f"ACTIVE PROJECT  /  {project_name}"
        title = "Your plan,<br><em>in motion.</em>"
        deadline = html.escape(str(project.get("deadline", "Not set")))
        status = html.escape(str(project.get("plan", {}).get("deadline_feasible", "Review")))
    else:
        description = "Shape your requirements into a clear plan, give your team a path forward, and keep every milestone in view."
        overline = "CODERS PROJECT WORKSPACE  /  PLAN THE JOURNEY"
        title = "Turn ideas into<br><em>clear plans.</em>"
        deadline = "Start with a deadline"
        status = "Project overview"

    st.markdown(
        f"""
        <div class="journey-hero">
          <svg class="hero-art" viewBox="0 0 900 440" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
            <defs>
              <linearGradient id="sky" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0" stop-color="#54426e"/>
                <stop offset=".58" stop-color="#b66d80"/>
                <stop offset="1" stop-color="#f2a178"/>
              </linearGradient>
              <linearGradient id="ridge" x1="0" y1="0" x2="0" y2="1">
                <stop stop-color="#9b7195"/>
                <stop offset="1" stop-color="#443452"/>
              </linearGradient>
              <linearGradient id="valley" x1="0" y1="0" x2="1" y2="1">
                <stop stop-color="#563e68"/>
                <stop offset="1" stop-color="#211b35"/>
              </linearGradient>
              <radialGradient id="glow">
                <stop stop-color="#ffd1a6" stop-opacity=".85"/>
                <stop offset="1" stop-color="#ffb38f" stop-opacity="0"/>
              </radialGradient>
            </defs>
            <rect width="900" height="440" fill="url(#sky)"/>
            <circle cx="650" cy="145" r="155" fill="url(#glow)"/>
            <circle cx="650" cy="145" r="54" fill="#ffd1a6" opacity=".8"/>
            <path d="M245 330 455 95 570 222 684 74 900 310 900 440 210 440Z" fill="url(#ridge)" opacity=".76"/>
            <path d="m435 118 20-23 23 25-16-5-11 13-7-11-12 7Z" fill="#f3c7c0" opacity=".76"/>
            <path d="m659 102 25-28 29 32-19-7-11 13-10-12-14 8Z" fill="#f7c4b8" opacity=".72"/>
            <path d="M170 363 340 226 474 323 621 208 900 372 900 440 130 440Z" fill="#684d72"/>
            <path d="M260 389 476 303 570 359 730 248 900 351 900 440 170 440Z" fill="url(#valley)"/>
            <path d="M510 440c70-67 130-83 220-104 62-16 108-43 170-96v200Z" fill="#332642" opacity=".78"/>
            <path d="M595 440c42-46 97-55 145-66 59-14 98-33 160-75" fill="none" stroke="#ffd0ad" stroke-opacity=".42" stroke-width="3"/>
            <g fill="#fff0df" opacity=".82">
              <circle cx="500" cy="68" r="2"/><circle cx="565" cy="42" r="1.5"/>
              <circle cx="738" cy="57" r="2"/><circle cx="812" cy="116" r="1.5"/>
              <circle cx="580" cy="185" r="1.5"/><circle cx="840" cy="205" r="2"/>
            </g>
          </svg>
          <div class="hero-copy">
            <div class="hero-overline">{overline}</div>
            <div class="hero-title">{title}</div>
            <div class="hero-description">{description}</div>
            <div class="hero-footer">
              <div><span class="hero-date-label">DEADLINE</span><span class="hero-date-value">{deadline}</span></div>
              <div class="hero-date-divider"></div>
              <div><span class="hero-date-label">STATUS</span><span class="hero-date-value">{status}</span></div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


if page == "New project":
    with st.container(border=True):
        create_project_form()

elif page == "Overview":
    render_hero(project)
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
