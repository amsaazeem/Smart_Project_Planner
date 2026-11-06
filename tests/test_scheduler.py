import unittest
from datetime import date

from src.scheduler import (
    calculate_critical_path,
    calculate_project_duration,
    calculate_schedule,
)


class SchedulerTests(unittest.TestCase):
    def test_schedule_dates_and_duration(self):
        tasks = [
            {"id": 1, "name": "Requirements", "duration": 3, "dependencies": []},
            {"id": 2, "name": "Database", "duration": 4, "dependencies": [1]},
            {"id": 3, "name": "UI", "duration": 2, "dependencies": [1]},
            {"id": 4, "name": "Integration", "duration": 3, "dependencies": [2, 3]},
        ]
        schedule = calculate_schedule(tasks, date(2026, 1, 1))
        self.assertEqual(calculate_project_duration(schedule), 10)
        self.assertEqual(schedule[-1]["start"], date(2026, 1, 8))
        self.assertEqual(schedule[-1]["finish"], date(2026, 1, 10))

    def test_cpm_finds_two_critical_paths(self):
        tasks = [
            {"id": 1, "name": "Requirements", "duration": 2, "dependencies": []},
            {"id": 2, "name": "Backend", "duration": 4, "dependencies": [1]},
            {"id": 3, "name": "Frontend", "duration": 4, "dependencies": [1]},
            {"id": 4, "name": "Integration", "duration": 3, "dependencies": [2, 3]},
            {"id": 5, "name": "Documentation", "duration": 2, "dependencies": []},
        ]
        result = calculate_critical_path(tasks)
        self.assertEqual(result["project_duration"], 9)
        self.assertEqual(len(result["critical_paths"]), 2)
        self.assertEqual(result["critical_tasks"], [1, 2, 3, 4])
        self.assertEqual(result["total_float"][5], 7)

    def test_cpm_empty_tasks(self):
        result = calculate_critical_path([])
        self.assertEqual(result["project_duration"], 0)
        self.assertEqual(result["critical_paths"], [])

    def test_missing_dependency_is_rejected(self):
        tasks = [
            {"id": 1, "name": "Task A", "duration": 2, "dependencies": [99]}
        ]
        with self.assertRaisesRegex(ValueError, "missing task"):
            calculate_critical_path(tasks)

    def test_circular_dependency_is_rejected(self):
        tasks = [
            {"id": 1, "name": "Task A", "duration": 2, "dependencies": [2]},
            {"id": 2, "name": "Task B", "duration": 2, "dependencies": [1]},
        ]
        with self.assertRaisesRegex(ValueError, "Circular dependencies"):
            calculate_schedule(tasks, date(2026, 1, 1))


if __name__ == "__main__":
    unittest.main()
