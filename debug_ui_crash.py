from core.engine import VaxEngine
from datetime import datetime
import traceback

engine = VaxEngine()

center_schedule = {"default": [0,1,2,3,4,5,6]}

# Register a new child in New mode
engine.config["pneumo_mode"] = "New"
print("Registering child in New mode...")
new_id = engine.register_child("Test Child 2", datetime(2024, 1, 1), "M", "Secteur A", center_schedule=center_schedule)

# Simulate load_table_data grouping
print("Simulating load_table_data grouping (New mode)...")
records = engine.get_records(new_id)

def print_grouped(records):
    grouped = {}
    for r in records:
        m = r[0]
        if m not in grouped: grouped[m] = []
        grouped[m].append(r)

    for m, vax_list in grouped.items():
        try:
            due_date_str = vax_list[0][2]
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
            print(f"Milestone {m} parsed properly: {due_date}")
        except Exception as e:
             print(f"CRASH reading milestone {m}: {e}")
             traceback.print_exc()

print_grouped(records)

print("\nSwitching to Old mode...")
engine.config["pneumo_mode"] = "Old"
try:
    engine.recalculate_schedule(new_id, center_schedule)
    print("Recalculation successful.")
except Exception as e:
    print("CRASH during recalculation!")
    traceback.print_exc()

records = engine.get_records(new_id)
# filter
records = [r for r in records if r[1] != "Pneumo3_NewOnly"]
print("Simulating load_table_data grouping (Old mode)...")
print_grouped(records)
