# Intelligent Project Management Agent

An AI-assisted project planner for software development teams. It accepts project requirements, deadlines and team skills, then decomposes work, estimates effort, allocates resources and generates a schedule. It also stores project memory and updates plans when requirements change.

## Features

- Task decomposition into phases and subtasks
- Prompt chaining: requirement analysis → decomposition → estimation → review
- ReAct-style tool workflow: allocate resources → schedule tasks → validate dependencies → review observations
- Skill-based team allocation with workload balancing
- Working-day schedule generation and deadline feasibility check
- Persistent JSON project memory
- Dynamic requirement updates with change history
- CSV export
- Rule-based fallback if Groq API is not configured or unavailable

## Requirements

- Python 3.10+
- A Groq API key (optional, but recommended for AI-generated plans)

## Run in VS Code

1. Extract the ZIP file.
2. Open the extracted `intelligent_project_management_agent` folder in VS Code.
3. Open the VS Code terminal.
4. Create and activate a virtual environment.

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

5. Install dependencies:

```powershell
pip install -r requirements.txt
```

6. Create your `.env` file:

```powershell
Copy-Item .env.example .env
```

Open `.env` and replace `your_groq_api_key_here` with your own Groq API key. Never share or upload your API key.

7. Start the app:

```powershell
streamlit run app.py
```

The app opens in your browser, usually at `http://localhost:8501`.

## Team input format

Enter one team member per line:

```text
Name | skill1, skill2, skill3 | availability percentage
```

Example:

```text
Aarav | Python, FastAPI, SQL | 100
Priya | React, JavaScript, UI/UX | 100
Rahul | Testing, API testing, QA | 80
Meera | Database, SQL, DevOps | 70
```

## How the agent works

1. **Requirement analysis:** the LLM extracts deliverables, assumptions and risks.
2. **Task decomposition:** the LLM breaks the project into task-sized units.
3. **Estimation:** the LLM reviews duration and dependency estimates.
4. **ReAct-style execution:** Python tools allocate resources, generate dates and validate dependencies. Tool observations are passed to the review prompt.
5. **Memory:** plans and change history are saved in `data/projects.json`.
6. **Dynamic updates:** a change request is compared with the saved plan, then the task list and schedule are regenerated. Completed tasks with matching IDs retain their completed status.

## Project structure

```text
intelligent_project_management_agent/
│
├── app.py              # Streamlit user interface
├── agent.py            # AI agent and prompt chaining
├── prompts.py          # System and task prompts
├── scheduler.py        # Resource allocation and schedule tools
├── memory.py           # Persistent JSON memory
├── requirements.txt    # Python dependencies
├── .env.example        # API configuration template
├── .gitignore
└── README.md
```

## Important notes

- The generated plan is a planning recommendation, not a guaranteed delivery commitment.
- Duration estimates are in working days; the basic scheduler excludes weekends but does not yet model public holidays or partial-day capacity.
- Resource allocation is a simple skill-overlap heuristic. A real company should review workload, seniority, leave and task concurrency.
- This prototype stores memory locally in JSON. For a production multi-user deployment, use a database with authentication and access controls.
- The ReAct implementation uses observable tool actions and results; it does not expose private chain-of-thought.
