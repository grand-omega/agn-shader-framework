"""Smoke test to verify the project scaffold works."""

from src.main import main


def test_main_runs(capsys: object) -> None:
    """Verify main() executes without error."""
    main()
