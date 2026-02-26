from core.engine import VaxEngine
from datetime import datetime
import json

engine = VaxEngine()
center_schedule = {"default": [0,1,2,3,4,5,6]}
engine.config["pneumo_mode"] = "New"

print("Registering dummy child...")
new_id = engine.register_child("Test Child Rupture", datetime(2024, 1, 1), "M", "Secteur A", center_schedule=center_schedule)

engine.settings = {"allow_future_dates": False, "pneumo_mode": "New"}
print("Simulating Rupture on Pentavalent 1 inside 2 Mois group...")

engine.mark_rupture(new_id, "2 Mois", "Pentavalent 1", "2024-03-01")

print("\nAttempting to validate Pneumo1 on 2024-03-10 (69 days old)")
res1 = engine.validate_vaccine_date(new_id, "Pneumo1", datetime(2024, 3, 10).date())
print(f"Result 1 (Expecting Error): {res1}")

print("\nAttempting to validate Pneumo1 on 2024-03-11 (70 days old)")
res2 = engine.validate_vaccine_date(new_id, "Pneumo1", datetime(2024, 3, 11).date())
print(f"Result 2 (Expecting None): {res2}")
