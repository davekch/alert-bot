# alert-bot
Pipe the output of terminal commands to any destination.

create a desktop notification as soon as a command finishes:
```bash
long_command && echo finished | alert-bot --handler notify
```

get an email if a command produces an error:
```bash
some_command | grep --line-buffered ERROR | alert-bot --handler email --subject "some_command produced an error"
```

or send it via telegram:
```bash
poll_favourite_website_for_updates | alert-bot -s "new content!" --handlers telegram
```

## installation
```bash
pip install git+https://github.com/davekch/alert-bot.git
```

with support for desktop notifications and telegram, respectively:
```bash
pip install "alert-bot[notify,telegram] @ git+https://github.com/davekch/alert-bot.git"
```

## usage
`alert-bot-daemon` needs to run in the background. A configuration file gets created on the first run in `~/.config/alert-bot/config.toml`.

Example configuration with various handlers to send via telegram or mail:
```toml
[tool]
fifo_path = "/tmp/alert-bot.fifo"
handlers = [ "logger",]
logging_level = "INFO"
allow_plugins = false

[handlers.telegram]
type = "telegram"

[handlers.telegram.config]
token = "1234:abcd"
chat_id = "1234"
```
