from django.urls import path

from accounts.views import account


app_name = "accounts"
urlpatterns = [
    path("register/", account.register, name="register"),
    path("login/", account.login, name="login"),
    path("refresh/", account.refresh, name="refresh"),
    path("logout/", account.logout, name="logout"),
    path("me/", account.me, name="me"),
    path("password/", account.password, name="password"),
]
