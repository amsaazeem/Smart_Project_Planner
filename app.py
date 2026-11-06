
import streamlit as st
import pandas as pd
import sqlite3
import json
import plotly.express as px

from datetime import date, timedelta
from pathlib import Path

from src.scheduler import (
    calculate_critical_path,
    calculate_schedule,
    calculate_project_duration
)


# ==========================================
# 1. APPLICATION CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Smart Project Planner",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Smart Project Planner")
st.subheader("Project Management and Decision Support System")

st.write(
    "Manage projects, organize tasks, monitor progress "
    "and make better project decisions."
)

# ==========================================
# 2. DATABASE CONNECTION
# ==========================================

DATABASE = Path(__file__).resolve().parent / "planner.db"


def get_connection():
    return sqlite3.connect(DATABASE)


# ==========================================
# 3. CREATE DATABASE TABLE
# ==========================================


def initialize_database():

    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT NOT NULL,
            priority TEXT NOT NULL,
            estimated_hours INTEGER NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)

    # Check existing database columns
    cursor = connection.cursor()
    cursor.execute("PRAGMA table_info(tasks)")
    columns = [column[1] for column in cursor.fetchall()]

    # Add duration_days if it does not exist
    if "duration_days" not in columns:
        cursor.execute(
            "ALTER TABLE tasks ADD COLUMN duration_days INTEGER DEFAULT 1"
        )

    # Add dependencies if it does not exist
    if "dependencies" not in columns:
        cursor.execute(
            "ALTER TABLE tasks ADD COLUMN dependencies TEXT DEFAULT '[]'"
        )

    connection.commit()
    connection.close()



# ==========================================
# 4. RETRIEVE ALL TASKS
# ==========================================

def get_tasks():

    connection = get_connection()

    df = pd.read_sql_query(
        "SELECT * FROM tasks ORDER BY id",
        connection
    )

    connection.close()

    return df


# ==========================================
# 5. ADD A NEW TASK
# ==========================================


def add_task(
    name,
    priority,
    hours,
    due_date,
    status,
    duration_days,
    dependencies
):

    connection = get_connection()

    connection.execute(
        """
        INSERT INTO tasks
        (
            task_name,
            priority,
            estimated_hours,
            due_date,
            status,
            duration_days,
            dependencies
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            priority,
            hours,
            due_date.isoformat(),
            status,
            duration_days,
            json.dumps(dependencies)
        )
    )

    connection.commit()
    connection.close()



# ==========================================
# 6. UPDATE AN EXISTING TASK
# ==========================================


def update_task(
    task_id,
    name,
    priority,
    hours,
    due_date,
    status,
    duration_days,
    dependencies
):

    connection = get_connection()

    connection.execute(
        """
        UPDATE tasks
        SET task_name = ?,
            priority = ?,
            estimated_hours = ?,
            due_date = ?,
            status = ?,
            duration_days = ?,
            dependencies = ?
        WHERE id = ?
        """,
        (
            name,
            priority,
            hours,
            due_date.isoformat(),
            status,
            duration_days,
            json.dumps(dependencies),
            task_id
        )
    )

    connection.commit()
    connection.close()

# ==========================================
# 7. DELETE A TASK
# ==========================================

def delete_task(task_id):

    connection = get_connection()

    connection.execute(
        "DELETE FROM tasks WHERE id = ?",
        (task_id,)
    )

    connection.commit()
    connection.close()


# Create database table when application starts
initialize_database()


# ==========================================
# 8. ADD TASK INTERFACE
# ==========================================


# ==========================================
# 8. ADD TASK INTERFACE
# ==========================================

st.header("➕ Add a New Task")

# Load existing tasks for dependency selection
existing_tasks_df = get_tasks()

existing_task_options = {
    int(row["id"]): row["task_name"]
    for _, row in existing_tasks_df.iterrows()
}

with st.form("add_task_form", clear_on_submit=True):

    task_name = st.text_input("Task Name")

    col1, col2 = st.columns(2)

    with col1:

        priority = st.selectbox(
            "Priority",
            ["High", "Medium", "Low"]
        )

        estimated_hours = st.number_input(
            "Estimated Hours",
            min_value=1,
            max_value=1000,
            value=8
        )

        duration_days = st.number_input(
            "Duration (Calendar Days)",
            min_value=1,
            max_value=365,
            value=3
        )

    with col2:

        due_date = st.date_input(
            "Due Date",
            value=date.today() + timedelta(days=7)
        )

        status = st.selectbox(
            "Status",
            ["Not Started", "In Progress", "Completed"]
        )

    dependencies = st.multiselect(
        "Dependencies (Tasks that must finish first)",
        options=list(existing_task_options.keys()),
        format_func=lambda task_id:
            f"{task_id} - {existing_task_options[task_id]}"
    )

    submitted = st.form_submit_button("Add Task")

    if submitted:

        if task_name.strip():

            add_task(
                task_name.strip(),
                priority,
                estimated_hours,
                due_date,
                status,
                duration_days,
                dependencies
            )

            st.success("Task saved permanently in database!")
            st.rerun()

        else:

            st.warning("Please enter a task name.")



# ==========================================
# 9. LOAD TASKS FROM DATABASE
# ==========================================

df = get_tasks()


# ==========================================
# 10. EDIT AND DELETE TASKS
# ==========================================

st.divider()
st.header("✏️ Manage Existing Tasks")

if not df.empty:

    task_options = {
        int(row["id"]): row["task_name"]
        for _, row in df.iterrows()
    }

    selected_id = st.selectbox(
        "Select a task",
        options=list(task_options.keys()),
        format_func=lambda task_id:
            f"{task_id} - {task_options[task_id]}"
    )

    selected_task = df[df["id"] == selected_id].iloc[0]

    # Read existing dependencies
    current_dependencies = json.loads(
        selected_task["dependencies"] or "[]"
    )

    # Exclude the selected task from its own dependencies
    dependency_options = {
        task_id: task_name
        for task_id, task_name in task_options.items()
        if task_id != selected_id
    }

    current_dependencies = [
        dep for dep in current_dependencies
        if dep in dependency_options
    ]

    with st.form("edit_task_form"):

        st.subheader("Edit Task Details")

        edited_name = st.text_input(
            "Task Name",
            value=selected_task["task_name"]
        )

        col1, col2 = st.columns(2)

        with col1:

            edited_priority = st.selectbox(
                "Priority",
                ["High", "Medium", "Low"],
                index=["High", "Medium", "Low"].index(
                    selected_task["priority"]
                )
            )

            edited_hours = st.number_input(
                "Estimated Hours",
                min_value=1,
                max_value=1000,
                value=int(selected_task["estimated_hours"])
            )

            edited_duration = st.number_input(
                "Duration (Calendar Days)",
                min_value=1,
                max_value=365,
                value=int(selected_task["duration_days"])
            )

        with col2:

            edited_date = st.date_input(
                "Due Date",
                value=date.fromisoformat(
                    selected_task["due_date"]
                )
            )

            edited_status = st.selectbox(
                "Status",
                ["Not Started", "In Progress", "Completed"],
                index=[
                    "Not Started",
                    "In Progress",
                    "Completed"
                ].index(selected_task["status"])
            )

        edited_dependencies = st.multiselect(
            "Dependencies (Tasks that must finish first)",
            options=list(dependency_options.keys()),
            default=current_dependencies,
            format_func=lambda task_id:
                f"{task_id} - {dependency_options[task_id]}"
        )

        save_changes = st.form_submit_button("Save Changes")

        if save_changes:

            if edited_name.strip():

                update_task(
                    selected_id,
                    edited_name.strip(),
                    edited_priority,
                    edited_hours,
                    edited_date,
                    edited_status,
                    edited_duration,
                    edited_dependencies
                )

                st.success("Task updated in database!")
                st.rerun()

            else:

                st.warning("Task name cannot be empty.")

    if st.button("🗑️ Delete Selected Task"):

        delete_task(selected_id)

        st.success("Task deleted from database!")
        st.rerun()

else:

    st.info("No tasks available. Add your first task above.")


# ==========================================
# 11. PROJECT DASHBOARD
# ==========================================

st.divider()
st.header("📈 Project Dashboard")

df = get_tasks()

if not df.empty:

    total_tasks = len(df)

    completed = len(
        df[df["status"] == "Completed"]
    )

    in_progress = len(
        df[df["status"] == "In Progress"]
    )

    pending = len(
        df[df["status"] == "Not Started"]
    )

    progress = (completed / total_tasks) * 100

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Tasks", total_tasks)
    col2.metric("Completed", completed)
    col3.metric("In Progress", in_progress)
    col4.metric("Progress", f"{progress:.1f}%")

    st.progress(progress / 100)

    # Task table

    st.subheader("📋 All Project Tasks")

    display_df = df.rename(
        columns={
            "id": "ID",
            "task_name": "Task",
            "priority": "Priority",
            "estimated_hours": "Estimated Hours",
            "due_date": "Due Date",
            "status": "Status"
        }
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    # Status chart

    st.subheader("Task Status Analysis")

    status_counts = (
        df["status"]
        .value_counts()
        .reindex(
            ["Not Started", "In Progress", "Completed"],
            fill_value=0
        )
    )

    st.bar_chart(status_counts)

    # Priority chart

    st.subheader("Task Priority Analysis")

    priority_counts = (
        df["priority"]
        .value_counts()
        .reindex(
            ["High", "Medium", "Low"],
            fill_value=0
        )
    )

    st.bar_chart(priority_counts)

    # Workload

    total_hours = df["estimated_hours"].sum()

    st.subheader("⏱️ Project Workload")

    st.metric(
        "Total Estimated Work Hours",
        f"{total_hours} hours"
    )

else:

    st.info("Add tasks to display project statistics.")



# ==========================================================
# SECTION 12: AUTOMATIC PROJECT SCHEDULING
# ==========================================================

st.header("📅 Automatic Project Scheduling")

st.write(
    "Generate a project schedule based on task durations "
    "and dependencies, and analyze the project using a Gantt chart "
    "and Critical Path Method (CPM)."
)

# Reload the latest tasks from the database
df = get_tasks()

if df.empty:
    st.info("Add some tasks before generating a project schedule.")

else:
    # Select project start date
    project_start = st.date_input(
        "Project Start Date",
        value=date.today(),
        key="project_start_date"
    )

    # Generate schedule
    if st.button("🚀 Generate Project Schedule"):

        try:
            # Prepare tasks for the scheduling algorithm
            scheduling_tasks = []

            for _, row in df.iterrows():
                dependencies = json.loads(
                    row["dependencies"]
                    if row["dependencies"]
                    else "[]"
                )

                scheduling_tasks.append({
                    "id": int(row["id"]),
                    "name": row["task_name"],
                    "duration": int(row["duration_days"]),
                    "dependencies": dependencies
                })

            # Calculate task schedule
            schedule = calculate_schedule(
                scheduling_tasks,
                project_start
            )

            # Calculate total project duration
            total_duration = calculate_project_duration(schedule)

            # Calculate Critical Path Method results
            cpm_results = calculate_critical_path(scheduling_tasks)

            # Check that a schedule was generated
            if schedule:

                # --------------------------------------------------
                # 12.1 PROJECT SUMMARY METRICS
                # --------------------------------------------------

                st.subheader("📊 Project Summary")

                project_finish = max(
                    task["finish"] for task in schedule
                )

                metric1, metric2, metric3 = st.columns(3)

                metric1.metric(
                    "Total Project Tasks",
                    len(schedule)
                )

                metric2.metric(
                    "Project Duration",
                    f"{total_duration} days"
                )

                metric3.metric(
                    "Projected Finish Date",
                    project_finish.strftime("%d %b %Y")
                )

                st.divider()

                # --------------------------------------------------
                # 12.2 PREPARE SCHEDULE DATAFRAME
                # --------------------------------------------------

                schedule_df = pd.DataFrame(schedule)

                # Add task information from the database
                chart_df = schedule_df.merge(
                    df[["id", "priority", "status", "due_date"]],
                    on="id",
                    how="left"
                )

                # Add one day so the Gantt chart displays the
                # complete inclusive task duration
                chart_df["Chart Finish"] = (
                    chart_df["finish"] + timedelta(days=1)
                )

                # Convert dependencies into readable text
                chart_df["Dependencies"] = chart_df["dependencies"].apply(
                    lambda deps: (
                        ", ".join(str(dep) for dep in deps)
                        if deps else "None"
                    )
                )

                # --------------------------------------------------
                # 12.3 PROJECT GANTT CHART
                # --------------------------------------------------

                st.subheader("📊 Project Gantt Chart")

                fig = px.timeline(
                    chart_df,
                    x_start="start",
                    x_end="Chart Finish",
                    y="name",
                    color="priority",
                    color_discrete_map={
                        "High": "#D9534F",
                        "Medium": "#E6A23C",
                        "Low": "#3A9D6F"
                    },
                    hover_data={
                        "id": True,
                        "priority": True,
                        "status": True,
                        "duration": True,
                        "due_date": True,
                        "Dependencies": True,
                        "start": True,
                        "finish": True,
                        "Chart Finish": False
                    },
                    title="Project Schedule by Task Priority"
                )

                fig.update_yaxes(
                    autorange="reversed",
                    title="Project Tasks"
                )

                fig.update_xaxes(
                    title="Project Timeline",
                    tickformat="%d %b %Y"
                )

                fig.update_layout(
                    height=max(400, len(chart_df) * 65),
                    legend_title_text="Task Priority",
                    hoverlabel=dict(font_size=12)
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

                st.caption(
                    "High = Red | Medium = Orange | Low = Green. "
                    "Hover over a task to view its details."
                )

                st.divider()

                # --------------------------------------------------
                # 12.4 DETAILED PROJECT SCHEDULE
                # --------------------------------------------------

                st.subheader("📋 Detailed Project Schedule")

                display_df = chart_df[
                    [
                        "id",
                        "name",
                        "priority",
                        "status",
                        "duration",
                        "start",
                        "finish",
                        "due_date",
                        "Dependencies"
                    ]
                ].copy()

                display_df.columns = [
                    "Task ID",
                    "Task Name",
                    "Priority",
                    "Status",
                    "Duration (Days)",
                    "Start Date",
                    "Finish Date",
                    "Due Date",
                    "Dependencies"
                ]

                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True
                )

                st.divider()

                # --------------------------------------------------
                # 12.5 CRITICAL PATH ANALYSIS (CPM)
                # --------------------------------------------------

                st.subheader("🎯 Critical Path Analysis")

                st.write(
                    "Identify the tasks that determine the overall "
                    "project duration and calculate the scheduling "
                    "flexibility available for each task."
                )

                critical_task_ids = set(cpm_results["critical_tasks"])

                # CPM summary metrics
                cpm_col1, cpm_col2, cpm_col3 = st.columns(3)

                cpm_col1.metric(
                    "CPM Project Duration",
                    f'{cpm_results["project_duration"]} days'
                )

                cpm_col2.metric(
                    "Critical Tasks",
                    len(critical_task_ids)
                )

                cpm_col3.metric(
                    "Non-Critical Tasks",
                    len(scheduling_tasks) - len(critical_task_ids)
                )

                st.divider()

                # Prepare CPM task analysis table
                cpm_rows = []

                for task in scheduling_tasks:
                    task_id = task["id"]

                    cpm_rows.append({
                        "Task ID": task_id,
                        "Task Name": task["name"],
                        "Duration (Days)": task["duration"],
                        "Early Start (Day)": cpm_results["early_start"][task_id],
                        "Early Finish (Day)": cpm_results["early_finish"][task_id],
                        "Late Start (Day)": cpm_results["late_start"][task_id],
                        "Late Finish (Day)": cpm_results["late_finish"][task_id],
                        "Total Float (Days)": cpm_results["total_float"][task_id],
                        "Critical Task": (
                            "Yes" if task_id in critical_task_ids else "No"
                        )
                    })

                cpm_df = pd.DataFrame(cpm_rows)

                st.subheader("📋 CPM Task Analysis")

                st.dataframe(
                    cpm_df,
                    use_container_width=True,
                    hide_index=True
                )

                # Display all critical paths
                st.subheader("🔴 Identified Critical Paths")

                critical_paths = cpm_results["critical_paths"]

                if critical_paths:
                    task_names = {
                        task["id"]: task["name"]
                        for task in scheduling_tasks
                    }

                    for index, path in enumerate(critical_paths, start=1):
                        path_names = [
                            task_names[task_id]
                            for task_id in path
                        ]

                        st.write(
                            f"**Critical Path {index}:** "
                            + " → ".join(path_names)
                        )
                else:
                    st.info("No critical path was identified.")

                st.caption(
                    "Interpretation: Tasks with zero total float are critical. "
                    "A delay in these tasks can delay the overall project."
                )

                st.success(
                    "Project schedule and Critical Path Analysis "
                    "generated successfully!"
                )

            else:
                st.warning(
                    "No schedule was generated. Please check your tasks."
                )

        except ValueError as error:
            st.error(f"Scheduling error: {error}")

        except KeyError as error:
            st.error(
                f"Missing task data: {error}. "
                "Please check your database columns."
            )

        except TypeError as error:
            st.error(f"Data type error: {error}")

        except Exception as error:
            st.error(f"Unexpected error: {error}")


# ==========================================================
# END OF SECTION 12
# ==========================================================



# ==========================================
# 13. APPLICATION FOOTER
# ==========================================

st.divider()

st.caption(
    "Smart Project Planner | Python | Streamlit | "
    "Pandas | SQLite"
)
