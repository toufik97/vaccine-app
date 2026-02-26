from core.engine import VaxEngine
from datetime import datetime

engine = VaxEngine()
center_schedule = {"default": [0,1,2,3,4,5,6]}
engine.config["pneumo_mode"] = "New"

print("Registering dummy child...")
new_id = engine.register_child("Test Child 3", datetime(2024, 1, 1), "M", "Secteur A", center_schedule=center_schedule)

print("Pre-update:")
for r in engine.get_records(new_id):
    if r[0] == "2 Mois": print(r)

print("\nSimulating user typing '2024-03-01' in 2 Mois group input... Expecting Pneumo to stay Pending.")
engine.update_milestone_status(new_id, "2 Mois", "Done", "2024-03-01")

print("\nPost-update:")
for r in engine.get_records(new_id):
    if r[0] == "2 Mois": print(r)
