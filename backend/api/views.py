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
    
    Milestone.objects.all().delete()
    VaccineFamily.objects.all().delete()
    VaccineDose.objects.all().delete()
    
    for idx, m in enumerate(data.get("milestones_order", [])):
        Milestone.objects.create(name=m["name"], target_days=m["target_days"], order_index=idx)
        
    for family in data.get("vaccines", []):
        f_id = family.get("id", str(uuid.uuid4()))
        VaccineFamily.objects.create(id_name=f_id, display_name=family.get("name", ""), description=family.get("description", ""))
        
        for dose in family.get("doses", []):
            base_id = dose.get("id", "dose")
            if base_id.endswith("_Old"): base_id = base_id[:-4]
            if base_id.endswith("_New"): base_id = base_id[:-4]
            
            milestone = dose["milestone"]
            d_id = f"{f_id}_{base_id}_{milestone}_{str(uuid.uuid4())[:8]}"
            rules = dose.get("rules", {})
            
            if "Old" in rules or "New" in rules:
                for protocol in ["Old", "New"]:
                    if protocol in rules:
                        p_rules = rules[protocol]
                        p_min = p_rules.get("min_age_days", 0)
                        p_offset = p_rules.get("offset_from_milestone_days", 0)
                        p_adv = {k:v for k,v in p_rules.items() if k not in ["min_age_days", "offset_from_milestone_days"]}
                        VaccineDose.objects.create(
                            id=f"{base_id}_{protocol}", family_id=f_id, milestone_name=milestone, 
                            pneumo_protocol=protocol, min_age_days=p_min, 
                            offset_days=p_offset, advanced_rules_json=json.dumps(p_adv)
                        )
            else:
                p_min = rules.get("min_age_days", 0)
                p_offset = rules.get("offset_from_milestone_days", 0)
                p_adv = {k:v for k,v in rules.items() if k not in ["min_age_days", "offset_from_milestone_days"]}
                VaccineDose.objects.create(
                    id=base_id, family_id=f_id, milestone_name=milestone, 
                    pneumo_protocol="All", min_age_days=p_min, 
                    offset_days=p_offset, advanced_rules_json=json.dumps(p_adv)
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
