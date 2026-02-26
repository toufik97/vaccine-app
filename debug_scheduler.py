from core.scheduler import Scheduler
from datetime import datetime

s = Scheduler()
s.load_protocols()
dob = "2024-01-01"
records = {}

for milestone, days, vaccines in s.milestones:
    for v in vaccines:
        records[v] = {"status": "Pending", "date_given": None, "due_date": ""}

center = {"default": [0,1,2,3,4,5,6]}

print("==== OLD MODE ====")
updates_old = s.calculate_updates(dob, records, center, "Old")
print("Total updates old:", len(updates_old))
for u in updates_old:
    print(u)

print("\n==== NEW MODE ====")
updates_new = s.calculate_updates(dob, records, center, "New")
print("Total updates new:", len(updates_new))
for u in updates_new:
    print(u)
