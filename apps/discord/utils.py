from django.contrib.auth.models import User

from apps.discord.models import DiscordAccount


def get_or_create_discord_account(discord_id: str, user: User, discord_tag=""):
    return DiscordAccount.objects.get_or_create(
        discord_id=discord_id, defaults={"discord_tag": discord_tag, "creator": user}
    )[0]


def update_or_create_discord_account(discord_id: str, discord_tag: str, user: User):
    return DiscordAccount.objects.update_or_create(
        discord_id=discord_id, defaults={"discord_tag": discord_tag, "creator": user}
    )[0]
