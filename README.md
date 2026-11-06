# Smart Project Planner

A Python and Streamlit project-management dashboard for organizing tasks, planning dependency-based schedules, visualizing timelines, and analyzing project critical paths.

## Features

- **Task management:** add, edit, and delete project tasks.
- **SQLite persistence:** task information is stored locally in `planner.db`.
- **Task attributes:** priority, estimated work hours, due date, status, duration in calendar days, and task dependencies.
- **Project dashboard:** task counts, completion progress, status distribution, priority distribution, and estimated workload.
- **Automatic scheduling:** calculate task start and finish dates from dependencies.
- **Interactive Gantt chart:** visualize the project timeline and inspect task details.
- **Critical Path Method (CPM):** calculate early/late start and finish, total float, critical tasks, project duration, and all complete critical paths.
- **Dependency validation:** detect missing dependencies, self-dependencies, duplicate IDs, and circular dependencies.

## Technology stack

- Python 3.12 (recommended)
- Streamlit
- SQLite
- Pandas
- Plotly

## Project structure

```text
Smart_Project_Planner/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── planner.db              # created locally when the app runs; not committed
├── src/
│   ├── __init__.py
│   └── scheduler.py
└── tests/
    └── test_scheduler.py
```

## Run locally

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/Smart_Project_Planner.git
cd Smart_Project_Planner
```

### 2. Create and activate a virtual environment

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Start the application

```bash
streamlit run app.py
```

Streamlit will print a local address, normally `http://localhost:8501`. Open it in your browser. The application creates `planner.db` automatically on first run.

## How to use

1. Add tasks and set their priority, estimated hours, due date, status, and duration in calendar days.
2. Select dependencies for tasks that must wait for other tasks to finish.
3. Use **Manage Existing Tasks** to edit or delete tasks.
4. Review progress and workload in the Project Dashboard.
5. Choose a project start date and select **Generate Project Schedule**.
6. Review the Gantt chart, detailed schedule, and Critical Path Analysis.

## Scheduling assumptions

- Task durations are expressed in **calendar days**, not working days.
- A task with no dependencies can start on the selected project start date.
- A dependent task starts on the calendar day after its latest predecessor finishes.
- CPM day numbers start at day 0. The CPM project duration is the longest dependency-driven duration in calendar days.
- The current model does not account for weekends, public holidays, resource capacity, or resource leveling.

## Run the tests

From the project root:

```bash
python -m unittest discover -s tests -v
```

## Database and privacy

The local SQLite database (`planner.db`) is intentionally excluded from Git. It may contain personal or project-specific task information. Each person running the app gets a local database created on their own machine.

## Future improvements

- Working-day calendars and holiday handling
- Resource allocation and workload balancing
- Export schedule and reports to CSV/PDF/Excel
- Project risk and cost analysis
- User authentication and multi-project support
- Automated deployment

## Author

**Amsa Azeem**

Portfolio project demonstrating Python application development, database integration, project scheduling, data visualization, and decision-support techniques.
