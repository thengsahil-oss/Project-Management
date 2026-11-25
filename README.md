# Intelligent Project Management Agent

A working Python and Streamlit prototype that turns software project requirements, deadlines, and team skills into a reviewed schedule. The application uses Groq-hosted Llama when an API key is configured; without it, a deterministic planner keeps the core workflow demonstrable.

## What it demonstrates

| Rubric concept | Implementation |
| --- | --- |
| Role and system prompting | A project-manager role and stable safety rules are sent on every model request. |
| Zero-shot prompting | Requirements are analyzed without a worked example. |
| One-shot prompting | A single small-project example sets task decomposition shape and granularity. |
| Few-shot prompting | Two examples calibrate effort-estimation style. |
| Structured output | Groq JSON mode is followed by local validators for types, required fields, limits, IDs, dependency references, and cycles. |
| Step-back reasoning | A high-level principles/constraints pass precedes requirements analysis. |
| Prompt chaining | Step-back → analysis → decomposition → estimation → Python tools → plan review. |
| ReAct-style tool use | Python allocation, dependency-validation, and scheduling actions produce an inspectable action/observation trace. |
| Response evaluation | Six deterministic checks score task presence, IDs, durations, dependencies, assignments, and schedule feasibility metadata. |
| Error handling | Invalid inputs are rejected; model/API/JSON/validation failures produce a visible warning and a deterministic fallback. |

The app does **not** request or expose private chain-of-thought. It shows concise outputs, assumptions, validation results, and observable Python tool actions instead.

## Architecture

1. `app.py` provides the Streamlit dashboard, project form, schedule, persistent history, and Prompt Lab.
2. `agent.py` validates input, builds the prompt chain, calls the configured LLM, validates every structured response, and chooses a visible fallback when a stage fails.
3. `scheduler.py` assigns tasks by skill overlap, validates dependency references, and computes working-day schedule dates.
4. `memory.py` stores project plans and update history in local JSON under `data/projects.json`.
5. `prompts.py` contains the role/system instructions, planning prompts, worked examples, Prompt Lab demos, and technique descriptions.

The model suggests requirements, tasks, dependencies, and estimates. Python performs allocation and scheduling so those steps are explicit and repeatable. Generated plans are planning aids and need human review.

## Setup

### Requirements

- Python 3.10+
- A Groq API key for LLM-backed planning (optional; deterministic fallback works without one)

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Add your own key to `.env`:

```text
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

Keep `.env` private; it is ignored by Git. When configured, project requirements and team information are sent to the Groq API for planning. With no key, the app uses deterministic fallback tasks and does not make model requests.

Start the app:

```powershell
streamlit run app.py
```

Open the local URL printed by Streamlit, usually `http://localhost:8501`.

## Team input format

Enter one team member per line:

```text
Name | skill1, skill2, skill3 | availability percentage
```

For example:

```text
Aarav | Python, FastAPI, SQL | 100
Priya | React, JavaScript, UI/UX | 100
Rahul | Testing, API testing, QA | 80
```

Availability can be omitted (it defaults to 100). Names must be unique; availability must be a whole number from 1 to 100.

## Prompt design and reasoning workflow

The shared system prompt sets the delivery-manager role, treats project inputs as untrusted data, disallows secret disclosure, and asks for concise JSON rather than private reasoning traces.

For a new plan, the stages are:

1. **Step-back:** identify general delivery principles, constraints, and questions before solving the specific project.
2. **Zero-shot requirement analysis:** extract deliverables, requirements, assumptions, and risks without an example.
3. **One-shot decomposition:** use one small worked example to guide task granularity; adapt the example rather than copying its subject.
4. **Few-shot estimation:** use two estimate examples to calibrate working-day estimates while retaining the task IDs and titles.
5. **Tool execution:** allocate team members, validate dependency references, and build the schedule.
6. **Structured review:** inspect tool observations for risks and deadline pressure.

The Prompt Lab runs zero-shot, one-shot, and few-shot examples separately. Try its incomplete brief, instruction-like text, and tight-constraint inputs, or enter a custom request.

## Input handling, security, and evaluation

- Project names, descriptions, changes, dates, team sizes, skills, availability, task counts, and task fields are bounded and validated before use.
- Instruction-like text is passed as JSON project data, not concatenated into the system message. The system prompt explicitly says not to follow embedded override requests; the UI also flags common override patterns.
- Model output is parsed as JSON and checked before any allocation or schedule tool runs. Invalid output is not silently accepted.
- API failures, malformed JSON, and invalid model output use deterministic fallback data with an explicit warning. Logs do not include prompts, API keys, or raw request content.
- API credentials are read from `.env`; do not commit credentials or real sensitive project data.
- The displayed score is a structural/consistency check, not a measure of semantic correctness or a guarantee that estimates are accurate.
- Groq receives the project data when LLM mode is enabled. Review provider privacy terms and avoid entering confidential data unless authorized.

## Tests

Run the standard-library test suite from the project root:

```powershell
python -m unittest discover -s tests -v
```

The tests cover fallback plan generation, plan evaluation and tool traces, incomplete and oversized input, malformed team/deadline values, instruction-like input, malformed model output, cyclic dependencies, Prompt Lab output, and preservation of completed tasks during updates.

## Jury demonstration walkthrough

1. Run `streamlit run app.py` and open the local workspace.
2. Create a sample project with the example team. Show the technique chain, assigned tasks, schedule, warnings, and evaluation score.
3. Open **Prompt Lab** and compare Zero-shot, One-shot, and Few-shot on the same brief.
4. Try **Incomplete requirements** and **Instruction-like text** to demonstrate validation and prompt-injection handling.
5. Inspect the prompt-chain stages and ReAct-style Python observations under the plan quality expander.
6. Update a saved project's requirements and show its revised schedule and preserved completed work.
7. Run the tests from the terminal to demonstrate automated handling of edge cases.

If no API key is configured, explicitly identify the output as deterministic fallback rather than LLM-generated output.

## Limitations and future work

- Fallback tasks are generic; they keep the application usable but are not project-specific AI planning.
- Skill matching and workload balancing are simple heuristics. The scheduler excludes weekends, but does not model holidays, partial-day capacity, or resource contention.
- The evaluation checks structure and consistency, not factual accuracy, estimate quality, or stakeholder acceptance.
- Project memory is a local JSON file with no authentication, concurrency control, or multi-user access controls.
- Future improvements could add richer semantic evaluation with a reviewed benchmark, public-holiday calendars, role-based access, a database-backed multi-user store, and experiments with a small local model or LoRA adapter.

## Project files

```text
app.py              Streamlit interface
agent.py            Prompt chain, validation, fallback, evaluation
prompts.py          System and task prompts
scheduler.py        Resource allocation and schedule tools
memory.py           Local JSON project memory
tests/test_agent.py Focused input and workflow tests
requirements.txt    Python dependencies
.env.example        API configuration template
```
