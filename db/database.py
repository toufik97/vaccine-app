import sqlite3
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from contextlib import contextmanager
from core.enums import VaccineStatus, Gender

class Database:
    def __init__(self, db_path='vax_pro.db'):
        self.db_path = db_path
        self.setup_db()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def setup_db(self):
        with self.get_connection() as conn:
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
                                   (p_id, "4 Mois", "Rota3", due, VaccineStatus.PENDING.value, None, ""))
            conn.commit()

    def generate_id(self):
        year = datetime.now().strftime("%y")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id_label FROM patients WHERE id_label LIKE ?", (f'%/{year}',))
            ids = [int(row[0].split('/')[0]) for row in cursor.fetchall()]
            return f"{max(ids) + 1 if ids else 1}/{year}"

    def register_child(self, new_id, name, dob_str, sexe, address, parent_name, phone, allergies, email, initial_records):
        if sexe not in [Gender.MALE.value, Gender.FEMALE.value]:
            raise ValueError(f"Sexe invalide: '{sexe}'. Doit être '{Gender.MALE.value}' ou '{Gender.FEMALE.value}'.")
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO patients (id_label, name, dob, sexe, address, parent_name, phone, allergies, email) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                           (new_id, name, dob_str, sexe, address, parent_name, phone, allergies, email))
            
            for milestone, vax, due in initial_records:
                cursor.execute("INSERT INTO records (patient_id, milestone, vax_name, due_date, status, date_given, observations) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                               (new_id, milestone, vax, due, VaccineStatus.PENDING.value, None, ""))
            conn.commit()

    def update_records_due_dates(self, p_id, updates):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for new_due, vax_name in updates:
                cursor.execute("UPDATE records SET due_date = ? WHERE patient_id = ? AND vax_name = ?", 
                               (new_due, p_id, vax_name))
            conn.commit()

    def get_patient_dob_and_records(self, p_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT dob FROM patients WHERE id_label = ?", (p_id,))
            row = cursor.fetchone()
            if not row:
                return None, None
            dob_str = row[0]
            
            cursor.execute("SELECT vax_name, status, date_given, due_date FROM records WHERE patient_id = ?", (p_id,))
            records = {r[0]: {"status": r[1], "date_given": r[2], "due_date": r[3]} for r in cursor.fetchall()}
            return dob_str, records
        return dob_str, records

    def search_patients(self, query):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM patients WHERE name LIKE ? OR id_label = ?", (f'%{query}%', query))
            res = cursor.fetchall()
            return res

    def search_by_vaccine_date(self, date_str):
        with self.get_connection() as conn:
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
            return res

    def get_records(self, p_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT milestone, vax_name, due_date, status, date_given, observations FROM records WHERE patient_id = ? ORDER BY due_date ASC", (p_id,))
            res = cursor.fetchall()
            return res

    def update_vax_status(self, p_id, milestone, vax_name, status, date_given):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE records SET status = ?, date_given = ? WHERE patient_id = ? AND milestone = ? AND vax_name = ?", 
                           (status, date_given, p_id, milestone, vax_name))
            conn.commit()

    def update_milestone_status(self, p_id, milestone, status, date_given):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE records SET status = ?, date_given = ? WHERE patient_id = ? AND milestone = ?", 
                           (status, date_given, p_id, milestone))
            conn.commit()

    def mark_rupture(self, p_id, milestone, vax_name, date_str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT observations FROM records WHERE patient_id = ? AND milestone = ? AND vax_name = ?", (p_id, milestone, vax_name))
            row = cursor.fetchone()
            current_obs = row[0] if row and row[0] else ""
            if current_obs:
                if date_str not in current_obs: obs = current_obs + f", {date_str}"
                else: obs = current_obs
            else: obs = f"Rupture signalée le {date_str}"
            cursor.execute("UPDATE records SET status = ?, date_given = NULL, observations = ? WHERE patient_id = ? AND milestone = ? AND vax_name = ?", 
                           (VaccineStatus.RUPTURE.value, obs, p_id, milestone, vax_name))
            conn.commit()

    def mark_milestone_rupture(self, p_id, milestone, date_str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT vax_name, observations FROM records WHERE patient_id = ? AND milestone = ?", (p_id, milestone))
            rows = cursor.fetchall()
            for vax_name, current_obs in rows:
                current_obs = current_obs if current_obs else ""
                if current_obs:
                    if date_str not in current_obs: obs = current_obs + f", {date_str}"
                    else: obs = current_obs
                else: obs = f"Rupture signalée le {date_str}"
                cursor.execute("UPDATE records SET status = ?, date_given = NULL, observations = ? WHERE patient_id = ? AND milestone = ? AND vax_name = ?", 
                               (VaccineStatus.RUPTURE.value, obs, p_id, milestone, vax_name))
            conn.commit()

    def mark_maladie(self, p_id, milestone, vax_name, date_str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT observations FROM records WHERE patient_id = ? AND milestone = ? AND vax_name = ?", (p_id, milestone, vax_name))
            row = cursor.fetchone()
            current_obs = row[0] if row and row[0] else ""
            if current_obs:
                if date_str not in current_obs: obs = current_obs + f", Reporté (Maladie) le {date_str}"
                else: obs = current_obs
            else: obs = f"Reporté (Maladie) le {date_str}"
            cursor.execute("UPDATE records SET status = ?, date_given = NULL, observations = ? WHERE patient_id = ? AND milestone = ? AND vax_name = ?", 
                           (VaccineStatus.MALADIE.value, obs, p_id, milestone, vax_name))
            conn.commit()

    def mark_milestone_maladie(self, p_id, milestone, date_str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT vax_name, observations FROM records WHERE patient_id = ? AND milestone = ?", (p_id, milestone))
            rows = cursor.fetchall()
            for vax_name, current_obs in rows:
                current_obs = current_obs if current_obs else ""
                if current_obs:
                    if date_str not in current_obs: obs = current_obs + f", Reporté (Maladie) le {date_str}"
                    else: obs = current_obs
                else: obs = f"Reporté (Maladie) le {date_str}"
                cursor.execute("UPDATE records SET status = ?, date_given = NULL, observations = ? WHERE patient_id = ? AND milestone = ? AND vax_name = ?", 
                               (VaccineStatus.MALADIE.value, obs, p_id, milestone, vax_name))
            conn.commit()

    def cancel_vaccine(self, p_id, milestone, vax_name):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE records SET status = ?, date_given = NULL, observations = '' WHERE patient_id = ? AND milestone = ? AND vax_name = ?", 
                           (VaccineStatus.PENDING.value, p_id, milestone, vax_name))
            conn.commit()

    def cancel_milestone(self, p_id, milestone):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE records SET status = ?, date_given = NULL, observations = '' WHERE patient_id = ? AND milestone = ?", 
                           (VaccineStatus.PENDING.value, p_id, milestone))
            conn.commit()

    def get_patient(self, p_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM patients WHERE id_label = ?", (p_id,))
            res = cursor.fetchone()
            return res

    def get_all_patients(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM patients")
            res = cursor.fetchall()
            return res

    def update_patient(self, p_id, name, dob_str, sexe, address, parent_name, phone, allergies, email):
        if sexe not in [Gender.MALE.value, Gender.FEMALE.value]:
            raise ValueError(f"Sexe invalide: '{sexe}'. Doit être '{Gender.MALE.value}' ou '{Gender.FEMALE.value}'.")
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE patients SET name = ?, dob = ?, sexe = ?, address = ?, parent_name = ?, phone = ?, allergies = ?, email = ? WHERE id_label = ?", 
                           (name, dob_str, sexe, address, parent_name, phone, allergies, email, p_id))
            conn.commit()

    def add_visit(self, p_id, date_str, weight, height, imc):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO visits (patient_id, visit_date, weight, height, imc) VALUES (?, ?, ?, ?, ?)",
                           (p_id, date_str, weight, height, imc))
            conn.commit()

    def get_visits(self, p_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT visit_date, weight, height, imc FROM visits WHERE patient_id = ? ORDER BY visit_date DESC", (p_id,))
            res = cursor.fetchall()
            return res

    def get_daily_stats(self, date_str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT vax_name, COUNT(*) FROM records 
                              WHERE status = ? AND date_given = ? 
                              GROUP BY vax_name''', (VaccineStatus.DONE.value, date_str))
            stats = cursor.fetchall()
            return stats

    def get_monthly_stats(self, year_month_str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''SELECT vax_name, date_given FROM records 
                              WHERE status = ? AND date_given LIKE ? 
                              ORDER BY date_given ASC''', (VaccineStatus.DONE.value, year_month_str))
            rows = cursor.fetchall()
        
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

    def get_detailed_export_stats(self, date_pattern, exact_date=False):
        """
        Fetches detailed stats for the PDF Fiche Mensuelle / Daily report.
        If exact_date is True, date_pattern is treated as "YYYY-MM-DD".
        Otherwise it is treated as a LIKE pattern, e.g. "YYYY-MM%".
        Returns a list of dicts: [ { 'patient_id':.., 'vax_name':.., 'date_given':.., 'dob':.., 'sexe':.., 'address':.. } ]
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if exact_date:
                query = '''SELECT p.id_label, r.vax_name, r.date_given, p.dob, p.sexe, p.address,
                           (CASE WHEN EXISTS (SELECT 1 FROM records r2 WHERE r2.patient_id = p.id_label AND r2.vax_name = 'Pneumo3_NewOnly') THEN 1 ELSE 0 END) as has_pneumo3
                           FROM records r
                           JOIN patients p ON r.patient_id = p.id_label
                           WHERE r.status = ? AND r.date_given = ?
                           ORDER BY r.date_given ASC'''
            else:
                query = '''SELECT p.id_label, r.vax_name, r.date_given, p.dob, p.sexe, p.address,
                           (CASE WHEN EXISTS (SELECT 1 FROM records r2 WHERE r2.patient_id = p.id_label AND r2.vax_name = 'Pneumo3_NewOnly') THEN 1 ELSE 0 END) as has_pneumo3
                           FROM records r
                           JOIN patients p ON r.patient_id = p.id_label
                           WHERE r.status = ? AND r.date_given LIKE ?
                           ORDER BY r.date_given ASC'''
                           
            cursor.execute(query, (VaccineStatus.DONE.value, date_pattern))
            rows = cursor.fetchall()
        
        result = []
        for patient_id, vax_name, date_given, dob, sexe, address, has_pneumo3 in rows:
            result.append({
                "patient_id": patient_id,
                "vax_name": vax_name,
                "date_given": date_given,
                "dob": dob,
                "sexe": sexe,
                "address": address,
                "has_pneumo3": has_pneumo3
            })
        return result

    def get_nutrition_register_data(self, dates):
        """
        Fetches combined data for the Registre Intégré de Nutrition on a specific date.
        Returns a list of dicts: [
            {
                'record_date': '...',
                'patient_id': '...',
                'name': '...',
                'dob': '...',
                'sexe': '...',
                'address': '...',
                'weight': 0.0,
                'height': 0.0,
                'imc': 0.0,
                'vaccines': ['Vax1', 'Vax2']
            }
        ]
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            results = []
            if not dates:
                return results

            def chunker(seq, size):
                return (seq[pos:pos + size] for pos in range(0, len(seq), size))
            
            from core.who_zscore import WhoZScoreCalculator
            calc = WhoZScoreCalculator()

            # Process dates in chunks to stay well below the 999 SQLite variable limit
            for date_chunk in chunker(dates, 300):
                placeholders = ",".join(["?"] * len(date_chunk))
                sql_pairs = f"""
                    SELECT patient_id, visit_date as event_date FROM visits WHERE visit_date IN ({placeholders})
                    UNION
                    SELECT patient_id, date_given as event_date FROM records WHERE date_given IN ({placeholders}) AND status = ?
                """
                params = list(date_chunk) + list(date_chunk) + [VaccineStatus.DONE.value]
                cursor.execute(sql_pairs, params)
                pairs = cursor.fetchall()
                if not pairs: continue
                
                # Fetch Patients in chunks
                patient_ids = list(set([p[0] for p in pairs]))
                patients_dict = {}
                for p_chunk in chunker(patient_ids, 900):
                    p_placeholders = ",".join(["?"] * len(p_chunk))
                    cursor.execute(f"SELECT id_label, name, dob, sexe, address FROM patients WHERE id_label IN ({p_placeholders})", p_chunk)
                    for r in cursor.fetchall(): patients_dict[r[0]] = r
                        
                # Fetch Visits in chunks
                visits_dict = {}
                for p_chunk in chunker(patient_ids, 400):
                    p_placeholders = ",".join(["?"] * len(p_chunk))
                    cursor.execute(f"SELECT patient_id, visit_date, weight, height, imc FROM visits WHERE visit_date IN ({placeholders}) AND patient_id IN ({p_placeholders})", list(date_chunk) + p_chunk)
                    for r in cursor.fetchall(): visits_dict[(r[0], r[1])] = r
                        
                # Fetch Records in chunks
                records_dict = {}
                for p_chunk in chunker(patient_ids, 400):
                    p_placeholders = ",".join(["?"] * len(p_chunk))
                    cursor.execute(f"SELECT patient_id, date_given, vax_name FROM records WHERE date_given IN ({placeholders}) AND patient_id IN ({p_placeholders}) AND status = ?", list(date_chunk) + p_chunk + [VaccineStatus.DONE.value])
                    for r in cursor.fetchall():
                        key = (r[0], r[1])
                        if key not in records_dict: records_dict[key] = []
                        records_dict[key].append(r[2])
                
                # Assemble Results Chronologically
                sorted_pairs = sorted(pairs, key=lambda x: (x[1], x[0]))
                for p_id, event_date in sorted_pairs:
                    if p_id not in patients_dict: continue
                    p_row = patients_dict[p_id]
                    name, dob, sexe, address = p_row[1], p_row[2], p_row[3], p_row[4]
                    
                    v_row = visits_dict.get((p_id, event_date))
                    weight = v_row[2] if v_row else None
                    height = v_row[3] if v_row else None
                    imc = v_row[4] if v_row else None
                    
                    vaxes = records_dict.get((p_id, event_date), [])
                    
                    z_w, z_h, z_i = None, None, None
                    if weight or height or imc:
                        try:
                            z_w, z_h, z_i = calc.get_visit_zscores(dob, sexe, event_date, 
                                                                   weight if weight else 0, 
                                                                   height if height else 0, 
                                                                   imc if imc else 0)
                        except Exception:
                            pass
                    
                    results.append({
                        "record_date": event_date,
                        "patient_id": p_id,
                        "name": name,
                        "dob": dob,
                        "sexe": sexe,
                        "address": address,
                        "weight": weight,
                        "height": height,
                        "imc": imc,
                        "z_w": z_w,
                        "z_h": z_h,
                        "z_i": z_i,
                        "vaccines": vaxes
                    })
                    
        return results
