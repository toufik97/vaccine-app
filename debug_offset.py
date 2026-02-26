from core.engine import VaxEngine
from datetime import datetime

engine = VaxEngine()
center_schedule = {"default": [0,1,2,3,4,5,6]}
engine.config["pneumo_mode"] = "New"

print("Registering dummy child...")
new_id = engine.register_child("Test Child Offset", datetime(2024, 1, 1), "M", "Secteur A", center_schedule=center_schedule)

engine.settings = {"allow_future_dates": False, "pneumo_mode": "New"}

print("\n--- Testing Offset ---")
print("Attempting to validate Pneumo1 without Pentavalent 1...")
res1 = engine.validate_vaccine_date(new_id, "Pneumo1", datetime(2024, 3, 20).date())
print(f"Result 1 (Expecting Error): {res1}")

print("\nValidating Pentavalent 1 on 2024-03-01")
engine.update_vax_status(new_id, "2 Mois", "Pentavalent 1", "Done", "2024-03-01")
engine.update_vax_status(new_id, "2 Mois", "VPO1", "Done", "2024-03-01")
engine.update_vax_status(new_id, "2 Mois", "Rota1", "Done", "2024-03-01")

print("\nAttempting to validate Pneumo1 on 2024-03-05 (Too early)")
res2 = engine.validate_vaccine_date(new_id, "Pneumo1", datetime(2024, 3, 5).date())
print(f"Result 2 (Expecting Error): {res2}")

print("\nAttempting to validate Pneumo1 on 2024-03-15 (Valid)")
res3 = engine.validate_vaccine_date(new_id, "Pneumo1", datetime(2024, 3, 15).date())
print(f"Result 3 (Expecting None): {res3}")
