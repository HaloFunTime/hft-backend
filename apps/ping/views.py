import logging
import random

from django.db import OperationalError, connections
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.serializers import CharField
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class Ping(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        responses={
            "200": inline_serializer(
                name="PingSuccessResponse", fields={"ping": CharField()}
            ),
            "500": inline_serializer(
                name="PingFailureResponse", fields={"ping": CharField()}
            ),
        }
    )
    def get(self, request):
        """
        Evaluates API health by testing a database connection.
        """
        logger.info("Called ping function...")
        open_connections = connections.all()
        if not open_connections:
            logger.debug("Ping failure - database connectivity error")
            return Response(
                data={"ping": "Failure (database connectivity error)."}, status=500
            )
        connection = random.choice(open_connections)
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            health_check = cursor.fetchone()[0]
            if health_check != 1:
                logger.debug("Ping failure - health check error")
                return Response(
                    data={"ping": "Failure (health check error)."}, status=500
                )
        except OperationalError:
            logger.exception("Ping failure - operational error")
            return Response(data={"ping": "Failure (operational error)."}, status=500)
        logger.info("Successful ping!")
        return Response(
            data={"ping": "Success (the HaloFunTime API is responding as expected)."},
            status=200,
        )
