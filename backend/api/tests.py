from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import Patient, PatientVaccine

class VaccineApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.patient = Patient.objects.create(
            id_label="TEST_123",
            name="John Doe",
            dob="2020-01-01",
            sexe=0,
            pneumo_mode="Old"
        )
        self.vax = PatientVaccine.objects.create(
            patient=self.patient,
            milestone_name="Naissance",
            vaccine_name="BCG",
            status="Pending"
        )

    def test_rename_vaccine(self):
        url = reverse('rename-vaccine')
        response = self.client.post(url, {"old_name": "BCG", "new_name": "BCG_MODIFIED"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.vax.refresh_from_db()
        self.assertEqual(self.vax.vaccine_name, "BCG_MODIFIED")

    def test_delete_vaccine_dose(self):
        url = reverse('delete-vaccine-dose')
        response = self.client.post(url, {"vax_name": "BCG"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertFalse(PatientVaccine.objects.filter(vaccine_name="BCG").exists())

    def test_patient_api_includes_nested_vaccines(self):
        response = self.client.get('/api/patients/TEST_123/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['name'], "John Doe")
        self.assertEqual(len(data['vaccines']), 1)
        self.assertEqual(data['vaccines'][0]['vaccine_name'], "BCG")
