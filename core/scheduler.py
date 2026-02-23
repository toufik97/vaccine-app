import json
import os
from datetime import datetime, timedelta

class Scheduler:
    def __init__(self):
        self.milestones = []
        self.dependencies = {}
        self.load_protocols()

    def load_protocols(self):
        protocol_file = 'protocols.json'
        
        if os.path.exists(protocol_file):
            with open(protocol_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.milestones = [(m[0], m[1], m[2]) for m in data.get("milestones", [])]
                self.dependencies = data.get("dependencies", {})
        else:
            self.milestones = [
                ("Naissance", 0, ["BCG", "VPO Zéro", "HB Zéro", "Vit D1"]),
                ("2 Mois", 60, ["Pentavalent 1", "VPO1", "Rota1", "Pneumo1"]),
                ("3 Mois", 90, ["Pentavalent 2", "VPO2", "Rota2"]),
                ("4 Mois", 120, ["Pentavalent 3", "VPO3", "Pneumo2", "VPI", "Rota3"]),
                ("6 Mois", 183, ["Vit D2", "Vit A1"]),
                ("9 Mois", 274, ["RR1"]),
                ("12 Mois", 365, ["Pneumo3", "Vit A2"]),
                ("18 Mois", 548, ["RR2", "Rappel DTC", "VPO (18 Mois)", "Vit A3"]),
                ("5 Ans", 1825, ["Rappel DTC", "VPO (5 Ans)"])
            ]
            self.dependencies = {
                "Pentavalent 2": ["Pentavalent 1", 28],
                "Pentavalent 3": ["Pentavalent 2", 28],
                "VPO2": ["VPO1", 28],
                "VPO3": ["VPO2", 28],
                "Rota2": ["Rota1", 28],
                "Rota3": ["Rota2", 28],
                "Pneumo2": ["Pneumo1", 56],    
                "Pneumo3": ["Pneumo2", 180],   
                "RR2": ["RR1", 180],           
                "Rappel DTC": ["Pentavalent 3", 365], 
                "VPO (18 Mois)": ["VPO3", 365]
            }
            with open(protocol_file, 'w', encoding='utf-8') as f:
                json.dump({"milestones": self.milestones, "dependencies": self.dependencies}, f, indent=4, ensure_ascii=False)

    def get_next_available_date(self, base_date_obj, vax_name, center_schedule):
        allowed_days = center_schedule.get(vax_name, center_schedule.get("default", [0, 1, 2, 3, 4]))
        current_date = base_date_obj
        while current_date.weekday() not in allowed_days:
            current_date += timedelta(days=1)
        return current_date

    def calculate_updates(self, dob_str, records_dict, center_schedule):
        """
        records_dict should be a dict mapped by vax_name: {"status": ..., "date_given": ..., "due_date": ...}
        Returns a list of tuples: (new_due_str, vax_name)
        """
        dob_obj = datetime.strptime(dob_str, "%Y-%m-%d")
        updates = []
        projected_dates = {}
        
        for milestone, days_from_birth, vaccines in self.milestones:
            target_date = dob_obj + timedelta(days=days_from_birth)
            max_pushed_date = target_date
            
            for vax in vaccines:
                if vax in self.dependencies:
                    dep_vax, min_days = self.dependencies[vax]
                    if dep_vax in projected_dates:
                        dep_date = projected_dates[dep_vax]
                        medical_min_date = dep_date + timedelta(days=min_days)
                        if medical_min_date > max_pushed_date:
                            max_pushed_date = medical_min_date
                            
            for vax in vaccines:
                if vax not in records_dict:
                    continue
                record = records_dict[vax]
                
                if record["status"] in ["Done", "Externe"] and record["date_given"]:
                    projected_dates[vax] = datetime.strptime(record["date_given"], "%Y-%m-%d")
                    continue
                
                final_date = self.get_next_available_date(max_pushed_date, vax, center_schedule)
                projected_dates[vax] = final_date
                
                if final_date.strftime("%Y-%m-%d") != record["due_date"]:
                    updates.append((final_date.strftime("%Y-%m-%d"), vax))
                    
        return updates
