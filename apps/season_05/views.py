import datetime
import logging
import random

from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.discord.utils import update_or_create_discord_account
from apps.link.models import DiscordXboxLiveLink
from apps.season_05.models import (
    DomainChallengeTeamAssignment,
    DomainChallengeTeamReassignment,
    DomainMaster,
)
from apps.season_05.serializers import (
    CheckDomainsRequestSerializer,
    CheckDomainsResponseSerializer,
    DomainScoreSerializer,
    JoinChallengeRequestSerializer,
    JoinChallengeResponseSerializer,
    ProcessedReassignmentSerializer,
    ProcessReassignmentsRequestSerializer,
    ProcessReassignmentsResponseSerializer,
    SaveMasterRequestSerializer,
    SaveMasterResponseSerializer,
)
from apps.season_05.utils import get_domain_score_info
from config.serializers import StandardErrorSerializer

logger = logging.getLogger(__name__)


class CheckDomainsView(APIView):
    @extend_schema(
        request=CheckDomainsRequestSerializer,
        responses={
            200: CheckDomainsResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Evaluate a Discord User ID by retrieving its verified linked Xbox Live gamertag, querying stats from the Halo
        Infinite API and the HFT DB, and returning a payload indicating the progress the gamertag has made toward the
        Season 5 Domain Challenge.
        """
        validation_serializer = CheckDomainsRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            discord_id = validation_serializer.data.get("discordUserId")
            discord_username = validation_serializer.data.get("discordUsername")
            assignment = None
            link = None
            domains_mastered = 0
            domain_scores = []

            try:
                discord_account = update_or_create_discord_account(
                    discord_id, discord_username, request.user
                )
                try:
                    link = DiscordXboxLiveLink.objects.filter(
                        discord_account_id=discord_account.discord_id, verified=True
                    ).get()
                except DiscordXboxLiveLink.DoesNotExist:
                    pass
                assignment = DomainChallengeTeamAssignment.objects.filter(
                    assignee_id=discord_account.discord_id
                ).get()

                domain_score_info = get_domain_score_info(link)
                for domain_dict in domain_score_info:
                    if domain_dict.get("is_mastered", False):
                        domains_mastered += 1
                    domain_scores.append(
                        DomainScoreSerializer(
                            {
                                "name": domain_dict.get("name"),
                                "description": domain_dict.get("description"),
                                "effectiveDate": domain_dict.get("effective_date"),
                                "currentScore": domain_dict.get("current_score"),
                                "maxScore": domain_dict.get("max_score"),
                                "isMastered": domain_dict.get("is_mastered"),
                            }
                        ).data
                    )
            except DomainChallengeTeamAssignment.DoesNotExist:
                logger.info(
                    "No team assignment exists, so the return payload will be mostly empty."
                )
            except Exception as ex:
                logger.error("Error attempting to check Domain Challenge progress.")
                logger.error(ex)
                raise APIException(
                    "Error attempting to check Domain Challenge progress."
                )
            serializer = CheckDomainsResponseSerializer(
                {
                    "joinedChallenge": assignment is not None,
                    "linkedGamertag": link is not None,
                    "discordUserId": discord_id,
                    "assignedTeam": assignment.team if assignment is not None else None,
                    "domainsMastered": domains_mastered,
                    "domainScores": domain_scores,
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)


# TODO
class CheckTeamsView(APIView):
    pass


class JoinChallengeView(APIView):
    @extend_schema(
        request=JoinChallengeRequestSerializer,
        responses={
            200: JoinChallengeResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Create a TeamAssignment for someone who has not yet joined the Season 5 Domain Challenge.
        """
        validation_serializer = JoinChallengeRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            discord_id = validation_serializer.data.get("discordUserId")
            discord_username = validation_serializer.data.get("discordUsername")

            try:
                assignment = DomainChallengeTeamAssignment.objects.filter(
                    assignee_id=discord_id
                ).get()
            except DomainChallengeTeamAssignment.DoesNotExist:
                assignment = None

            try:
                discord_account = update_or_create_discord_account(
                    discord_id, discord_username, request.user
                )
                new_joiner = False
                if assignment is None:
                    new_joiner = True
                    assignment = DomainChallengeTeamAssignment.objects.create(
                        creator=request.user,
                        assignee=discord_account,
                        team=random.choice(
                            [
                                DomainChallengeTeamAssignment.Teams.FunTimeBot,
                                DomainChallengeTeamAssignment.Teams.HFT_Intern,
                            ]
                        ),
                    )

            except Exception as ex:
                logger.error(
                    "Error attempting to save a Domain Challenge Team Assignment."
                )
                logger.error(ex)
                raise APIException(
                    "Error attempting to save a Domain Challenge Team Assignment."
                )
            serializer = JoinChallengeResponseSerializer(
                {
                    "assignedTeam": assignment.team,
                    "discordUserId": assignment.assignee_id,
                    "newJoiner": new_joiner,
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)


class ProcessReassignmentsView(APIView):
    @extend_schema(
        request=ProcessReassignmentsRequestSerializer,
        responses={
            200: ProcessReassignmentsResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Query all DomainChallengeTeamReassignments for the specified date, update DomainChallengeTeamAssignments as
        requested, and return a payload describing all reassignments that happened.
        """
        validation_serializer = ProcessReassignmentsRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            date = validation_serializer.data.get("date")

            try:
                reassignments = DomainChallengeTeamReassignment.objects.filter(
                    reassignment_date=date
                )
                processed_reassignments = []
                with transaction.atomic():
                    for reassignment in reassignments:
                        assignment = DomainChallengeTeamAssignment.objects.filter(
                            assignee_id=reassignment.reassignee_id
                        ).first()
                        if assignment is not None:
                            assignment.team = reassignment.next_team
                            assignment.save()
                            processed_reassignments.append(
                                ProcessedReassignmentSerializer(
                                    {
                                        "discordUserId": reassignment.reassignee_id,
                                        "team": reassignment.next_team,
                                        "reason": reassignment.reason,
                                    }
                                ).data
                            )
                        reassignment.delete()
            except Exception as ex:
                logger.error(
                    "Error attempting to process Domain Challenge Team Reassignments."
                )
                logger.error(ex)
                raise APIException(
                    "Error attempting to process Domain Challenge Team Reassignments."
                )
            serializer = ProcessReassignmentsResponseSerializer(
                {
                    "date": date,
                    "processedReassignments": processed_reassignments,
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)


class SaveMasterView(APIView):
    @extend_schema(
        request=SaveMasterRequestSerializer,
        responses={
            200: SaveMasterResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Save whether a Discord User ID has already completed the Season 5 Domain Challenge. Update or create a record
        in the DomainMaster table based on that information.
        """
        validation_serializer = SaveMasterRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            discord_id = validation_serializer.data.get("discordUserId")
            discord_username = validation_serializer.data.get("discordUsername")
            domains_mastered = validation_serializer.data.get("domainsMastered")

            try:
                existing_master = DomainMaster.objects.filter(
                    master_id=discord_id
                ).get()
            except DomainMaster.DoesNotExist:
                existing_master = None

            try:
                discord_account = update_or_create_discord_account(
                    discord_id, discord_username, request.user
                )

                if existing_master is None:
                    DomainMaster.objects.create(
                        creator=request.user,
                        master=discord_account,
                        mastered_at=datetime.datetime.now(tz=datetime.timezone.utc),
                        domain_count=domains_mastered,
                    )
                else:
                    existing_master.domain_count = domains_mastered
                    existing_master.save()

            except Exception as ex:
                logger.error("Error attempting to save a Domain Challenge Master.")
                logger.error(ex)
                raise APIException(
                    "Error attempting to save a Domain Challenge Master."
                )
            serializer = SaveMasterResponseSerializer(
                {
                    "discordUserId": discord_id,
                    "newMaster": existing_master is None,
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
