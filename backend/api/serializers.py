from rest_framework import serializers
from .models import Setting, VaccineFamily, Milestone, VaccineDose, Patient, PatientVaccine, Visit
import json

class SettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setting
        fields = '__all__'

class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = '__all__'

class VaccineDoseSerializer(serializers.ModelSerializer):
    # We parse the advanced JSON rules so the API consumer gets a clean dictionary
    # rather than an escaped string.
    advanced_rules = serializers.SerializerMethodField()
    
    class Meta:
        model = VaccineDose
        fields = ['id', 'family_id', 'milestone_name', 'pneumo_protocol', 'min_age_days', 'offset_days', 'advanced_rules']

    def get_advanced_rules(self, obj):
        if obj.advanced_rules_json:
            try:
                return json.loads(obj.advanced_rules_json)
            except:
                return {}
        return {}

class VaccineFamilySerializer(serializers.ModelSerializer):
    doses = serializers.SerializerMethodField()

    class Meta:
        model = VaccineFamily
        fields = ['id_name', 'display_name', 'description', 'doses']

    def get_doses(self, obj):
        # Nested serialization to emulate the structure of the original protocols.json
        doses = VaccineDose.objects.filter(family_id=obj.id_name)
        return VaccineDoseSerializer(doses, many=True).data

class PatientVaccineSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientVaccine
        fields = '__all__'

class VisitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visit
        fields = '__all__'

class PatientSerializer(serializers.ModelSerializer):
    vaccines = PatientVaccineSerializer(many=True, read_only=True)
    visits = VisitSerializer(many=True, read_only=True)

    class Meta:
        model = Patient
        fields = '__all__'
