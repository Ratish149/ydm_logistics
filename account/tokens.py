from rest_framework_simplejwt.tokens import RefreshToken


class UserRefreshToken(RefreshToken):
    """
    Custom JWT token that embeds user details in the payload.
    These claims are encoded inside the token — only visible after decoding.
    """

    @classmethod
    def for_user(cls, user):
        token = super().for_user(user)

        # Embed user details — readable only by decoding the JWT
        token["username"] = user.username
        token["email"] = user.email
        token["first_name"] = user.first_name
        token["last_name"] = user.last_name
        token["phone_number"] = user.phone_number or ""
        token["address"] = user.address or ""

        return token
