from db.database import Database
from core.who_zscore import WhoZScoreCalculator
from core.scheduler import Scheduler
from datetime import datetime, timedelta

class VaxEngine:
    """
    Facade class that integrates Database, Scheduler, and WhoZScoreCalculator
    to behave largely exactly as the old monolithic logic.py VaxEngine.
    """
    def __init__(self):
        self.db = Database('vax_pro.db')
        self.zscore_calc = WhoZScoreCalculator()
        self.scheduler = Scheduler()
        self.load_config()

    def load_config(self):
        self.config_file = 'config.json'
        # Ensure we always parse the latest file locally
        import os, json
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = {"pneumo_mode": "Old"}
            self.save_config()

    def save_config(self):
        import json
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)
        
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
            
        pneumo_mode = self.config.get("pneumo_mode", "Old")
        updates = self.scheduler.calculate_updates(dob_str, records_dict, center_schedule, pneumo_mode)
        self.db.update_records_due_dates(p_id, updates)

    def recalculate_all_schedules(self, center_schedule):
        for p in self.db.get_all_patients():
            self.recalculate_schedule(p[0], center_schedule)

    def register_child(self, name, dob_obj, sexe, address, parent_name="", phone="", allergies="", email="", center_schedule={}):
        new_id = self.db.generate_id()
        dob_str = dob_obj.strftime("%Y-%m-%d")
        
        initial_records = []
        for milestone, days, vaccines in self.scheduler.milestones:
            due = (dob_obj + timedelta(days=days)).strftime("%Y-%m-%d")
            for vax in vaccines:
                initial_records.append((milestone, vax, due))
                
        self.db.register_child(new_id, name, dob_str, sexe, address, parent_name, phone, allergies, email, initial_records)
        self.recalculate_schedule(new_id, center_schedule)
        return new_id

    def search_patients(self, query):
        return self.db.search_patients(query)

    def search_by_vaccine_date(self, date_str):
        return self.db.search_by_vaccine_date(date_str)

    def get_records(self, p_id):
        return self.db.get_records(p_id)

    def update_vax_status(self, p_id, milestone, vax_name, status, date_given):
        self.db.update_vax_status(p_id, milestone, vax_name, status, date_given)

    def update_milestone_status(self, p_id, milestone, status, date_given):
        pneumo_mode = self.config.get("pneumo_mode", "Old")
        for v in self.scheduler.get_core_vaccines(milestone, pneumo_mode):
            self.db.update_vax_status(p_id, milestone, v, status, date_given)

    def mark_rupture(self, p_id, milestone, vax_name, date_str):
        self.db.mark_rupture(p_id, milestone, vax_name, date_str)

    def mark_milestone_rupture(self, p_id, milestone, date_str):
        pneumo_mode = self.config.get("pneumo_mode", "Old")
        for v in self.scheduler.get_core_vaccines(milestone, pneumo_mode):
            self.db.mark_rupture(p_id, milestone, v, date_str)

    def mark_maladie(self, p_id, milestone, vax_name, date_str):
        self.db.mark_maladie(p_id, milestone, vax_name, date_str)

    def mark_milestone_maladie(self, p_id, milestone, date_str):
        pneumo_mode = self.config.get("pneumo_mode", "Old")
        for v in self.scheduler.get_core_vaccines(milestone, pneumo_mode):
            self.db.mark_maladie(p_id, milestone, v, date_str)

    def cancel_vaccine(self, p_id, milestone, vax_name):
        self.db.cancel_vaccine(p_id, milestone, vax_name)

    def cancel_milestone(self, p_id, milestone):
        pneumo_mode = self.config.get("pneumo_mode", "Old")
        for v in self.scheduler.get_core_vaccines(milestone, pneumo_mode):
            self.db.cancel_vaccine(p_id, milestone, v)

    def validate_vaccine_date(self, p_id, vax_name, input_date):
        dob_str, records_dict = self.db.get_patient_dob_and_records(p_id)
        if not dob_str: return None
        pneumo_mode = self.config.get("pneumo_mode", "Old")
        return self.scheduler.validate_vaccine_input(dob_str, records_dict, vax_name, pneumo_mode, input_date)

    def get_patient(self, p_id):
        return self.db.get_patient(p_id)

    def get_all_patients(self):
        return self.db.get_all_patients()

    def update_patient(self, p_id, name, dob_obj, sexe, address, parent_name, phone, allergies, email, center_schedule={}):
        dob_str = dob_obj.strftime("%Y-%m-%d")
        self.db.update_patient(p_id, name, dob_str, sexe, address, parent_name, phone, allergies, email)
        self.recalculate_schedule(p_id, center_schedule)

    def add_visit(self, p_id, date_str, weight, height, imc):
        self.db.add_visit(p_id, date_str, weight, height, imc)

    def get_visits(self, p_id):
        return self.db.get_visits(p_id)

    def get_daily_stats(self, date_str):
        return self.db.get_daily_stats(date_str)

    def get_monthly_stats(self, year_month_str):
        return self.db.get_monthly_stats(year_month_str)
