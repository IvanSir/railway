from django.urls import path
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from users import views


router = SimpleRouter()
router.register(r'accounts', viewset=views.UserViewSet)
router.register(r'discount_types', viewset=views.DiscountTypeViewSet)
router.register(r'discounts', viewset=views.DiscountViewSet)


urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
urlpatterns += router.urls
