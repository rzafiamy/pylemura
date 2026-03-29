"""Tests for the default logger."""
from pylemura.logger.default_logger import DefaultLogger
from pylemura.types.logger import LogLevel


def test_logger_emits_problem_and_hints(capsys):
    logger = DefaultLogger(level=LogLevel.DEBUG, colorize=False)

    logger.error(
        "Request failed",
        {
            "problem": "backend unavailable",
            "hints": ["Check the provider connection", "Retry after startup"],
            "status": 503,
        },
    )

    captured = capsys.readouterr()
    assert "Request failed" in captured.err
    assert '"status": 503' in captured.err
    assert "Problem: backend unavailable" in captured.err
    assert "Check the provider connection" in captured.err
    assert "Retry after startup" in captured.err
