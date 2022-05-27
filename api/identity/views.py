from rest_framework import generics, permissions
from api.default.permissions import IsOwnerOrReadOnly
from .models import Identity
from .serializers import IdentitySerializer


class IdentityList(generics.ListCreateAPIView):
    queryset = Identity.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    serializer_class = IdentitySerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class IdentityDetail(generics.RetrieveUpdateDestroyAPIView):
    lookup_field = "id"
    queryset = Identity.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    serializer_class = IdentitySerializer
