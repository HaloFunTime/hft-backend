from django.contrib import admin

from apps.discord.models import DiscordAccount, DiscordLFGThreadHelpPrompt
from apps.overrides.admin import AutofillCreatorModelAdmin, linkify


@admin.register(DiscordAccount)
class DiscordAccountAdmin(AutofillCreatorModelAdmin):
    list_display = ("discord_id", "discord_username", "creator")
    list_filter = ("creator",)
    fields = ("discord_username", "discord_id", "creator")
    search_fields = ["discord_username"]


@admin.register(DiscordLFGThreadHelpPrompt)
class DiscordLFGThreadHelpPromptAdmin(AutofillCreatorModelAdmin):
    autocomplete_fields = ["help_receiver_discord"]
    list_display = (
        "__str__",
        linkify("help_receiver_discord"),
        "lfg_thread_name",
        "lfg_thread_id",
    )
    list_filter = (
        "help_receiver_discord",
        "lfg_thread_name",
        "lfg_thread_id",
    )
    fields = (
        "help_receiver_discord",
        "lfg_thread_name",
        "lfg_thread_id",
        "creator",
    )
    search_fields = ["help_receiver_discord__discord_username", "lfg_thread_name"]
