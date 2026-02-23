import sqlite3
import math
import csv
import os
import json # <-- NEW
from datetime import datetime, timedelta

class VaxEngine:
    def __init__(self):
        self.db_path = 'vax_pro.db'
        self.setup_db()
        
        # --- NEW: Load from JSON instead of hardcoding ---
        self.load_protocols()
        # -------------------------------------------------
        
        # Chargement des données OMS en mémoire au démarrage
        self.who_data = self.load_who_data()
    
    def load_protocols(self):
        protocol_file = 'protocols.json'
        
        if os.path.exists(protocol_file):
            with open(protocol_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ensure milestones are tuples (Name, Days, [Vaccines]) as expected by the GUI
                self.milestones = [(m[0], m[1], m[2]) for m in data.get("milestones", [])]
                self.dependencies = data.get("dependencies", {})
        else:
            # Fallback default protocols if the file is missing
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
            # Auto-generate the JSON file for future editing
            with open(protocol_file, 'w', encoding='utf-8') as f:
                json.dump({"milestones": self.milestones, "dependencies": self.dependencies}, f, indent=4, ensure_ascii=False)

    def setup_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS patients 
                          (id_label TEXT PRIMARY KEY, name TEXT, dob DATE, sexe TEXT, address TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS records 
                          (patient_id TEXT, milestone TEXT, vax_name TEXT, due_date DATE, status TEXT, date_given DATE)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS visits 
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id TEXT, visit_date DATE, weight REAL, height REAL, imc REAL)''')
        
        cursor.execute("PRAGMA table_info(records)")
        columns_records = [col[1] for col in cursor.fetchall()]
        if 'observations' not in columns_records:
            cursor.execute("ALTER TABLE records ADD COLUMN observations TEXT DEFAULT ''")
            
        cursor.execute("PRAGMA table_info(patients)")
        columns_patients = [col[1] for col in cursor.fetchall()]
        if 'parent_name' not in columns_patients:
            cursor.execute("ALTER TABLE patients ADD COLUMN parent_name TEXT DEFAULT ''")
        if 'phone' not in columns_patients:
            cursor.execute("ALTER TABLE patients ADD COLUMN phone TEXT DEFAULT ''")
        if 'allergies' not in columns_patients:
            cursor.execute("ALTER TABLE patients ADD COLUMN allergies TEXT DEFAULT ''")
        if 'email' not in columns_patients:
            cursor.execute("ALTER TABLE patients ADD COLUMN email TEXT DEFAULT ''")
            
        cursor.execute("SELECT id_label, dob FROM patients")
        patients = cursor.fetchall()
        for p_id, dob_str in patients:
            cursor.execute("SELECT 1 FROM records WHERE patient_id = ? AND vax_name = 'Rota3'", (p_id,))
            if not cursor.fetchone():
                dob_obj = datetime.strptime(dob_str, "%Y-%m-%d")
                due = (dob_obj + timedelta(days=120)).strftime("%Y-%m-%d")
                cursor.execute("INSERT INTO records (patient_id, milestone, vax_name, due_date, status, date_given, observations) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                               (p_id, "4 Mois", "Rota3", due, "Pending", None, ""))
        conn.commit()
        conn.close()

    # --- MÉTHODES POUR LES Z-SCORES (OMS) ---
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

    def get_visit_zscores(self, p_id, visit_date_str, weight, height, imc):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT dob, sexe FROM patients WHERE id_label = ?", (p_id,))
        patient = cursor.fetchone()
        conn.close()
        
        if not patient: return None, None, None
        
        dob_str, sexe = patient
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

    # --- MÉTHODES DU PLANNING ET VACCINS ---
    def get_next_available_date(self, base_date_obj, vax_name, center_schedule):
        allowed_days = center_schedule.get(vax_name, center_schedule.get("default", [0, 1, 2, 3, 4]))
        current_date = base_date_obj
        while current_date.weekday() not in allowed_days:
            current_date += timedelta(days=1)
        return current_date

    def recalculate_schedule(self, p_id, center_schedule):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT dob FROM patients WHERE id_label = ?", (p_id,))
        dob_str = cursor.fetchone()[0]
        dob_obj = datetime.strptime(dob_str, "%Y-%m-%d")
        
        cursor.execute("SELECT vax_name, status, date_given, due_date FROM records WHERE patient_id = ?", (p_id,))
        records = {row[0]: {"status": row[1], "date_given": row[2], "due_date": row[3]} for row in cursor.fetchall()}
        
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
                if records[vax]["status"] in ["Done", "Externe"] and records[vax]["date_given"]:
                    projected_dates[vax] = datetime.strptime(records[vax]["date_given"], "%Y-%m-%d")
                    continue
                
                final_date = self.get_next_available_date(max_pushed_date, vax, center_schedule)
                projected_dates[vax] = final_date
                
                if final_date.strftime("%Y-%m-%d") != records[vax]["due_date"]:
                    updates.append((final_date.strftime("%Y-%m-%d"), p_id, vax))
        
        for new_due, pid, vax_name in updates:
            cursor.execute("UPDATE records SET due_date = ? WHERE patient_id = ? AND vax_name = ?", 
                           (new_due, pid, vax_name))
            
        conn.commit()
        conn.close()

    def generate_id(self):
        year = datetime.now().strftime("%y")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id_label FROM patients WHERE id_label LIKE ?", (f'%/{year}',))
        ids = [int(row[0].split('/')[0]) for row in cursor.fetchall()]
        conn.close()
        return f"{max(ids) + 1 if ids else 1}/{year}"

    def register_child(self, name, dob_obj, sexe, address, parent_name="", phone="", allergies="", email="", center_schedule={}):
        new_id = self.generate_id()
        dob_str = dob_obj.strftime("%Y-%m-%d")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO patients (id_label, name, dob, sexe, address, parent_name, phone, allergies, email) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                       (new_id, name, dob_str, sexe, address, parent_name, phone, allergies, email))
        
        for milestone, days, vaccines in self.milestones:
            due = (dob_obj + timedelta(days=days)).strftime("%Y-%m-%d")
            for vax in vaccines:
                cursor.execute("INSERT INTO records (patient_id, milestone, vax_name, due_date, status, date_given, observations) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                               (new_id, milestone, vax, due, "Pending", None, ""))
        conn.commit()
        conn.close()
        
        self.recalculate_schedule(new_id, center_schedule)
        return new_id

    def search_patients(self, query):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patients WHERE name LIKE ? OR id_label = ?", (f'%{query}%', query))
        res = cursor.fetchall()
        conn.close()
        return res

    def search_by_vaccine_date(self, date_str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        query = """
            SELECT p.*, GROUP_CONCAT(r.vax_name, ', ') as vaccines 
            FROM patients p
            JOIN records r ON p.id_label = r.patient_id
            WHERE r.date_given = ?
            GROUP BY p.id_label
        """
        cursor.execute(query, (date_str,))
        res = cursor.fetchall()
        conn.close()
        return res

    def get_records(self, p_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT milestone, vax_name, due_date, status, date_given, observations FROM records WHERE patient_id = ? ORDER BY due_date ASC", (p_id,))
        res = cursor.fetchall()
        conn.close()
        return res

    def update_vax_status(self, p_id, milestone, vax_name, status, date_given):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE records SET status = ?, date_given = ? WHERE patient_id = ? AND milestone = ? AND vax_name = ?", 
                       (status, date_given, p_id, milestone, vax_name))
        conn.commit()
        conn.close()

    def update_milestone_status(self, p_id, milestone, status, date_given):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE records SET status = ?, date_given = ? WHERE patient_id = ? AND milestone = ?", 
                       (status, date_given, p_id, milestone))
        conn.commit()
        conn.close()

    def mark_rupture(self, p_id, milestone, vax_name, date_str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT observations FROM records WHERE patient_id = ? AND milestone = ? AND vax_name = ?", (p_id, milestone, vax_name))
        row = cursor.fetchone()
        current_obs = row[0] if row and row[0] else ""
        if current_obs:
            if date_str not in current_obs: obs = current_obs + f", {date_str}"
            else: obs = current_obs
        else: obs = f"Rupture signalée le {date_str}"
        cursor.execute("UPDATE records SET status = 'Rupture', date_given = NULL, observations = ? WHERE patient_id = ? AND milestone = ? AND vax_name = ?", 
                       (obs, p_id, milestone, vax_name))
        conn.commit()
        conn.close()

    def mark_milestone_rupture(self, p_id, milestone, date_str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT vax_name, observations FROM records WHERE patient_id = ? AND milestone = ?", (p_id, milestone))
        rows = cursor.fetchall()
        for vax_name, current_obs in rows:
            current_obs = current_obs if current_obs else ""
            if current_obs:
                if date_str not in current_obs: obs = current_obs + f", {date_str}"
                else: obs = current_obs
            else: obs = f"Rupture signalée le {date_str}"
            cursor.execute("UPDATE records SET status = 'Rupture', date_given = NULL, observations = ? WHERE patient_id = ? AND milestone = ? AND vax_name = ?", 
                           (obs, p_id, milestone, vax_name))
        conn.commit()
        conn.close()

    def mark_maladie(self, p_id, milestone, vax_name, date_str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT observations FROM records WHERE patient_id = ? AND milestone = ? AND vax_name = ?", (p_id, milestone, vax_name))
        row = cursor.fetchone()
        current_obs = row[0] if row and row[0] else ""
        if current_obs:
            if date_str not in current_obs: obs = current_obs + f", Reporté (Maladie) le {date_str}"
            else: obs = current_obs
        else: obs = f"Reporté (Maladie) le {date_str}"
        cursor.execute("UPDATE records SET status = 'Maladie', date_given = NULL, observations = ? WHERE patient_id = ? AND milestone = ? AND vax_name = ?", 
                       (obs, p_id, milestone, vax_name))
        conn.commit()
        conn.close()

    def mark_milestone_maladie(self, p_id, milestone, date_str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT vax_name, observations FROM records WHERE patient_id = ? AND milestone = ?", (p_id, milestone))
        rows = cursor.fetchall()
        for vax_name, current_obs in rows:
            current_obs = current_obs if current_obs else ""
            if current_obs:
                if date_str not in current_obs: obs = current_obs + f", Reporté (Maladie) le {date_str}"
                else: obs = current_obs
            else: obs = f"Reporté (Maladie) le {date_str}"
            cursor.execute("UPDATE records SET status = 'Maladie', date_given = NULL, observations = ? WHERE patient_id = ? AND milestone = ? AND vax_name = ?", 
                           (obs, p_id, milestone, vax_name))
        conn.commit()
        conn.close()

    def cancel_vaccine(self, p_id, milestone, vax_name):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE records SET status = 'Pending', date_given = NULL, observations = '' WHERE patient_id = ? AND milestone = ? AND vax_name = ?", 
                       (p_id, milestone, vax_name))
        conn.commit()
        conn.close()

    def cancel_milestone(self, p_id, milestone):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE records SET status = 'Pending', date_given = NULL, observations = '' WHERE patient_id = ? AND milestone = ?", 
                       (p_id, milestone))
        conn.commit()
        conn.close()

    def get_patient(self, p_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patients WHERE id_label = ?", (p_id,))
        res = cursor.fetchone()
        conn.close()
        return res

    def get_all_patients(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patients")
        res = cursor.fetchall()
        conn.close()
        return res

    def update_patient(self, p_id, name, dob_obj, sexe, address, parent_name, phone, allergies, email, center_schedule={}):
        dob_str = dob_obj.strftime("%Y-%m-%d")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE patients SET name = ?, dob = ?, sexe = ?, address = ?, parent_name = ?, phone = ?, allergies = ?, email = ? WHERE id_label = ?", 
                       (name, dob_str, sexe, address, parent_name, phone, allergies, email, p_id))
        conn.commit()
        conn.close()
        
        self.recalculate_schedule(p_id, center_schedule)

    def add_visit(self, p_id, date_str, weight, height, imc):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO visits (patient_id, visit_date, weight, height, imc) VALUES (?, ?, ?, ?, ?)",
                       (p_id, date_str, weight, height, imc))
        conn.commit()
        conn.close()

    def get_visits(self, p_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT visit_date, weight, height, imc FROM visits WHERE patient_id = ? ORDER BY visit_date DESC", (p_id,))
        res = cursor.fetchall()
        conn.close()
        return res

    def get_daily_stats(self, date_str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''SELECT vax_name, COUNT(*) FROM records 
                          WHERE status = 'Done' AND date_given = ? 
                          GROUP BY vax_name''', (date_str,))
        stats = cursor.fetchall()
        conn.close()
        return stats

    def get_monthly_stats(self, year_month_str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''SELECT vax_name, date_given FROM records 
                          WHERE status = 'Done' AND date_given LIKE ? 
                          ORDER BY date_given ASC''', (year_month_str,))
        rows = cursor.fetchall()
        conn.close()
        
        stats = {}
        for vax, d_given in rows:
            if vax not in stats:
                stats[vax] = {}
            stats[vax][d_given] = stats[vax].get(d_given, 0) + 1
            
        result = []
        for vax, dates_dict in stats.items():
            total_doses = sum(dates_dict.values())
            dates_str_list = []
            
            for d, count in dates_dict.items():
                d_fmt = datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m")
                if count > 1:
                    dates_str_list.append(f"{d_fmt} (x{count})")
                else:
                    dates_str_list.append(d_fmt)
                    
            result.append((vax, total_doses, ", ".join(dates_str_list)))
            
        return result