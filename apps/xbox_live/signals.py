import logging

from django.db.models.signals import pre_save
from django.dispatch import receiver

from apps.xbox_live.models import XboxLiveAccount
from apps.xbox_live.utils import get_xuid_for_gamertag

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=XboxLiveAccount)
def xbox_live_account_pre_save(sender, instance, **kwargs):
    instance.xuid = get_xuid_for_gamertag(instance.gamertag)
