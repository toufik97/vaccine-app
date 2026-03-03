from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SettingViewSet, MilestoneViewSet, VaccineFamilyViewSet, VaccineDoseViewSet, upload_protocols

router = DefaultRouter()
router.register(r'settings', SettingViewSet)
router.register(r'milestones', MilestoneViewSet)
router.register(r'vaccine-families', VaccineFamilyViewSet)
router.register(r'vaccine-doses', VaccineDoseViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('upload-protocols/', upload_protocols, name='upload-protocols'),
]
