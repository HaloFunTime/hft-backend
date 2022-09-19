import logging
import random

from django.db import OperationalError, connections
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import PingResponseSerializer

logger = logging.getLogger(__name__)


class Ping(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        responses={
            200: PingResponseSerializer,
            500: PingResponseSerializer,
        }
    )
    def get(self, request):
        """
        Evaluates API availability by testing a database connection.
        """
        logger.info("Called ping function")
        open_connections = connections.all()
        if not open_connections:
            logger.debug("Ping failure - database connectivity error")
            return Response(
                data={"detail": "Database connectivity error", "success": False},
                status=500,
            )
        connection = random.choice(open_connections)
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            health_check = cursor.fetchone()[0]
            if health_check != 1:
                logger.debug("Ping failure - health check error")
                return Response(
                    data={"detail": "Health check error", "success": False}, status=500
                )
        except OperationalError:
            logger.debug("Ping failure - operational error")
            return Response(
                data={"detail": "Operational error", "success": False}, status=500
            )
        logger.info("Successful ping!")
        return Response(
            data={"detail": "The HaloFunTime API is available", "success": True},
            status=200,
        )
