import os
import csv
import math
from datetime import datetime

class WhoZScoreCalculator:
    def __init__(self):
        self.who_data = self.load_who_data()

    def load_who_data(self):
        data = {"Poids": {}, "Taille": {}, "IMC": {}}
        files = {
            "Poids": {"Masculin": "oms_data/weight_boy.csv", "Féminin": "oms_data/weight_girl.csv"},
            "Taille": {"Masculin": "oms_data/height_boy.csv", "Féminin": "oms_data/height_girl.csv"},
            "IMC": {"Masculin": "oms_data/bmi_boy.csv", "Féminin": "oms_data/bmi_girl.csv"}
        }

        for metric, sexes in files.items():
            for sexe, filepath in sexes.items():
                data[metric][sexe] = {}
                if os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            day = int(row['Day'])
                            data[metric][sexe][day] = {
                                "L": float(row['L']), 
                                "M": float(row['M']), 
                                "S": float(row['S'])
                            }
        return data

    def calculate_lms_zscore(self, measure, l, m, s):
        if measure <= 0: return None
        try:
            if l == 0: z = math.log(measure / m) / s
            else: z = ((measure / m) ** l - 1) / (l * s)
            return round(z, 2)
        except Exception:
            return None

    def get_visit_zscores(self, dob_str, sexe, visit_date_str, weight, height, imc):
        dob_obj = datetime.strptime(dob_str, "%Y-%m-%d")
        visit_obj = datetime.strptime(visit_date_str, "%Y-%m-%d")
        
        days_diff = (visit_obj - dob_obj).days
        if days_diff < 0: return None, None, None
        if days_diff > 1856: days_diff = 1856
        
        z_w, z_h, z_i = None, None, None
        
        if sexe in self.who_data["Poids"] and days_diff in self.who_data["Poids"][sexe]:
            lms = self.who_data["Poids"][sexe][days_diff]
            z_w = self.calculate_lms_zscore(weight, lms["L"], lms["M"], lms["S"])
            
        if sexe in self.who_data["Taille"] and days_diff in self.who_data["Taille"][sexe]:
            lms = self.who_data["Taille"][sexe][days_diff]
            z_h = self.calculate_lms_zscore(height, lms["L"], lms["M"], lms["S"])
            
        if sexe in self.who_data["IMC"] and days_diff in self.who_data["IMC"][sexe]:
            lms = self.who_data["IMC"][sexe][days_diff]
            z_i = self.calculate_lms_zscore(imc, lms["L"], lms["M"], lms["S"])
            
        return z_w, z_h, z_i
