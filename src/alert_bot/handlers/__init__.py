from abc import ABC, abstractmethod
import importlib.metadata
import json
from typing import Type
import logging

from alert_bot import Config, HandlerConfig
from alert_bot.record import Record


logger = logging.getLogger(__name__)

HANDLER_CLASSES = {}
HANDLER_INSTANCES = {}


class AlertHandler(ABC):
    @abstractmethod
    def handle(self, message: Record):
        ...


def register_handler(name: str):
    def decorator(cls: Type[AlertHandler]):
        HANDLER_CLASSES[name] = cls
        return cls
    return decorator


def get_handler_class(name: str) -> Type[AlertHandler]:
    return HANDLER_CLASSES.get(name)


def get_handler(name: str) -> AlertHandler:
    return HANDLER_INSTANCES.get(name)


@register_handler("print")
class PrintHandler(AlertHandler):
    def handle(self, message: Record):
        print(json.dumps(message.as_dict()))


@register_handler("logger")
class LogHandler(AlertHandler):
    def handle(self, message):
        logger.info(f"received record {message}")


try:
    from alert_bot.handlers.telegram import TelegramHandler
    register_handler("telegram")(TelegramHandler)
except ImportError as e:
    pass


def register_plugins():
    plugins = importlib.metadata.entry_points(group="alert-bot.plugins")
    for plugin in plugins:
        name = plugin.name
        cls = plugin.load()
        if not issubclass(cls, AlertHandler):
            print(f"cannot register handler {name}: is not an AlertHandler")
            continue
        HANDLER_CLASSES[name] = cls


def create_handlers(config: Config):
    # create handlers for every entry that is listed as a default handler or has an entry in the handlers section
    create = set(config.tool.handlers + list(config.handlers.keys()))
    for instance_name in create:
        # check if this name has a config
        if instance_name in config.handlers:
            handler_config = config.handlers[instance_name]
        else:
            # assume that name refers to a type of handler instead of a specific configuration
            handler_config = HandlerConfig(type=instance_name)
        # get the class to construct this handler
        handler_class = get_handler_class(handler_config.type)
        if not handler_class:
            print(f"failed to construct handler {instance_name}: no such handler: {handler_config.type}")
            continue
        try:
            handler = handler_class(**handler_config.config)
            logger.info(f"handler {instance_name} ready")
            HANDLER_INSTANCES[instance_name] = handler
        except TypeError as e:
            logger.error(f"could not load handler {instance_name}: misconfigured")
