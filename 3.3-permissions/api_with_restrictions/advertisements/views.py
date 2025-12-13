from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from advertisements.filters import AdvertisementFilter
from advertisements.models import Advertisement, Favorite
from advertisements.permissions import IsOwnerOrReadOnly, IsAdminOrOwner
from advertisements.serializers import (
    AdvertisementSerializer,
    FavoriteSerializer
)


class AdvertisementViewSet(viewsets.ModelViewSet):
    """ViewSet для объявлений."""

    queryset = Advertisement.objects.all()
    serializer_class = AdvertisementSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = AdvertisementFilter
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get_queryset(self):
        """Фильтрация queryset в зависимости от пользователя."""
        queryset = super().get_queryset()
        user = self.request.user

        if not user.is_authenticated:
            return queryset.filter(status=Advertisement.OPEN)

        if user.is_staff:
            return queryset

        return queryset.filter(
            Q(status=Advertisement.OPEN) |
            Q(creator=user, status=Advertisement.DRAFT)
        )

    def get_permissions(self):
        """Получение прав для действий."""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsAdminOrOwner()]
        return [AllowAny()]

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """Добавить/удалить объявление из избранного."""
        advertisement = self.get_object()
        user = request.user

        if advertisement.creator == user:
            return Response(
                {'error': 'Нельзя добавить своё объявление в избранное'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':
            favorite, created = Favorite.objects.get_or_create(
                user=user,
                advertisement=advertisement
            )
            if created:
                serializer = FavoriteSerializer(favorite)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(
                {'error': 'Объявление уже в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )

        elif request.method == 'DELETE':
            deleted_count, _ = Favorite.objects.filter(
                user=user,
                advertisement=advertisement
            ).delete()

            if deleted_count > 0:
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'error': 'Объявление не найдено в избранном'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def favorites(self, request):
        """Получить список избранных объявлений пользователя."""
        favorites = Favorite.objects.filter(user=request.user)

        status_param = request.query_params.get('status')
        if status_param:
            favorites = favorites.filter(advertisement__status=status_param)

        created_at_after = request.query_params.get('created_at_after')
        created_at_before = request.query_params.get('created_at_before')

        if created_at_after:
            favorites = favorites.filter(advertisement__created_at__gte=created_at_after)
        if created_at_before:
            favorites = favorites.filter(advertisement__created_at__lte=created_at_before)

        page = self.paginate_queryset(favorites)
        if page is not None:
            serializer = FavoriteSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = FavoriteSerializer(favorites, many=True)
        return Response(serializer.data)