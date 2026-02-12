"""Tests for shared.observability -- structured logging."""

from __future__ import annotations

from ailine_runtime.shared.observability import configure_logging, get_logger, log_event


class TestConfigureLogging:
    def test_json_mode(self):
        # Should not raise
        configure_logging(json_output=True, level="DEBUG")

    def test_console_mode(self):
        # Should not raise
        configure_logging(json_output=False, level="INFO")


class TestGetLogger:
    def test_returns_bound_logger(self):
        logger = get_logger("test.module")
        assert logger is not None


class TestLogEvent:
    def test_does_not_raise(self):
        configure_logging(json_output=False, level="DEBUG")
        # Should not raise even without prior configuration
        log_event("test_event", foo="bar", count=42)
