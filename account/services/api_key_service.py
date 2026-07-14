from django.contrib.auth import get_user_model
from rest_framework_api_key.crypto import KeyGenerator

from account.models import APIKey

User = get_user_model()


def generate_key_for_obj(api_key_obj: APIKey) -> str:
    """
    Generates a raw key using djangorestframework-api-key's KeyGenerator
    and sets it to the key field of the object.
    Key format: ydm_<prefix>.<secret>
    """
    key, _, _ = KeyGenerator().generate()
    raw_key = f"ydm_{key}"
    api_key_obj.key = raw_key
    return raw_key


def create_api_key(user, expires_at=None) -> tuple[APIKey, str]:
    api_key = APIKey(user=user, expires_at=expires_at)
    raw_key = generate_key_for_obj(api_key)
    api_key.save()
    return api_key, raw_key
