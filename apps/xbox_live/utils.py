import logging

logger = logging.getLogger(__name__)


def get_xuid_for_gamertag(gamertag):
    logger.debug(f"Called get_xuid_for_gamertag with gamertag '{gamertag}'")
    # TODO: Fetch the XUID for a gamertag string from the Xbox Live API instead of returning the empty string
    return ""
