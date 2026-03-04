from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, SegmentViewSet, ApplianceViewSet, CabinetViewSet, index

router = DefaultRouter()
router.register(r'projects', ProjectViewSet)
router.register(r'segments', SegmentViewSet)
router.register(r'appliances', ApplianceViewSet)
router.register(r'cabinets', CabinetViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('', index, name='index'),
]
