import datetime
from calendar import TUESDAY

import pytz
from django.contrib.auth.models import User

from apps.discord.models import DiscordAccount
from apps.reputation.models import PlusRep


def get_current_time() -> datetime.datetime:
    return datetime.datetime.now(pytz.timezone("America/Denver"))


def get_current_week_start_time() -> datetime.datetime:
    # Return 11AM Denver time on the most recent Tuesday
    now = get_current_time()
    last_tuesday = None
    if now.weekday() == TUESDAY:
        if now.hour >= 11:
            # After cutoff time, today is the most recent Tuesday
            last_tuesday = now.date()
        else:
            # Before cutoff time, seven days ago is the most recent Tuesday
            last_tuesday = now.date() - datetime.timedelta(days=7)
    else:
        offset = (now.weekday() - TUESDAY) % 7
        last_tuesday = now - datetime.timedelta(days=offset)
    return datetime.datetime(
        last_tuesday.year,
        last_tuesday.month,
        last_tuesday.day,
        11,
        0,
        0,
        0,
        pytz.timezone("America/Denver"),
    )


def can_giver_send_rep(giver: DiscordAccount) -> bool:
    # Users are only allowed to give out reputation 3 times per week
    start = get_current_week_start_time()
    end = start + datetime.timedelta(days=7)
    plus_rep_given_in_current_week = PlusRep.objects.filter(
        giver=giver, created_at__range=(start, end)
    ).count()
    rep_given_in_current_week = plus_rep_given_in_current_week
    return rep_given_in_current_week < 3


def can_giver_send_rep_to_receiver(
    giver: DiscordAccount, receiver: DiscordAccount
) -> bool:
    # A user cannot give themself reputation
    if giver.discord_id == receiver.discord_id:
        return False
    # Only one reputation transaction is allowed per week from a giver to a receiver
    start = get_current_week_start_time()
    end = start + datetime.timedelta(days=7)
    plus_rep_given_in_current_week = PlusRep.objects.filter(
        giver=giver, receiver=receiver, created_at__range=(start, end)
    ).count()
    rep_given_in_current_week = plus_rep_given_in_current_week
    return rep_given_in_current_week < 1


def create_new_plus_rep(
    giver: DiscordAccount, receiver: DiscordAccount, message: str, user: User
) -> PlusRep | None:
    if can_giver_send_rep(giver) and can_giver_send_rep_to_receiver(giver, receiver):
        return PlusRep.objects.create(
            giver=giver,
            receiver=receiver,
            message=message,
            creator=user,
        )
    return None
