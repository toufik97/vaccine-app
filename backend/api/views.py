from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction
from .models import Setting, VaccineFamily, Milestone, VaccineDose, Patient, PatientVaccine, Visit
from .serializers import SettingSerializer, VaccineFamilySerializer, MilestoneSerializer, VaccineDoseSerializer, PatientSerializer, PatientVaccineSerializer, VisitSerializer
import json
import uuid

class SettingViewSet(viewsets.ModelViewSet):
    queryset = Setting.objects.all()
    serializer_class = SettingSerializer

class MilestoneViewSet(viewsets.ModelViewSet):
    queryset = Milestone.objects.all()
    serializer_class = MilestoneSerializer

class VaccineFamilyViewSet(viewsets.ModelViewSet):
    queryset = VaccineFamily.objects.all()
    serializer_class = VaccineFamilySerializer

class VaccineDoseViewSet(viewsets.ModelViewSet):
    queryset = VaccineDose.objects.all()
    serializer_class = VaccineDoseSerializer

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    lookup_value_regex = r'[^.]+' # Allows slashes in primary key

class PatientVaccineViewSet(viewsets.ModelViewSet):
    queryset = PatientVaccine.objects.all()
    serializer_class = PatientVaccineSerializer

class VisitViewSet(viewsets.ModelViewSet):
    queryset = Visit.objects.all()
    serializer_class = VisitSerializer

@api_view(['POST'])
@transaction.atomic
def upload_protocols(request):
    data = request.data
    
    # Cascade delete will handle related objects
    Milestone.objects.all().delete()
    VaccineFamily.objects.all().delete()
    
    milestone_map = {}
    for idx, m in enumerate(data.get("milestones_order", [])):
        milestone = Milestone.objects.create(
            name=m["name"], 
            target_days=m["target_days"], 
            order_index=idx
        )
        milestone_map[m["name"]] = milestone
        
    for family_data in data.get("vaccines", []):
        f_id = family_data.get("id", str(uuid.uuid4()))
        family = VaccineFamily.objects.create(
            id_name=f_id, 
            display_name=family_data.get("name", ""), 
            description=family_data.get("description", "")
        )
        
        for dose in family_data.get("doses", []):
            base_id = dose.get("id", "dose")
            milestone_name = dose["milestone"]
            milestone_obj = milestone_map.get(milestone_name)
            
            if not milestone_obj:
                continue # Or handle missing milestones
                
            rules = dose.get("rules", {})
            
            if "Old" in rules or "New" in rules:
                for protocol in ["Old", "New"]:
                    if protocol in rules:
                        p_rules = rules[protocol]
                        p_min = p_rules.get("min_age_days", 0)
                        p_offset = p_rules.get("offset_from_milestone_days", 0)
                        p_adv = {k:v for k,v in p_rules.items() if k not in ["min_age_days", "offset_from_milestone_days", "administration_route", "default_injection_site", "vial_lifespan_days"]}
                        
                        pk_id = f"{base_id}_{protocol}" if protocol in ["Old", "New"] else base_id
                        
                        VaccineDose.objects.create(
                            id=pk_id, 
                            family=family, 
                            milestone=milestone_obj, 
                            pneumo_protocol=protocol, 
                            min_age_days=p_min, 
                            offset_days=p_offset, 
                            administration_route=p_rules.get("administration_route", ""),
                            default_injection_site=p_rules.get("default_injection_site", ""),
                            vial_lifespan_days=p_rules.get("vial_lifespan_days", 0),
                            advanced_rules_json=json.dumps(p_adv)
                        )
            else:
                p_min = rules.get("min_age_days", 0)
                p_offset = rules.get("offset_from_milestone_days", 0)
                p_adv = {k:v for k,v in rules.items() if k not in ["min_age_days", "offset_from_milestone_days", "administration_route", "default_injection_site", "vial_lifespan_days"]}
                
                pk_id = base_id
                
                VaccineDose.objects.create(
                    id=pk_id, 
                    family=family, 
                    milestone=milestone_obj, 
                    pneumo_protocol="All", 
                    min_age_days=p_min, 
                    offset_days=p_offset, 
                    administration_route=rules.get("administration_route", ""),
                    default_injection_site=rules.get("default_injection_site", ""),
                    vial_lifespan_days=rules.get("vial_lifespan_days", 0),
                    advanced_rules_json=json.dumps(p_adv)
                )
                
    return Response({"status": "success"})


@api_view(['POST'])
@transaction.atomic
def rename_vaccine(request):
    old_name = request.data.get("old_name")
    new_name = request.data.get("new_name")
    if old_name and new_name:
        PatientVaccine.objects.filter(vaccine_name=old_name).update(vaccine_name=new_name)
        return Response({"status": "success", "message": f"Renamed {old_name} to {new_name}"})
    return Response({"error": "Missing old_name or new_name"}, status=400)


@api_view(['POST'])
@transaction.atomic
def delete_vaccine_dose(request):
    vax_name = request.data.get("vax_name")
    if vax_name:
        # According to business rules, we only cascade delete vaccines that are STILL PENDING. 
        # Done/Externe doses are preserved in the medical record cache.
        PatientVaccine.objects.filter(vaccine_name=vax_name, status="Pending").delete()
        return Response({"status": "success", "message": f"Deleted PENDING records for {vax_name}"})
    return Response({"error": "Missing vax_name"}, status=400)
