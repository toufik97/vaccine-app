from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction
from .models import Setting, VaccineFamily, Milestone, VaccineDose
from .serializers import SettingSerializer, VaccineFamilySerializer, MilestoneSerializer, VaccineDoseSerializer
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
