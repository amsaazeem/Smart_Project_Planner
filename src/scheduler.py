"""Dependency-based project scheduling and Critical Path Method utilities.

Durations are measured in calendar days. CPM day numbers are zero-based:
a task starting on day 0 with duration 3 finishes at day 3 in the CPM
forward-pass convention (the schedule calendar dates are inclusive).
"""

from datetime import timedelta


def _validate_tasks(tasks):
    """Validate task identifiers, durations, and dependency references."""
    task_map = {}

    for task in tasks:
        if "id" not in task:
            raise ValueError("Every task must have an 'id'.")
        if task["id"] in task_map:
            raise ValueError(f"Duplicate task ID found: {task['id']}.")
        if "name" not in task:
            raise ValueError(f"Task {task['id']} must have a name.")
        if "duration" not in task:
            raise ValueError(f"Task {task['id']} must have a duration.")
        if not isinstance(task["duration"], int) or task["duration"] < 1:
            raise ValueError(
                f"Task {task['id']} must have a duration of at least 1 day."
            )
        task_map[task["id"]] = task

    for task_id, task in task_map.items():
        dependencies = task.get("dependencies", [])
        if not isinstance(dependencies, list):
            raise ValueError(f"Dependencies for task {task_id} must be a list.")
        if len(dependencies) != len(set(dependencies)):
            raise ValueError(f"Task {task_id} contains duplicate dependencies.")
        for dependency in dependencies:
            if dependency not in task_map:
                raise ValueError(
                    f"Task {task_id} depends on missing task {dependency}."
                )
            if dependency == task_id:
                raise ValueError(f"Task {task_id} cannot depend on itself.")

    return task_map


def _topological_order(task_map):
    """Return tasks in dependency order, or raise for a dependency cycle."""
    successors = {task_id: [] for task_id in task_map}
    remaining_dependencies = {}

    for task_id, task in task_map.items():
        dependencies = task.get("dependencies", [])
        remaining_dependencies[task_id] = len(dependencies)
        for dependency in dependencies:
            successors[dependency].append(task_id)

    ready = [
        task_id
        for task_id, count in remaining_dependencies.items()
        if count == 0
    ]
    order = []

    while ready:
        current = ready.pop(0)
        order.append(current)
        for successor in successors[current]:
            remaining_dependencies[successor] -= 1
            if remaining_dependencies[successor] == 0:
                ready.append(successor)

    if len(order) != len(task_map):
        raise ValueError(
            "Circular dependencies detected. Please review the task dependencies."
        )

    return order, successors


def calculate_schedule(tasks, project_start):
    """Calculate earliest start and inclusive finish dates for each task."""
    task_map = _validate_tasks(tasks)
    order, _ = _topological_order(task_map)
    scheduled = {}

    for task_id in order:
        task = task_map[task_id]
        dependencies = task.get("dependencies", [])

        if dependencies:
            start = max(
                scheduled[dependency]["finish"]
                for dependency in dependencies
            ) + timedelta(days=1)
        else:
            start = project_start

        finish = start + timedelta(days=task["duration"] - 1)
        scheduled[task_id] = {
            "id": task_id,
            "name": task["name"],
            "duration": task["duration"],
            "dependencies": dependencies,
            "start": start,
            "finish": finish,
        }

    return [scheduled[task_id] for task_id in order]


def calculate_project_duration(schedule):
    """Return the inclusive calendar-day span of a generated schedule."""
    if not schedule:
        return 0
    earliest_start = min(task["start"] for task in schedule)
    latest_finish = max(task["finish"] for task in schedule)
    return (latest_finish - earliest_start).days + 1


def calculate_critical_path(tasks):
    """Calculate CPM timings, float, critical tasks, and all critical paths.

    Returns the keys used by the Streamlit dashboard, including both
    ``critical_path`` (the first path, for compatibility) and
    ``critical_paths`` (all complete critical paths).
    """
    task_map = _validate_tasks(tasks)

    if not task_map:
        return {
            "execution_order": [],
            "early_start": {},
            "early_finish": {},
            "late_start": {},
            "late_finish": {},
            "total_float": {},
            "critical_tasks": [],
            "critical_path": [],
            "critical_paths": [],
            "project_duration": 0,
        }

    order, successors = _topological_order(task_map)
    early_start = {}
    early_finish = {}

    # Forward pass
    for task_id in order:
        dependencies = task_map[task_id].get("dependencies", [])
        early_start[task_id] = max(
            (early_finish[dependency] for dependency in dependencies),
            default=0,
        )
        early_finish[task_id] = (
            early_start[task_id] + task_map[task_id]["duration"]
        )

    project_duration = max(early_finish.values())
    late_start = {}
    late_finish = {}

    # Backward pass
    for task_id in reversed(order):
        task_successors = successors[task_id]
        late_finish[task_id] = min(
            (late_start[successor] for successor in task_successors),
            default=project_duration,
        )
        late_start[task_id] = (
            late_finish[task_id] - task_map[task_id]["duration"]
        )

    total_float = {
        task_id: late_start[task_id] - early_start[task_id]
        for task_id in order
    }
    critical_tasks = [task_id for task_id in order if total_float[task_id] == 0]
    critical_set = set(critical_tasks)

    # A critical edge joins zero-float tasks that follow one another without
    # a scheduling gap. This allows all complete critical paths to be found.
    critical_successors = {task_id: [] for task_id in critical_tasks}
    critical_predecessors = {task_id: [] for task_id in critical_tasks}

    for task_id in critical_tasks:
        for successor in successors[task_id]:
            if (
                successor in critical_set
                and early_finish[task_id] == early_start[successor]
            ):
                critical_successors[task_id].append(successor)
                critical_predecessors[successor].append(task_id)

    path_starts = [
        task_id
        for task_id in critical_tasks
        if not critical_predecessors[task_id]
    ]
    critical_paths = []

    def walk_path(task_id, current_path):
        next_tasks = critical_successors[task_id]
        if not next_tasks:
            if early_finish[task_id] == project_duration:
                critical_paths.append(current_path + [task_id])
            return
        for next_task in next_tasks:
            walk_path(next_task, current_path + [task_id])

    for start_task in path_starts:
        walk_path(start_task, [])

    # Keep a backward-compatible single-path field.
    critical_path = critical_paths[0] if critical_paths else []

    return {
        "execution_order": order,
        "early_start": early_start,
        "early_finish": early_finish,
        "late_start": late_start,
        "late_finish": late_finish,
        "total_float": total_float,
        "critical_tasks": critical_tasks,
        "critical_path": critical_path,
        "critical_paths": critical_paths,
        "project_duration": project_duration,
    }
