from notify import notification

from . import AlertHandler, Record


class NotificationHandler(AlertHandler):
    def handle(self, message: Record):
        notification(
            message.subject,
            message=message.body,
        )
