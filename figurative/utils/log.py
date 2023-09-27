import logging
import sys
import io

from typing import List, Tuple, Optional, Callable

figurative_verbosity = 0
DEFAULT_LOG_LEVEL = logging.WARNING
logfmt = "%(asctime)s: [%(process)d] %(name)s:%(levelname)s %(message)s"
formatter = logging.Formatter(logfmt)


def get_figurative_logger_names() -> List[str]:
    return [name for name in logging.root.manager.loggerDict if name.split(".", 1)[0] == "figurative"]  # type: ignore


class CallbackStream(io.StringIO):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def write(self, log_str):
        self.callback(log_str)


class FigurativeContextFilter(logging.Filter):
    """
    This is a filter which injects contextual information into the log.
    """

    def summarized_name(self, name: str) -> str:
        """
        Produce a summarized record name
          i.e. figurative.core.executor -> m.c.executor
        """
        components = name.split(".")
        prefix = ".".join(c[0] for c in components[:-1])
        return f"{prefix}.{components[-1]}"

    colors_disabled = False

    coloring = {"DEBUG": "magenta", "WARNING": "yellow", "ERROR": "red", "INFO": "blue"}
    colors = dict(
        zip(
            ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"],
            map(str, range(30, 30 + 8)),
        )
    )

    color_map = {}
    for k, v in coloring.items():
        color_map[k] = colors[v]

    colored_levelname_format = "\x1b[{}m{}:\x1b[0m"
    plain_levelname_format = "{}:"

    def colored_level_name(self, levelname: str) -> str:
        """
        Colors the logging level in the logging record
        """
        if self.colors_disabled:
            return self.plain_levelname_format.format(levelname)
        else:
            return self.colored_levelname_format.format(self.color_map[levelname], levelname)

    def filter(self, record: logging.LogRecord) -> bool:
        if not record.name.startswith("figurative"):
            return True

        record.name = self.summarized_name(record.name)
        record.levelname = self.colored_level_name(record.levelname)
        return True


def disable_colors() -> None:
    FigurativeContextFilter.colors_disabled = True


def get_levels() -> List[List[Tuple[str, int]]]:
    all_loggers = get_figurative_logger_names()
    return [
        # 0
        [(x, DEFAULT_LOG_LEVEL) for x in all_loggers],
        # 1
        [
            ("figurative.main", logging.INFO),
            ("figurative.ethereum.*", logging.INFO),
            ("figurative.native.*", logging.INFO),
            ("figurative.core.figurative", logging.INFO),
        ],
        # 2 (-v)
        [
            ("figurative.core.worker", logging.INFO),
            ("figurative.platforms.*", logging.DEBUG),
            ("figurative.ethereum", logging.DEBUG),
            ("figurative.core.plugin", logging.INFO),
            ("figurative.wasm.*", logging.INFO),
            ("figurative.utils.emulate", logging.INFO),
        ],
        # 3 (-vv)
        [("figurative.native.cpu.*", logging.DEBUG), ("figurative.wasm.*", logging.DEBUG)],
        # 4 (-vvv)
        [
            ("figurative.native.memory", logging.DEBUG),
            ("figurative.native.cpu.*", logging.DEBUG),
            ("figurative.native.cpu.*.registers", logging.DEBUG),
            ("figurative.core.plugin", logging.DEBUG),
            ("figurative.utils.helpers", logging.INFO),
        ],
        # 5 (-vvvv)
        [
            ("figurative.core.figurative", logging.DEBUG),
            ("figurative.ethereum.*", logging.DEBUG),
            ("figurative.native.*", logging.DEBUG),
            ("figurative.core.smtlib", logging.DEBUG),
            ("figurative.core.smtlib.*", logging.DEBUG),
        ],
    ]


def get_verbosity(logger_name: str) -> int:
    def match(name: str, pattern: str):
        """
        Pseudo globbing that only supports full fields. 'a.*.d' matches 'a.b.d'
        but not 'a.b.c.d'.
        """
        name_l, pattern_l = name.split("."), pattern.split(".")
        if len(name_l) != len(pattern_l):
            return False
        for name_f, pattern_f in zip(name_l, pattern_l):
            if pattern_f == "*":
                continue
            if name_f != pattern_f:
                return False
        return True

    for level in range(figurative_verbosity, 0, -1):
        for pattern, log_level in get_levels()[level]:
            if match(logger_name, pattern):
                return log_level
    return DEFAULT_LOG_LEVEL


def set_verbosity(setting: int) -> None:
    """Set the global verbosity (0-5)."""
    global figurative_verbosity
    figurative_verbosity = min(max(setting, 0), len(get_levels()) - 1)
    for logger_name in get_figurative_logger_names():
        logger = logging.getLogger(logger_name)
        # min because more verbosity == lower numbers
        # This means if you explicitly call setLevel somewhere else in the source, and it's *more*
        # verbose, it'll stay that way even if figurative_verbosity is 0.
        logger.setLevel(min(get_verbosity(logger_name), logger.getEffectiveLevel()))


def register_log_callback(callback: Callable[[Optional[str]], None]) -> None:
    callback_handler = logging.StreamHandler(CallbackStream(callback))
    callback_handler.setFormatter(formatter)
    callback_handler.addFilter(FigurativeContextFilter())
    init_logging(callback_handler)


def default_handler() -> logging.Handler:
    """Return a default Figurative logger with a nice formatter and filter."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(FigurativeContextFilter())
    return handler


def init_logging(handler: Optional[logging.Handler] = None) -> None:
    """
    Initialize logging for Figurative, given a handler or by default use `default_logger()`
    """
    logger = logging.getLogger("figurative")
    logger.parent = None  # type: ignore

    # Explicitly set the level so that we don't use root's. If root is at DEBUG,
    # then _a lot_ of logs will be printed if the user forgets to set
    # figurative's logger
    logger.setLevel(DEFAULT_LOG_LEVEL)

    if handler is None:
        handler = default_handler()

    # Finally attach to Figurative
    logger.addHandler(handler)
