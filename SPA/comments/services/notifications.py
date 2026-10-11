from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction


COMMENTS_GROUP = "comments"


def notify_comments_changed():
    def publish():
        async_to_sync(get_channel_layer().group_send)(
            COMMENTS_GROUP, {"type": "comments.changed"},
        )

    # A Redis outage must not turn a committed comment/vote into an HTTP error.
    # Django logs failed callbacks; reconnecting browsers fetch fresh data.
    transaction.on_commit(publish, robust=True)
