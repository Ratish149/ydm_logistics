from django.contrib.auth import get_user_model

User = get_user_model()


def change_user_password(user, new_password: str):
    """
    Updates the password for the specified user and saves it.
    """
    user.set_password(new_password)
    user.save(update_fields=["password"])
    return user
