from core.who_zscore import WhoZScoreCalculator
from core.scheduler import Scheduler
from core.api_client import ApiClient
from datetime import datetime, timedelta
from core.enums import VaccineStatus
import uuid

class VaxEngine:
    """
    Facade class that integrates the HTTP ApiClient, Scheduler, and WhoZScoreCalculator.
    Translates JSON API data into legacy tuples to maintain UI compatibility.
    """
    def __init__(self):
        self.api = ApiClient()
        self.zscore_calc = WhoZScoreCalculator()
        self.scheduler = Scheduler(self.api)
        self.load_config()

    def load_config(self):
        settings_dict = self.api.get_settings()
        if settings_dict and "config" in settings_dict:
            self.config = settings_dict["config"]
        else:
            self.config = {}
            self.save_config()

    def save_config(self):
        self.api.save_settings({"config": self.config})
        
    def load_protocols(self):
        """ Reloads the protocols from json and sets them. """
        self.scheduler.load_protocols()
        
    @property
    def milestones(self):
        return self.scheduler.milestones

    @property
    def dependencies(self):
        return self.scheduler.dependencies
        
    # --- HELPER TRANSLATORS ---
    def _patient_dict_to_tuple(self, p):
        if not p: return None
        sexe_val = p.get('sexe', 0)
        sexe_str = "F" if sexe_val == 1 else "M"
        return (
            p.get('id_label'), p.get('name'), p.get('dob'), sexe_str,
            p.get('address', ''), p.get('parent_name', ''), p.get('phone', ''),
            p.get('allergies', ''), p.get('email', '')
        )

    def _vax_dict_to_tuple(self, v):
        return (
            v.get('milestone_name'), 
            v.get('vaccine_name'), 
            v.get('due_date') or "",
            v.get('status'), 
            v.get('given_date') or "", 
            v.get('observation') or ""
        )
        
    def _vax_list_to_records_dict(self, vaccines):
        records = {}
        for v in vaccines:
            records[v['vaccine_name']] = {
                "id": v['id'], # Track API ID for patching
                "status": v['status'], 
                "date_given": v['given_date'], 
                "due_date": v['due_date'], 
                "observations": v['observation'] or ""
            }
        return records

    def _visit_dict_to_tuple(self, v):
        return (v['id'], v['patient'], v['visit_date'] or "", v['weight'], v['height'], v['imc'])

    # --- CORE METHODS ---
    def get_patient(self, p_id):
        p = self.api.get_patient(p_id)
        return self._patient_dict_to_tuple(p) if p else None

    def get_all_patients(self):
        patients = self.api.get_all_patients()
        return [self._patient_dict_to_tuple(p) for p in patients]

    def search_patients(self, query):
        patients = self.get_all_patients()
        if not query: return patients
        query = query.lower()
        return [p for p in patients if query in str(p[0]).lower() or query in str(p[1]).lower()]

    def get_patient_dob_and_records(self, p_id):
        p = self.api.get_patient(p_id)
        if not p: return None, {}
        return p['dob'], self._vax_list_to_records_dict(p.get('vaccines', []))

    def get_records(self, p_id):
        p = self.api.get_patient(p_id)
        if not p: return []
        return [self._vax_dict_to_tuple(v) for v in p.get('vaccines', [])]

    # --- MUTATION METHODS ---
    def register_child(self, name, dob_obj, sexe, address, parent_name="", phone="", allergies="", email="", center_schedule={}):
        import uuid
        new_id = str(uuid.uuid4())[:8].upper()
        dob_str = dob_obj.strftime("%Y-%m-%d")
        
        patient_data = {
            "id_label": new_id,
            "name": name,
            "dob": dob_str,
            "sexe": sexe,
            "address": address,
            "parent_name": parent_name,
            "phone": phone,
            "allergies": allergies,
            "email": email
        }
        self.api.create_patient(patient_data)
        
        for milestone, days, vaccines in self.scheduler.milestones:
            due = (dob_obj + timedelta(days=days)).strftime("%Y-%m-%d")
            for vax in vaccines:
                self.api.create_patient_vaccine({
                    "patient": new_id,
                    "milestone_name": milestone,
                    "vaccine_name": vax,
                    "due_date": due,
                    "status": VaccineStatus.PENDING.value,
                    "given_date": "",
                    "observation": ""
                })
                
        self.recalculate_schedule(new_id, center_schedule)
        return new_id

    def update_patient(self, p_id, name, dob_str, sexe, address, parent_name, phone, allergies, email, center_schedule={}):
        data = {
            "name": name,
            "dob": dob_str,
            "sexe": sexe,
            "address": address,
            "parent_name": parent_name,
            "phone": phone,
            "allergies": allergies,
            "email": email
        }
        self.api.patch_patient(p_id, data)
        self.recalculate_schedule(p_id, center_schedule)
        
    def delete_patient(self, p_id):
        self.api.delete_patient(p_id)

    # --- VACCINE STATUS UPDATES ---
    def update_vax_status(self, p_id, milestone, vax_name, status, date_given, observation="", 
                          lot_number=None, expiration_date=None, diluent_confirmed=None, injection_site=None):
        p = self.api.get_patient(p_id)
        if not p: return
        
        # Find the specific vaccine record ID to patch
        for v in p.get("vaccines", []):
            if v["vaccine_name"] == vax_name and v["milestone_name"] == milestone:
                payload = {
                    "status": status,
                    "given_date": date_given if date_given else "",
                    "observation": observation
                }
                if lot_number is not None: payload["lot_number"] = lot_number
                if expiration_date is not None: payload["expiration_date"] = expiration_date
                if diluent_confirmed is not None: payload["diluent_confirmed"] = diluent_confirmed
                if injection_site is not None: payload["injection_site"] = injection_site
                
                self.api.patch_patient_vaccine(v["id"], payload)
                break

    def update_milestone_status(self, p_id, milestone, status, date_given):
        for v in self.scheduler.get_core_vaccines(milestone):
            self.update_vax_status(p_id, milestone, v, status, date_given)

    def mark_rupture(self, p_id, milestone, vax_name, date_str):
        self.update_vax_status(p_id, milestone, vax_name, VaccineStatus.RUPTURE.value, date_str)

    def mark_milestone_rupture(self, p_id, milestone, date_str):
        self.update_milestone_status(p_id, milestone, VaccineStatus.RUPTURE.value, date_str)

    def mark_maladie(self, p_id, milestone, vax_name, date_str):
        self.update_vax_status(p_id, milestone, vax_name, VaccineStatus.MALADIE.value, date_str)

    def mark_milestone_maladie(self, p_id, milestone, date_str):
        self.update_milestone_status(p_id, milestone, VaccineStatus.MALADIE.value, date_str)

    def cancel_vaccine(self, p_id, milestone, vax_name):
        self.update_vax_status(p_id, milestone, vax_name, VaccineStatus.PENDING.value, "")

    def cancel_milestone(self, p_id, milestone):
        self.update_milestone_status(p_id, milestone, VaccineStatus.PENDING.value, "")

    def get_eipv_url(self, p_id, vax_name):
        import urllib.parse
        p = self.api.get_patient(p_id)
        if not p: return ""
        
        v_record = None
        for v in p.get("vaccines", []):
            if v["vaccine_name"] == vax_name:
                v_record = v
                break
                
        if not v_record: return ""
        
        base_url = "https://vigiflow-eforms.who-umc.org/ma/vaccin"
        params = {
            "patient_name": p.get("name", ""),
            "patient_id": p.get("id_label", ""),
            "vaccine": vax_name,
            "lot_number": v_record.get("lot_number", ""),
            "date_given": v_record.get("given_date", "")
        }
        
        # Mark as notified in DB asynchronously or sync depending on implementation
        self.api.patch_patient_vaccine(v_record["id"], {"eipv_notified": True})
        
        encoded = urllib.parse.urlencode({k: v for k, v in params.items() if v})
        return f"{base_url}?{encoded}"

    # --- SCHEDULING & CALCULATIONS ---
    def get_visit_zscores(self, p_id, visit_date_str, weight, height, imc):
        p = self.api.get_patient(p_id)
        if not p: return None, None, None
        return self.zscore_calc.get_visit_zscores(p['dob'], p['sexe'], visit_date_str, weight, height, imc)

    def recalculate_schedule(self, p_id, center_schedule):
        dob_str, records_dict = self.get_patient_dob_and_records(p_id)
        if not dob_str: return
            
        # Detect if we should use rattling/catch-up logic (e.g. no proof)
        # Note: in a real environment, no_proof would be stored on Patient.
        # We can simulate this by checking if they are entirely unvaccinated/no history
        has_history = any(
            v["status"] in [VaccineStatus.DONE.value, VaccineStatus.EXTERNE.value] 
            for v in records_dict.values()
        )
        no_proof_flag = False
        if not has_history and (datetime.now() - datetime.strptime(dob_str, "%Y-%m-%d")).days > 365:
            # Simple heuristic or config flag
            no_proof_flag = True
            
        expected_vaxes = self.scheduler.generate_expected_vaxes(dob_str, no_proof=no_proof_flag)
        
        existing_vaxes = set(records_dict.keys())
        expected_vax_names = {v[1] for v in expected_vaxes}
        
        # Insert missing
        for milestone, vax_name in expected_vaxes:
            if vax_name not in existing_vaxes:
                self.api.create_patient_vaccine({
                    "patient": p_id,
                    "milestone_name": milestone,
                    "vaccine_name": vax_name,
                    "due_date": None,
                    "status": VaccineStatus.PENDING.value,
                    "given_date": "",
                    "observation": ""
                })
                # Re-fetch is safer, or just inject fake ID for next step
                records_dict[vax_name] = {"id": -1, "status": VaccineStatus.PENDING.value, "date_given": "", "due_date": "", "observations": ""}
                
        # Delete unused PENDING
        for vax, data in list(records_dict.items()):
            if vax not in expected_vax_names and data["status"] == VaccineStatus.PENDING.value:
                if data["id"] != -1: # It was a real API id
                    self.api.delete_patient_vaccine(data["id"])
                
        # Refresh real API records after additions/deletions before calculating updates
        dob_str, records_dict = self.get_patient_dob_and_records(p_id)
        updates = self.scheduler.calculate_updates(dob_str, records_dict, center_schedule)
        
        # Bulk update via loop (Okay for local API)
        for new_due, vax_name in updates:
            if vax_name in records_dict:
                vax_id = records_dict[vax_name]["id"]
                if vax_id != -1:
                    self.api.patch_patient_vaccine(vax_id, {"due_date": new_due})

    def recalculate_all_schedules(self, center_schedule):
        for p in self.get_all_patients():
            self.recalculate_schedule(p[0], center_schedule)

    def validate_vaccine_date(self, p_id, vax_name, input_date):
        dob_str, records_dict = self.get_patient_dob_and_records(p_id)
        if not dob_str: return None
        return self.scheduler.validate_vaccine_input(dob_str, records_dict, vax_name, input_date=input_date)

    # --- VISITS ---
    def add_visit(self, p_id, date_str, weight, height, imc):
        self.api.create_visit({
            "patient": p_id,
            "visit_date": date_str,
            "weight": weight,
            "height": height,
            "imc": imc
        })

    def get_visits(self, p_id):
        p = self.api.get_patient(p_id)
        if not p: return []
        return [self._visit_dict_to_tuple(v) for v in p.get('visits', [])]

    # --- STATS / ANALYTICS ---
    def get_daily_stats(self, date_str):
        # We process this client side from all patients.
        # In a real heavy app, this would be a custom DRF endpoint.
        patients = self.api.get_all_patients()
        total_doses = 0
        vaccine_counts = {}
        for p in patients:
            for v in p.get("vaccines", []):
                if v.get("status") in ["Done", "Externe"] and v.get("given_date") == date_str:
                    total_doses += 1
                    name = v.get("vaccine_name")
                    vaccine_counts[name] = vaccine_counts.get(name, 0) + 1
        return total_doses, vaccine_counts

    def get_monthly_stats(self, year_month_str):
        patients = self.api.get_all_patients()
        total_doses = 0
        vaccine_counts = {}
        for p in patients:
            for v in p.get("vaccines", []):
                given = v.get("given_date")
                if v.get("status") in ["Done", "Externe"] and given and given.startswith(year_month_str):
                    total_doses += 1
                    name = v.get("vaccine_name")
                    vaccine_counts[name] = vaccine_counts.get(name, 0) + 1
        return total_doses, vaccine_counts

    # --- SEARCH ---
    def search_by_vaccine_date(self, date_str):
        # Scan and return (patient tuple, (vax tuple))
        results = []
        patients = self.api.get_all_patients()
        for p in patients:
            for v in p.get("vaccines", []):
                if v.get("given_date") == date_str:
                    results.append((self._patient_dict_to_tuple(p), self._vax_dict_to_tuple(v)))
        return results

    # --- BULK PROTOCOL ACTIONS ---
    def rename_vaccine_in_db(self, old_vax_name, new_vax_name):
        self.api.rename_vaccine(old_vax_name, new_vax_name)

    def delete_vaccine_dose_in_db(self, vax_name):
        self.api.delete_vaccine_dose(vax_name)
