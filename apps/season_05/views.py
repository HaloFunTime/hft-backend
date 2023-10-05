import datetime
import logging
import random

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.discord.utils import update_or_create_discord_account
from apps.season_05.models import DomainChallengeTeamAssignment, DomainMaster
from apps.season_05.serializers import (
    JoinChallengeRequestSerializer,
    JoinChallengeResponseSerializer,
    SaveMasterRequestSerializer,
    SaveMasterResponseSerializer,
)
from config.serializers import StandardErrorSerializer

logger = logging.getLogger(__name__)


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
