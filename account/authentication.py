from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from account.models import APIKey


class APIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        api_key = request.headers.get("X-API-KEY")
        if not api_key:
            auth_header = request.headers.get("Authorization")
            if auth_header:
                parts = auth_header.split()
                if len(parts) == 2 and parts[0].lower() == "api-key":
                    api_key = parts[1]

        if not api_key:
            return None

        key_obj = (
            APIKey.objects.select_related("user")
            .filter(key=api_key, is_active=True, user__is_active=True)
            .first()
        )

        if not key_obj:
            raise AuthenticationFailed("Invalid API Key.")

        if key_obj.expires_at and key_obj.expires_at < timezone.now():
            raise AuthenticationFailed("API Key has expired.")

        return (key_obj.user, key_obj)
