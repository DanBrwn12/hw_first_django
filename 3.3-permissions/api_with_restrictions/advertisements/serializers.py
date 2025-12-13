from django.contrib.auth.models import User
from rest_framework import serializers

from advertisements.models import Advertisement, AdvertisementStatusChoices, Favorite


class UserSerializer(serializers.ModelSerializer):
    """Serializer для пользователя."""

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'is_staff')


class AdvertisementSerializer(serializers.ModelSerializer):
    """Serializer для объявления."""
    creator = UserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Advertisement
        fields = ('id', 'title', 'description', 'creator',
                  'status', 'created_at', 'updated_at', 'is_favorited')
        read_only_fields = ('creator', 'created_at', 'updated_at', 'is_favorited')

    def get_is_favorited(self, obj):
        """Проверяет, добавил ли текущий пользователь объявление в избранное."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(
                user=request.user,
                advertisement=obj
            ).exists()
        return False

    def create(self, validated_data):
        """Метод для создания."""
        validated_data["creator"] = self.context["request"].user

        if validated_data.get('status') == AdvertisementStatusChoices.OPEN:
            user = self.context["request"].user
            open_ads_count = Advertisement.objects.filter(
                creator=user,
                status=AdvertisementStatusChoices.OPEN,
            ).count()

            if open_ads_count >= 10:
                raise serializers.ValidationError(
                    "Нельзя иметь больше 10 открытых объявлений"
                )

        return super().create(validated_data)

    def validate(self, data):
        """Метод для валидации. Вызывается при создании и обновлении."""
        user = self.context["request"].user

        if self.instance and data.get('status') == AdvertisementStatusChoices.OPEN:
            if self.instance.status != AdvertisementStatusChoices.OPEN:
                open_ads_count = Advertisement.objects.filter(
                    creator=user,
                    status=AdvertisementStatusChoices.OPEN,
                ).count()

                if open_ads_count >= 10:
                    raise serializers.ValidationError(
                        "Нельзя иметь больше 10 открытых объявлений"
                    )

        return data


class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer для избранных объявлений."""
    advertisement = AdvertisementSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ('id', 'advertisement', 'created_at')
        read_only_fields = ('user', 'advertisement', 'created_at')