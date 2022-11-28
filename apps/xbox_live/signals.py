import logging

from django.db.models.signals import pre_save
from django.dispatch import receiver

from apps.xbox_live.models import XboxLiveAccount

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=XboxLiveAccount)
def xbox_live_account_pre_save(sender, instance, **kwargs):
    logger.debug("Called xbox_live_account_pre_save")
    # TODO: Uncomment the following block of code when xuid data is flowing
    # try:
    #     instance.xuid = get_xuid_for_gamertag(instance.gamertag)
    # except Exception as ex:
    #     logger.error(ex)
