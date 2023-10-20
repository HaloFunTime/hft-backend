import datetime
import logging

import pytz

from apps.halo_infinite.utils import get_service_record_data
from apps.link.models import DiscordXboxLiveLink
from apps.season_05.models import Domain

logger = logging.getLogger(__name__)


def get_current_time() -> datetime.datetime:
    return datetime.datetime.now(pytz.timezone("America/Denver"))


def get_active_domains() -> list[Domain]:
    # Calculate an "assessment date" anchored to the daily in-game reset time.
    # If we're before the daily reset, use yesterday's date. Otherwise use today's date.
    now = get_current_time()
    assessment_date = (
        now.date() if now.hour >= 11 else now.date() - datetime.timedelta(days=1)
    )
    return Domain.objects.filter(effective_date__lte=assessment_date)


def score_domain(domain: Domain, service_record_data_by_playlist: dict) -> (int, bool):
    playlist_id = domain.playlist_id
    sr_keys = service_record_data_by_playlist[playlist_id].keys()
    score = 0
    for sr_key in sr_keys:
        stat_path = domain.stat.split("_")
        data = service_record_data_by_playlist[playlist_id][sr_key]
        found = True
        while len(stat_path) > 0:
            stat_piece = stat_path.pop(0)
            if stat_piece in data:
                data = data[stat_piece]
            else:
                found = False
                break
        if found:
            if isinstance(data, int):
                score += data
            else:
                # Medal count case (it's the only non integer data)
                medals_list = data
                for medal in medals_list:
                    if medal["NameId"] == domain.medal_id:
                        score += medal["Count"]
                        continue

    return min(score, domain.max_score), score >= domain.max_score


def get_domain_score_info(link: DiscordXboxLiveLink | None) -> dict:
    domain_score_dicts = []
    if link is not None:
        domains = get_active_domains()
        service_record_data_by_playlist = {}
        playlist_ids = set()
        for domain in domains:
            playlist_ids.add(domain.playlist_id)
        for playlist_id in playlist_ids:
            service_record_data_by_playlist[playlist_id] = get_service_record_data(
                link.xbox_live_account_id, "5", playlist_id
            )
        for domain in domains:
            current_score, is_mastered = score_domain(
                domain, service_record_data_by_playlist
            )
            domain_score_dicts.append(
                {
                    "name": domain.name,
                    "description": domain.description,
                    "effective_date": domain.effective_date,
                    "current_score": current_score,
                    "max_score": domain.max_score,
                    "is_mastered": is_mastered,
                }
            )
    return domain_score_dicts
