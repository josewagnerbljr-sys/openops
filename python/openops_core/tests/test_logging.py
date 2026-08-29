import json
import logging as stdlib_logging

from openops_core.logging import JsonFormatter, LogCategory, get_logger


def _make_record(message: str, category: LogCategory | None = None, fields=None):
    record = stdlib_logging.LogRecord(
        name="openops.test",
        level=stdlib_logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=(),
        exc_info=None,
    )
    if category is not None:
        record.category = category.value
    if fields is not None:
        record.fields = fields
    return record


def test_json_formatter_produces_valid_json():
    formatter = JsonFormatter()
    record = _make_record("evento de teste", LogCategory.SECURITY, {"user_id": 42})

    output = formatter.format(record)
    parsed = json.loads(output)

    assert parsed["message"] == "evento de teste"
    assert parsed["category"] == "security"
    assert parsed["fields"] == {"user_id": 42}
    assert "timestamp" in parsed


def test_json_formatter_defaults_to_core_category():
    formatter = JsonFormatter()
    record = _make_record("sem categoria explícita")

    parsed = json.loads(formatter.format(record))

    assert parsed["category"] == "core"


def test_get_logger_does_not_raise(caplog):
    logger = get_logger("openops.test.module")
    logger.info("mensagem informativa", category=LogCategory.MAINTENANCE, snapshot_id="abc123")
    logger.warning("mensagem de aviso")
    logger.error("mensagem de erro", category=LogCategory.SECURITY)
