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
            
        updates = self.scheduler.calculate_updates(dob_str, records_dict, center_schedule)
        self.db.update_records_due_dates(p_id, updates)

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
        self.db.update_milestone_status(p_id, milestone, status, date_given)

    def mark_rupture(self, p_id, milestone, vax_name, date_str):
        self.db.mark_rupture(p_id, milestone, vax_name, date_str)

    def mark_milestone_rupture(self, p_id, milestone, date_str):
        self.db.mark_milestone_rupture(p_id, milestone, date_str)

    def mark_maladie(self, p_id, milestone, vax_name, date_str):
        self.db.mark_maladie(p_id, milestone, vax_name, date_str)

    def mark_milestone_maladie(self, p_id, milestone, date_str):
        self.db.mark_milestone_maladie(p_id, milestone, date_str)

    def cancel_vaccine(self, p_id, milestone, vax_name):
        self.db.cancel_vaccine(p_id, milestone, vax_name)

    def cancel_milestone(self, p_id, milestone):
        self.db.cancel_milestone(p_id, milestone)

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
