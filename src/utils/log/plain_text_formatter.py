import logging

from rich.console import Console


class PlainTextFormatter(logging.Formatter):
    """Strips Rich markup and ANSI codes from log messages for file output."""

    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
        # We use a dummy console to "render" the text to plain string
        # force_terminal=False ensures no ANSI color codes are generated
        self._console = Console(width=1000, force_terminal=False)

    def format(self, record):
        # Allow standard formatting (timestamp, level, etc)
        original_msg = record.msg
        # Render markup and get plain text
        if isinstance(record.msg, str):
            record.msg = self._console.render_str(record.msg).plain

        result = super().format(record)
        # Restore original message in case other handlers need it
        record.msg = original_msg
        return result
