import logging

from apps.link.models import DiscordXboxLiveLink

logger = logging.getLogger(__name__)


def get_illuminated_qualified(links: list[DiscordXboxLiveLink]) -> list[str]:
    # TODO: Implement Illuminated logic
    illuminated_qualified_discord_ids = []
    return illuminated_qualified_discord_ids


def get_dynamo_qualified(links: list[DiscordXboxLiveLink]) -> list[str]:
    # TODO: Implement Dynamo logic
    dynamo_qualified_discord_ids = []
    return dynamo_qualified_discord_ids
