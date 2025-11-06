from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
import logging
from pathlib import Path
import os
import toml


@dataclass
class ToolConfig:
    fifo_path: Path = Path("/tmp/alert-bot.fifo")
    handlers: list[str] = field(default_factory=lambda: ["logger"])
    logging_level: str = "INFO"
    logging_format: str = "[%(levelname)-8s] %(name)-16s: %(message)s"
    pid_file: Path = Path("/tmp/alert-bot-daemon.pid")
    allow_plugins: bool = False

    def as_dict(self) -> dict:
        d = asdict(self)
        d["fifo_path"] = str(self.fifo_path)
        d["pid_file"] = str(self.pid_file)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "ToolConfig":
        default = cls()
        return cls(
            fifo_path=Path(data.get("fifo_path", default.fifo_path)),
            handlers=data.get("handlers", default.handlers),
            logging_level=data.get("logging_level", default.logging_level),
            logging_format=data.get("logging_format", default.logging_format),
            pid_file=Path(data.get("pid_file", default.pid_file)),
        )


@dataclass
class HandlerConfig:
    type: str
    config: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "HandlerConfig":
        return cls(
            type=data["type"],
            config=data.get("config", {})
        )


@dataclass
class Config:
    tool: ToolConfig = field(default_factory=ToolConfig)
    handlers: dict[str, HandlerConfig] = field(default_factory=dict)  # maps names of handler *instances* to their configs

    def as_dict(self) -> dict:
        return {
            "tool": self.tool.as_dict(),
            "handlers": {name: hc.as_dict() for name, hc in self.handlers.items()}
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        tool = ToolConfig.from_dict(data.get("tool", {}))

        handlers = {
            name: HandlerConfig.from_dict(hdata)
            for name, hdata in data.get("handlers", {}).items()
        }
        return cls(tool=tool, handlers=handlers)

    def setup_logging(self):
        logging.basicConfig(
            level=self.tool.logging_level,
            format=self.tool.logging_format,
        )


def get_config_path():
    config_dir = Path(
        os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")
    ) / "alert-bot"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.toml"


def load_config(path: str | Path=None) -> Config:
    if not path:
        path = get_config_path()
    else:
        path = Path(path)
    config = Config()
    if not path.exists():
        write_config(config)
        return config

    with path.open() as f:
        data = toml.load(f)

    return Config.from_dict(data)


def write_config(config: Config):
    path = get_config_path()
    config_data = config.as_dict()
    with path.open("w") as f:
        toml.dump(config_data, f)


@contextmanager
def make_fifo(config: Config):
    """
    context manager to create and open a fifo for reading, deletes after closing
    """
    fifo_path = config.tool.fifo_path
    if not fifo_path.exists():
        os.mkfifo(fifo_path)
    try:
        with fifo_path.open() as fifo:
            yield fifo
    finally:
        fifo_path.unlink()
