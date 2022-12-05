from rest_framework.routers import SimpleRouter

from tickets import views


router = SimpleRouter()
router.register(r'tickets', viewset=views.TicketsViewSet)
router.register(r'arrival_points', viewset=views.ArrivalPointViewSet)
router.register(r'routes', viewset=views.RouteViewSet)
router.register(r'orders', viewset=views.OrderViewSet)
router.register(r'cities', viewset=views.CityViewSet)
router.register(r'carriage_types', viewset=views.CarriageTypeViewSet)
router.register(r'carriages', viewset=views.CarriageViewSet)


urlpatterns = router.urls
