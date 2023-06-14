import datetime
import logging
from collections import deque

from django.db.models import Q

from apps.discord.models import DiscordAccount
from apps.fun_time_friday.models import (
    FunTimeFridayVoiceConnect,
    FunTimeFridayVoiceDisconnect,
)

logger = logging.getLogger(__name__)


def get_voice_connections(
    discord_account: DiscordAccount,
    time_start: datetime.datetime,
    time_end: datetime.datetime,
) -> list[dict]:
    assert discord_account is not None
    assert time_start is not None
    assert time_end is not None
    voice_connections = []
    connects = deque(
        list(
            FunTimeFridayVoiceConnect.objects.filter(connector_discord=discord_account)
            .filter(Q(connected_at__gte=time_start) & Q(connected_at__lte=time_end))
            .order_by("connected_at")
        )
    )
    disconnects = deque(
        list(
            FunTimeFridayVoiceDisconnect.objects.filter(
                disconnector_discord=discord_account
            )
            .filter(
                Q(disconnected_at__gte=time_start) & Q(disconnected_at__lte=time_end)
            )
            .order_by("disconnected_at")
        )
    )
    while connects and disconnects:
        connect = None
        disconnect = None
        next_connect = connects[0]
        next_disconnect = disconnects[0]
        # If next connect matches next disconnect, we can pop them both
        if (
            next_connect is not None
            and next_disconnect is not None
            and next_connect.channel_id == next_disconnect.channel_id
        ):
            connect = connects.popleft()
            disconnect = disconnects.popleft()
        # Otherwise we must look one further ahead in each deque
        else:
            second_connect = None
            try:
                second_connect = connects[1]
            except IndexError:
                pass
            second_disconnect = None
            try:
                second_disconnect = disconnects[1]
            except IndexError:
                pass
            # Check the second connect (if it matches, pop twice)
            if (
                second_connect is not None
                and second_connect.channel_id == next_disconnect.channel_id
            ):
                connects.popleft()  # Pop and discard "next" connect
                connect = connects.popleft()
                disconnect = disconnects.popleft()
            # Check the second disconnect (if it matches, pop twice)
            elif (
                second_disconnect is not None
                and next_connect.channel_id == second_disconnect.channel_id
            ):
                disconnects.popleft()  # Pop and discard "next" disconnect
                connect = connects.popleft()
                disconnect = disconnects.popleft()
            # If neither of the next records match, pop both
            else:
                connects.popleft()
                disconnects.popleft()

        if connect is not None and disconnect is not None:
            time_connected = disconnect.disconnected_at - connect.connected_at
            voice_connections.append(
                {
                    "channel_id": connect.channel_id,
                    "connect": connect,
                    "disconnect": disconnect,
                    "time_connected": time_connected,
                }
            )
    return voice_connections
