import datetime
import logging
from collections import deque
from decimal import Decimal

from django.db.models import Q

from apps.discord.models import DiscordAccount
from apps.fun_time_friday.models import (
    FunTimeFridayVoiceConnect,
    FunTimeFridayVoiceDisconnect,
)

logger = logging.getLogger(__name__)


def get_voice_connection_report(
    time_start: datetime.datetime, time_end: datetime.datetime
) -> dict | None:
    import json

    logger.warn(time_start)
    logger.warn(time_end)
    connects = list(
        FunTimeFridayVoiceConnect.objects.filter(
            Q(connected_at__gte=time_start) & Q(connected_at__lte=time_end)
        ).order_by("connected_at")
    )
    disconnects = list(
        FunTimeFridayVoiceDisconnect.objects.filter(
            Q(disconnected_at__gte=time_start) & Q(disconnected_at__lte=time_end)
        ).order_by("disconnected_at")
    )
    unique_discord_accounts = set()
    for connect in connects:
        unique_discord_accounts.add(connect.connector_discord)
    for disconnect in disconnects:
        unique_discord_accounts.add(disconnect.disconnector_discord)

    unique_channel_ids = set()
    total_connection_time = datetime.timedelta(seconds=0)
    discord_ids_by_seconds_connected = {}
    for discord_account in unique_discord_accounts:
        connection_data = get_voice_connections(
            discord_account=discord_account, time_start=time_start, time_end=time_end
        )
        user_connection_time = datetime.timedelta(seconds=0)
        for connection in connection_data:
            unique_channel_ids.add(connection["channel_id"])
            user_connection_time += connection["time_connected"]
        seconds_connected = int(user_connection_time.total_seconds())
        if seconds_connected in discord_ids_by_seconds_connected:
            discord_ids_by_seconds_connected[seconds_connected].append(
                discord_account.discord_id
            )
        else:
            discord_ids_by_seconds_connected[seconds_connected] = [
                discord_account.discord_id
            ]
        total_connection_time += user_connection_time

    logger.warn(unique_channel_ids)
    logger.warn(total_connection_time)
    logger.warn(json.dumps(discord_ids_by_seconds_connected))

    if discord_ids_by_seconds_connected == {}:
        return None

    # Determine the Party Animals
    most_seconds_connected = max(discord_ids_by_seconds_connected.keys())
    second_most_seconds_connected = sorted(discord_ids_by_seconds_connected.keys())[-2]
    third_most_seconds_connected = sorted(discord_ids_by_seconds_connected.keys())[-3]
    party_animals = []
    for discord_id in discord_ids_by_seconds_connected[most_seconds_connected]:
        party_animals.append(
            {"discord_id": discord_id, "seconds": most_seconds_connected}
        )
    for discord_id in discord_ids_by_seconds_connected[second_most_seconds_connected]:
        party_animals.append(
            {"discord_id": discord_id, "seconds": second_most_seconds_connected}
        )
    for discord_id in discord_ids_by_seconds_connected[third_most_seconds_connected]:
        party_animals.append(
            {"discord_id": discord_id, "seconds": third_most_seconds_connected}
        )
    party_animals[:3]

    # Determine the Party Poopers
    least_seconds_connected = min(discord_ids_by_seconds_connected.keys())
    party_poopers = []
    for discord_id in discord_ids_by_seconds_connected[least_seconds_connected]:
        party_poopers.append(
            {"discord_id": discord_id, "seconds": least_seconds_connected}
        )

    logger.warn(
        json.dumps(
            {
                "total_players": len(unique_discord_accounts),
                "total_hours": round(
                    Decimal(total_connection_time.total_seconds() / 3600), 3
                ),
                "total_channels": len(unique_channel_ids),
                "party_animals": party_animals,
                "party_poopers": party_poopers,
            }
        )
    )
    return {
        "total_players": len(unique_discord_accounts),
        "total_hours": round(Decimal(total_connection_time.total_seconds() / 3600), 3),
        "total_channels": len(unique_channel_ids),
        "party_animals": party_animals,
        "party_poopers": party_poopers,
    }


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
