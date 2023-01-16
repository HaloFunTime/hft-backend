import datetime
from calendar import TUESDAY

import pytz
from django.contrib.auth.models import User
from django.db.models import Count, Q

from apps.discord.models import DiscordAccount
from apps.reputation.models import PlusRep


def get_current_time() -> datetime.datetime:
    return datetime.datetime.now(pytz.timezone("America/Denver"))


def get_week_start_time(timestamp: datetime.datetime) -> datetime.datetime:
    # Return the Tuesday at 11AM Denver time nearest to the timestamp and before it
    prior_tuesday = None
    if timestamp.weekday() == TUESDAY:
        if timestamp.hour >= 11:
            # After cutoff time, today is the most recent Tuesday
            prior_tuesday = timestamp.date()
        else:
            # Before cutoff time, seven days ago is the most recent Tuesday
            prior_tuesday = timestamp.date() - datetime.timedelta(days=7)
    else:
        offset = (timestamp.weekday() - TUESDAY) % 7
        prior_tuesday = timestamp - datetime.timedelta(days=offset)
    return datetime.datetime(
        prior_tuesday.year,
        prior_tuesday.month,
        prior_tuesday.day,
        11,
        0,
        0,
        0,
        pytz.timezone("America/Denver"),
    )


def get_current_week_start_time() -> datetime.datetime:
    # Return 11AM Denver time on the most recent Tuesday
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


def get_top_rep_past_year(count: int) -> list[DiscordAccount]:
    # Returns a list of the top `count` DiscordAccounts, ordered by total rep in the last year,
    # descending, excluding all DiscordAccounts with zero rep in the last year
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
        .order_by("-total_rep", "-unique_rep", "created_at")[:count]
    )

    # Evaluate the queryset at this stage
    top_rep = []
    for receiver in receivers:
        top_rep.append(receiver)

    # Rank every DiscordAccount in the list by `total_rep`
    def rank_data(a):
        def rank_simple(vector):
            return sorted(range(len(vector)), key=vector.__getitem__)

        n = len(a)
        ivec = rank_simple(a)
        svec = [a[rank] for rank in ivec]
        sumranks = 0
        dupcount = 0
        newarray = [0] * n
        for i in range(n):
            sumranks += i
            dupcount += 1
            if i == n - 1 or svec[i] != svec[i + 1]:
                avgrank = sumranks / float(dupcount) + 1
                for j in range(i - dupcount + 1, i + 1):
                    newarray[ivec[j]] = avgrank
                sumranks = 0
                dupcount = 0
        return newarray

    rep_ranks = rank_data([account.total_rep * -1 for account in top_rep])

    # Tack the rank data on too
    for i in range(len(top_rep)):
        top_rep[i].rank = int(rep_ranks[i])

    return top_rep
