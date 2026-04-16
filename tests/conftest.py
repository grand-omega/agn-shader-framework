"""Shared test fixtures."""

import pytest


@pytest.fixture
def tmp_task_list(tmp_path):
    """Create a temporary task-list.json for testing."""
    task_file = tmp_path / "task-list.json"
    task_file.write_text('{"plan": null, "dependencies": [], "tasks": [], "last_updated": null}')
    return task_file
