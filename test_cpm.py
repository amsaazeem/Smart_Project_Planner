
from src.scheduler import calculate_critical_path


# TEST 1: Original project with one critical path
tasks_one_path = [
    {
        "id": 1,
        "name": "Requirements Analysis",
        "duration": 3,
        "dependencies": []
    },
    {
        "id": 2,
        "name": "Database Design",
        "duration": 4,
        "dependencies": [1]
    },
    {
        "id": 3,
        "name": "UI Design",
        "duration": 2,
        "dependencies": [1]
    },
    {
        "id": 4,
        "name": "System Integration",
        "duration": 3,
        "dependencies": [2, 3]
    }
]


# TEST 2: Project with two critical paths
tasks_two_paths = [
    {
        "id": 1,
        "name": "Requirements Analysis",
        "duration": 2,
        "dependencies": []
    },
    {
        "id": 2,
        "name": "Backend Development",
        "duration": 4,
        "dependencies": [1]
    },
    {
        "id": 3,
        "name": "Frontend Development",
        "duration": 4,
        "dependencies": [1]
    },
    {
        "id": 4,
        "name": "System Integration",
        "duration": 3,
        "dependencies": [2, 3]
    },
    {
        "id": 5,
        "name": "Documentation",
        "duration": 2,
        "dependencies": []
    }
]


def display_results(title, tasks):

    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

    result = calculate_critical_path(tasks)

    task_names = {
        task["id"]: task["name"]
        for task in tasks
    }

    print("\nProject Duration:")
    print(result["project_duration"], "days")

    print("\nTask Float:")

    for task_id in result["execution_order"]:
        print(
            task_names[task_id],
            "-> Float:",
            result["total_float"][task_id]
        )

    print("\nAll Critical Paths:")

    for number, path in enumerate(
        result["critical_paths"], start=1
    ):
        path_names = [
            task_names[task_id]
            for task_id in path
        ]

        print(
            f"Critical Path {number}:",
            " -> ".join(path_names)
        )


# Run both tests
display_results(
    "TEST 1: Single Critical Path",
    tasks_one_path
)

display_results(
    "TEST 2: Multiple Critical Paths",
    tasks_two_paths
)
