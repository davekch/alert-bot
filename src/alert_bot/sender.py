import argparse
import json
from contextlib import contextmanager
from datetime import datetime
import logging
from pathlib import Path
import os

from alert_bot import load_config, make_fifo, Config
from alert_bot.handlers import register_plugins, get_handler, create_handlers
from alert_bot.record import Record


logger = logging.getLogger(__name__)


@contextmanager
def open_pid_file(path: Path):
    path.write_text(str(os.getpid()))
    try:
        yield
    finally:
        path.unlink()


def is_daemon_ready(pid_file: Path) -> bool:
    try:
        pid = int(pid_file.read_text())
    except Exception:
        return False
    try:
        os.kill(pid, 0)  # check if process exists
        return True
    except ProcessLookupError:
        return False


def send_to_handlers(data: dict, default_handlers: list):
    record = Record(subject=data["subject"], body=data["body"], timestamp=datetime.fromisoformat(data["timestamp"]))
    # get additional handlers to send this to
    handlers = data.get("handlers", [])
    # add handlers in set so that there are no duplicates
    for handler_name in set(handlers + default_handlers):
        handler = get_handler(handler_name)
        if handler:
            logger.debug(f"pass record to handler {handler_name}")
            handler.handle(record)
        else:
            logger.error(f"handler {handler_name} not found; drop message {record}")


def setup(config_path: str, loglevel: str=None) -> Config:
    config = load_config(config_path)
    if loglevel:
        config.tool.logging_level = loglevel
    config.setup_logging()
    if config.tool.allow_plugins:
        register_plugins()
    create_handlers(config)
    make_fifo(config)
    return config


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-c", "--config", metavar="path", help="path to config file")
    return parser.parse_args()


def main():
    args = get_args()
    config = setup(args.config, "DEBUG" if args.debug else None)
    fifo_path = config.tool.fifo_path
    default_handlers = config.tool.handlers
    
    with open_pid_file(config.tool.pid_file):
        while True:
            with fifo_path.open() as fifo:
                for line in fifo:  # blocks
                    logger.debug(f"got line from fifo: {line}")
                    data = json.loads(line)
                    send_to_handlers(data, default_handlers)


if __name__ == "__main__":
    main()
