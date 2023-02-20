from django.contrib import admin

from apps.overrides.admin import AutofillCreatorModelAdmin
from apps.xbox_live.models import (
    XboxLiveAccount,
    XboxLiveOAuthToken,
    XboxLiveUserToken,
    XboxLiveXSTSToken,
)


@admin.register(XboxLiveAccount)
class XboxLiveAccountAdmin(AutofillCreatorModelAdmin):
    list_display = ("xuid", "gamertag", "creator")
    list_filter = ("creator",)
    fields = ("gamertag", "xuid", "creator")


@admin.register(XboxLiveOAuthToken)
class XboxLiveOAuthTokenAdmin(AutofillCreatorModelAdmin):
    list_display = ("id", "created_at", "expires_in", "token_type", "creator")
    list_filter = ("creator",)
    fields = (
        "token_type",
        "expires_in",
        "scope",
        "access_token",
        "refresh_token",
        "user_id",
        "creator",
    )


@admin.register(XboxLiveUserToken)
class XboxLiveUserTokenAdmin(AutofillCreatorModelAdmin):
    list_display = ("id", "issue_instant", "not_after", "creator")
    list_filter = ("creator",)
    fields = (
        "issue_instant",
        "not_after",
        "token",
        "uhs",
        "creator",
    )


@admin.register(XboxLiveXSTSToken)
class XboxLiveXSTSTokenAdmin(AutofillCreatorModelAdmin):
    list_display = ("id", "issue_instant", "not_after", "creator")
    list_filter = ("creator",)
    fields = (
        "issue_instant",
        "not_after",
        "token",
        "uhs",
        "creator",
    )
