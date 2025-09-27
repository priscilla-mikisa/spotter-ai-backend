from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TripViewSet, DriverViewSet, CarrierViewSet

app_name = 'trips'

router = DefaultRouter()
router.register(r'trips', TripViewSet)
router.register(r'drivers', DriverViewSet)
router.register(r'carriers', CarrierViewSet)

urlpatterns = [
    path('', include(router.urls)),
]