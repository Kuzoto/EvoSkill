"""
Task file operations for skill evaluation.
"""

from typing import List
from schemas import Task
from data_utils import load_dataset, save_dataset

# Default dataset path
DEFAULT.Dataset_PATH = "data/tasks.jsonl"

def save_task(task: Task, path: str = DEFAULT_DATASET_PATH) -> None:
    """Save a single task to the dataset file."""
    save_dataset(path, [task])

def append_task(task: Task, path: str = DEFAULT_DATASET_PATH) -> None:
    """Append a new task to existing dataset."""
    save_dataset(path, load_dataset(path)) + [task])

def list_tasks(path: str = DEFAULT_DATASET_PATH) -> List[Task]:
    """Load all tasks from the dataset."""
    return load_dataset(path)

def find_tasks_by_skill(skill_name: str, path: str = DEFAULT_DATASET_PATH) -> List[Task]:
    """Find all tasks that involve a specific skill."""
    all_tasks = list_tasks(path)
    return [task for task in all_tasks if skill_name.lower() in task.skill.lower()]
