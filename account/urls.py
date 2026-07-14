from django.urls import path

from account.views import (
    APIKeyListGenerateAPI,
    UserListAPI,
    UserLoginAPI,
    UserRegisterAPI,
    VendorListAPI,
)

urlpatterns = [
    path("register/", UserRegisterAPI.as_view(), name="register"),
    path("login/", UserLoginAPI.as_view(), name="login"),
    path("api-keys/", APIKeyListGenerateAPI.as_view(), name="api-keys"),
    path("users/", UserListAPI.as_view(), name="user-list"),
    path("vendors/", VendorListAPI.as_view(), name="vendor-list"),
]
