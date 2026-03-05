from django.urls import path
from .views import UserListAPIView, UserProfileUpdateAPIView, UserViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'gestion', UserViewSet, basename='user-gestion')

urlpatterns = [
    path('', UserListAPIView.as_view(), name='user-list'),
    path('<int:user_pk>/profile/', UserProfileUpdateAPIView.as_view(), name='user-profile-update'),
] + router.urls
