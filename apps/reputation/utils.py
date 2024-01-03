import datetime
from calendar import MONDAY

import pytz
from django.contrib.auth.models import User
from django.db.models import Count, Q

from apps.discord.models import DiscordAccount
from apps.reputation.models import PlusRep


def get_current_time() -> datetime.datetime:
    return datetime.datetime.now(pytz.timezone("America/Denver"))


def get_week_start_time(timestamp: datetime.datetime) -> datetime.datetime:
    # Return the Monday at 11AM Denver time nearest to the timestamp and before it
    prior_monday = None
    if timestamp.weekday() == MONDAY:
        if timestamp.hour >= 11:
            # After cutoff time, today is the most recent Monday
            prior_monday = timestamp.date()
        else:
            # Before cutoff time, seven days ago is the most recent Monday
            prior_monday = timestamp.date() - datetime.timedelta(days=7)
    else:
        offset = (timestamp.weekday() - MONDAY) % 7
        prior_monday = timestamp - datetime.timedelta(days=offset)
    return pytz.timezone("America/Denver").localize(
        datetime.datetime(
            prior_monday.year,
            prior_monday.month,
            prior_monday.day,
            11,
            0,
            0,
            0,
        )
    )


def get_current_week_start_time() -> datetime.datetime:
    # Return 11AM Denver time on the most recent Monday
    return get_week_start_time(get_current_time())


def get_time_until_reset() -> datetime.timedelta:
    # Add a week to the current time, then calculate the week start for the week that lands in
    current_time = get_current_time()
    next_reset = get_week_start_time(current_time + datetime.timedelta(weeks=1))
    return next_reset - current_time


def count_plus_rep_given_in_current_week(giver: DiscordAccount) -> int:
    start = get_current_week_start_time()
    end = start + datetime.timedelta(days=7)
    return PlusRep.objects.filter(giver=giver, created_at__range=(start, end)).count()


def can_giver_send_rep(giver: DiscordAccount) -> bool:
    # Users are only allowed to give out reputation 3 times per week
    rep_given_in_current_week = count_plus_rep_given_in_current_week(giver)
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


def check_past_year_rep(account: DiscordAccount) -> tuple[int, int]:
    end = get_current_time()
    start = end.replace(year=end.year - 1)
    plus_rep = PlusRep.objects.filter(receiver=account, created_at__range=(start, end))
    unique_rep = plus_rep.values("giver__discord_id").distinct().count()
    total_rep = plus_rep.count()
    return (total_rep, unique_rep)


def get_top_rep_past_year(
    count: int, exclude_ids: list[str] = []
) -> list[DiscordAccount]:
    # Returns a list of the top `count` DiscordAccounts, ordered by total rep in the last year,
    # descending, excluding all DiscordAccounts with zero rep in the last year and excluding
    # all DiscordAccounts specifically excluded in `exclude_ids`.
    if count == 0:
        return []
    end = get_current_time()
    start = end.replace(year=end.year - 1)
    receivers = (
        DiscordAccount.objects.annotate(
            total_rep=Count(
                "receivers", filter=Q(receivers__created_at__range=(start, end))
            ),
            unique_rep=Count(
                "receivers__giver__discord_id",
                distinct=True,
                filter=Q(receivers__created_at__range=(start, end)),
            ),
        )
        .filter(total_rep__gt=0)
        .exclude(discord_id__in=exclude_ids)
        .order_by("-total_rep", "-unique_rep", "created_at")[:count]
    )

    # Evaluate the queryset at this stage
    top_rep = []
    for receiver in receivers:
        top_rep.append(receiver)

    # Rank every DiscordAccount in the list by `total_rep`
    sorted_rep = [account.total_rep for account in top_rep]
    sorted_rep.sort()
    sorted_rep.reverse()
    rep_ranks = [sorted_rep.index(account.total_rep) + 1 for account in top_rep]

    # Tack the rank data on too
    for i in range(len(top_rep)):
        top_rep[i].rank = int(rep_ranks[i])

    return top_rep


def get_partytimers_past_year(
    cap: int, total_rep_min: int, unique_rep_min: int, exclude_ids: list[str] = []
) -> list[DiscordAccount]:
    # Returns a list of up to `cap` DiscordAccounts, ordered by total rep and unique rep in the last year, descending,
    # excluding all DiscordAccounts with less than `total_rep_min` total rep and `unique_rep_min` unique rep,
    # as well as all DiscordAccounts specifically excluded in `exclude_ids`.
    end = get_current_time()
    start = end.replace(year=end.year - 1)
    receivers = (
        DiscordAccount.objects.annotate(
            total_rep=Count(
                "receivers", filter=Q(receivers__created_at__range=(start, end))
            ),
            unique_rep=Count(
                "receivers__giver__discord_id",
                distinct=True,
                filter=Q(receivers__created_at__range=(start, end)),
            ),
        )
        .filter(total_rep__gte=total_rep_min, unique_rep__gte=unique_rep_min)
        .exclude(discord_id__in=exclude_ids)
        .order_by("-total_rep", "-unique_rep", "created_at")[:cap]
    )

    # Evaluate the queryset at this stage
    partytimers = []
    for receiver in receivers:
        partytimers.append(receiver)

    # Rank every DiscordAccount in the list by `total_rep`
    sorted_rep = [account.total_rep for account in partytimers]
    sorted_rep.sort()
    sorted_rep.reverse()
    rep_ranks = [sorted_rep.index(account.total_rep) + 1 for account in partytimers]

    # Tack the rank data on too
    for i in range(len(partytimers)):
        partytimers[i].rank = int(rep_ranks[i])

    return partytimers
