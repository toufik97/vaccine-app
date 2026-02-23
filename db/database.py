import sqlite3
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_path='vax_pro.db'):
        self.db_path = db_path
        self.setup_db()

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

    def generate_id(self):
        year = datetime.now().strftime("%y")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id_label FROM patients WHERE id_label LIKE ?", (f'%/{year}',))
        ids = [int(row[0].split('/')[0]) for row in cursor.fetchall()]
        conn.close()
        return f"{max(ids) + 1 if ids else 1}/{year}"

    def register_child(self, new_id, name, dob_str, sexe, address, parent_name, phone, allergies, email, initial_records):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO patients (id_label, name, dob, sexe, address, parent_name, phone, allergies, email) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                       (new_id, name, dob_str, sexe, address, parent_name, phone, allergies, email))
        
        for milestone, vax, due in initial_records:
            cursor.execute("INSERT INTO records (patient_id, milestone, vax_name, due_date, status, date_given, observations) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                           (new_id, milestone, vax, due, "Pending", None, ""))
        conn.commit()
        conn.close()

    def update_records_due_dates(self, p_id, updates):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for new_due, vax_name in updates:
            cursor.execute("UPDATE records SET due_date = ? WHERE patient_id = ? AND vax_name = ?", 
                           (new_due, p_id, vax_name))
        conn.commit()
        conn.close()

    def get_patient_dob_and_records(self, p_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT dob FROM patients WHERE id_label = ?", (p_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None, None
        dob_str = row[0]
        
        cursor.execute("SELECT vax_name, status, date_given, due_date FROM records WHERE patient_id = ?", (p_id,))
        records = {r[0]: {"status": r[1], "date_given": r[2], "due_date": r[3]} for r in cursor.fetchall()}
        conn.close()
        return dob_str, records

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

    def update_patient(self, p_id, name, dob_str, sexe, address, parent_name, phone, allergies, email):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE patients SET name = ?, dob = ?, sexe = ?, address = ?, parent_name = ?, phone = ?, allergies = ?, email = ? WHERE id_label = ?", 
                       (name, dob_str, sexe, address, parent_name, phone, allergies, email, p_id))
        conn.commit()
        conn.close()

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
