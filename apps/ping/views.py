import logging
import random

from django.db import OperationalError, connections
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class Ping(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        """
        Health check - SELECT 1 on a current database connection
        """
        logger.info("Called ping function...")
        open_connections = connections.all()
        if not open_connections:
            logger.debug("Failed to get a database connection")
            return Response(status=500)
        connection = random.choice(open_connections)
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            health_check = cursor.fetchone()[0]
            if health_check != 1:
                logger.debug("Health check failed")
                return Response(status=500)
        except OperationalError:
            logger.exception("Ping failure")
            return Response(status=500)
        logger.info("Successful ping!")
        return Response(
            {"ping": "The HaloFunTime API is responding as expected."}, status=200
        )
