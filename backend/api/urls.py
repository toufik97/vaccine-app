from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (SettingViewSet, MilestoneViewSet, VaccineFamilyViewSet, 
                    VaccineDoseViewSet, upload_protocols, PatientViewSet, 
                    PatientVaccineViewSet, VisitViewSet, rename_vaccine, delete_vaccine_dose)

router = DefaultRouter()
router.register(r'settings', SettingViewSet)
router.register(r'milestones', MilestoneViewSet)
router.register(r'vaccine-families', VaccineFamilyViewSet)
router.register(r'vaccine-doses', VaccineDoseViewSet)
router.register(r'patients', PatientViewSet)
router.register(r'patient-vaccines', PatientVaccineViewSet)
router.register(r'visits', VisitViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('upload-protocols/', upload_protocols, name='upload-protocols'),
    path('rename-vaccine/', rename_vaccine, name='rename-vaccine'),
    path('delete-vaccine-dose/', delete_vaccine_dose, name='delete-vaccine-dose'),
]
