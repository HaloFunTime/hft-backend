import logging

from django.db.models.signals import pre_save
from django.dispatch import receiver

from apps.xbox_live.models import XboxLiveAccount
from apps.xbox_live.utils import get_gamertag_from_xuid, get_xuid_and_exact_gamertag

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=XboxLiveAccount)
def xbox_live_account_pre_save(sender, instance, **kwargs):
    if instance.xuid is None:
        xuid_gamertag_tuple = get_xuid_and_exact_gamertag(instance.gamertag)
        instance.xuid = xuid_gamertag_tuple[0]
        instance.gamertag = xuid_gamertag_tuple[1]
    else:
        instance.gamertag = get_gamertag_from_xuid(instance.xuid)
