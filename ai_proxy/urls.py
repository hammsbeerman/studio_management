from django.urls import path

from .views import proxy

app_name = "ai_proxy"

urlpatterns = [
    path("ui/", proxy, {"subpath": "ui/"}, name="proxy_root"),
    path("<path:subpath>", proxy, name="proxy"),
]