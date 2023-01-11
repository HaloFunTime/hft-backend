from apps.discord.models import DiscordAccount


def update_or_create_discord_account(discord_id, discord_tag, user):
    return DiscordAccount.objects.update_or_create(
        discord_id=discord_id, defaults={"discord_tag": discord_tag, "creator": user}
    )[0]
