from db.database import Database
from core.who_zscore import WhoZScoreCalculator
from core.scheduler import Scheduler
from core.api_client import ApiClient
from datetime import datetime, timedelta
from core.enums import PneumoProtocol, VaccineStatus

class VaxEngine:
    """
    Facade class that integrates Database, Scheduler, and WhoZScoreCalculator
    to behave largely exactly as the old monolithic logic.py VaxEngine.
    """
    def __init__(self):
        self.db = Database('vax_pro.db')
        self.api = ApiClient()
        self.zscore_calc = WhoZScoreCalculator()
        self.scheduler = Scheduler(self.api)
        self.load_config()

    def load_config(self):
        settings_dict = self.api.get_settings()
        if settings_dict and "config" in settings_dict:
            self.config = settings_dict["config"]
        else:
            self.config = {"pneumo_mode": PneumoProtocol.OLD.value}
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
        
    def get_visit_zscores(self, p_id, visit_date_str, weight, height, imc):
        patient = self.db.get_patient(p_id)
        if not patient: return None, None, None
        
        # patient tuple: (id_label, name, dob, sexe, address, ...)
        dob_str = patient[2]
        sexe = patient[3]
        
        return self.zscore_calc.get_visit_zscores(dob_str, sexe, visit_date_str, weight, height, imc)
        
    def recalculate_schedule(self, p_id, center_schedule):
        dob_str, records_dict = self.db.get_patient_dob_and_records(p_id)
        if not dob_str:
            return
            
        pneumo_mode = self.db.get_patient_pneumo_mode(p_id)
        
        # Sync DB records with expected vaccines for this pneumo_mode
        expected_vaxes = []
        for milestone, target, vaxes in self.scheduler.milestones:
            for vax in vaxes:
                if vax == "Pneumo3_NewOnly" and pneumo_mode == PneumoProtocol.OLD.value:
                    continue
                expected_vaxes.append((milestone, vax))
                
        existing_vaxes = set(records_dict.keys())
        expected_vax_names = {v[1] for v in expected_vaxes}
        
        # Insert missing (e.g., Pneumo3_NewOnly if switched to New)
        for milestone, vax in expected_vaxes:
            if vax not in existing_vaxes:
                self.db.add_patient_vaccine_record(p_id, milestone, vax)
                records_dict[vax] = {"status": VaccineStatus.PENDING.value, "date_given": None, "due_date": "", "observations": ""}
                
        # Delete unused PENDING (e.g. Pneumo3_NewOnly if switched to Old)
        for vax, data in records_dict.items():
            if vax not in expected_vax_names and data["status"] == VaccineStatus.PENDING.value:
                self.db.delete_patient_vaccine_record_if_pending(p_id, vax)
                
        # Refresh records after sync
        dob_str, records_dict = self.db.get_patient_dob_and_records(p_id)
        
        updates = self.scheduler.calculate_updates(dob_str, records_dict, center_schedule, pneumo_mode)
        self.db.update_records_due_dates(p_id, updates)

    def recalculate_all_schedules(self, center_schedule):
        for p in self.db.get_all_patients():
            self.recalculate_schedule(p[0], center_schedule)

    def register_child(self, name, dob_obj, sexe, address, parent_name="", phone="", allergies="", email="", pneumo_mode="Old", center_schedule={}):
        new_id = self.db.generate_id()
        dob_str = dob_obj.strftime("%Y-%m-%d")
        
        initial_records = []
        for milestone, days, vaccines in self.scheduler.milestones:
            due = (dob_obj + timedelta(days=days)).strftime("%Y-%m-%d")
            for vax in vaccines:
                initial_records.append((milestone, vax, due))
                
        self.db.register_child(new_id, name, dob_str, sexe, address, parent_name, phone, allergies, email, pneumo_mode, initial_records)
        self.recalculate_schedule(new_id, center_schedule)
        return new_id

    def search_patients(self, query):
        return self.db.search_patients(query)

    def search_by_vaccine_date(self, date_str):
        return self.db.search_by_vaccine_date(date_str)

    def get_records(self, p_id):
        return self.db.get_records(p_id)

    def update_vax_status(self, p_id, milestone, vax_name, status, date_given, observation=""):
        self.db.update_vax_status(p_id, milestone, vax_name, status, date_given, observation)

    def update_milestone_status(self, p_id, milestone, status, date_given):
        pneumo_mode = self.config.get("pneumo_mode", PneumoProtocol.OLD.value)
        for v in self.scheduler.get_core_vaccines(milestone, pneumo_mode):
            self.db.update_vax_status(p_id, milestone, v, status, date_given)

    def mark_rupture(self, p_id, milestone, vax_name, date_str):
        self.db.mark_rupture(p_id, milestone, vax_name, date_str)

    def mark_milestone_rupture(self, p_id, milestone, date_str):
        pneumo_mode = self.config.get("pneumo_mode", PneumoProtocol.OLD.value)
        for v in self.scheduler.get_core_vaccines(milestone, pneumo_mode):
            self.db.mark_rupture(p_id, milestone, v, date_str)

    def mark_maladie(self, p_id, milestone, vax_name, date_str):
        self.db.mark_maladie(p_id, milestone, vax_name, date_str)

    def mark_milestone_maladie(self, p_id, milestone, date_str):
        pneumo_mode = self.config.get("pneumo_mode", PneumoProtocol.OLD.value)
        for v in self.scheduler.get_core_vaccines(milestone, pneumo_mode):
            self.db.mark_maladie(p_id, milestone, v, date_str)

    def cancel_vaccine(self, p_id, milestone, vax_name):
        self.db.cancel_vaccine(p_id, milestone, vax_name)

    def cancel_milestone(self, p_id, milestone):
        pneumo_mode = self.config.get("pneumo_mode", PneumoProtocol.OLD.value)
        for v in self.scheduler.get_core_vaccines(milestone, pneumo_mode):
            self.db.cancel_vaccine(p_id, milestone, v)

    def validate_vaccine_date(self, p_id, vax_name, input_date):
        dob_str, records_dict = self.db.get_patient_dob_and_records(p_id)
        if not dob_str: return None
        # Use patient's pneumo mode instead of global
        pneumo_mode = self.db.get_patient_pneumo_mode(p_id) 
        return self.scheduler.validate_vaccine_input(dob_str, records_dict, vax_name, pneumo_mode, input_date)

    def rename_vaccine_in_db(self, old_vax_name, new_vax_name):
        self.db.rename_vaccine(old_vax_name, new_vax_name)

    def delete_vaccine_dose_in_db(self, vax_name):
        self.db.delete_vaccine_dose(vax_name)

    def get_patient(self, p_id):
        return self.db.get_patient(p_id)

    def get_all_patients(self):
        return self.db.get_all_patients()

    def update_patient(self, p_id, name, dob_obj, sexe, address, parent_name, phone, allergies, email, pneumo_mode, center_schedule={}):
        dob_str = dob_obj.strftime("%Y-%m-%d")
        self.db.update_patient(p_id, name, dob_str, sexe, address, parent_name, phone, allergies, email, pneumo_mode)
        self.recalculate_schedule(p_id, center_schedule)

    def add_visit(self, p_id, date_str, weight, height, imc):
        self.db.add_visit(p_id, date_str, weight, height, imc)

    def get_visits(self, p_id):
        return self.db.get_visits(p_id)

    def get_daily_stats(self, date_str):
        return self.db.get_daily_stats(date_str)

    def get_monthly_stats(self, year_month_str):
        return self.db.get_monthly_stats(year_month_str)
