from core.engine import VaxEngine
from datetime import datetime

engine = VaxEngine()
center_schedule = {"default": [0,1,2,3,4,5,6]}
engine.config["pneumo_mode"] = "New"

print("Registering dummy child...")
new_id = engine.register_child("Test Late Offset", datetime(2024, 1, 1), "M", "Secteur A", center_schedule=center_schedule)

engine.settings = {"allow_future_dates": False, "pneumo_mode": "New"}
print("Simulating Late Pentavalent on 2024-05-01 (instead of 2024-03-01)...")

engine.update_vax_status(new_id, "2 Mois", "Pentavalent 1", "Done", "2024-05-01")
engine.update_vax_status(new_id, "2 Mois", "VPO1", "Done", "2024-03-01")
engine.update_vax_status(new_id, "2 Mois", "Rota1", "Done", "2024-03-01")

engine.recalculate_schedule(new_id, center_schedule)

dob_str, records = engine.db.get_patient_dob_and_records(new_id)

print(f"Pneumo 1 New Due Date: {records['Pneumo1']['due_date']} (Expected: 2024-05-15)")
