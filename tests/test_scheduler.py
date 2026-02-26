import unittest
from datetime import datetime, timedelta
from core.scheduler import Scheduler

class TestSchedulerRules(unittest.TestCase):
    def setUp(self):
        self.scheduler = Scheduler()
        # Mock default protocols to ensure tests pass identically regardless of local protocols.json modification
        self.scheduler.milestones = [
            ("Naissance", 0, ["BCG", "VPO Zéro", "HB Zéro", "Vit D1"]),
            ("2 Mois", 60, ["Pentavalent 1", "Pneumo1"]),
            ("3 Mois", 90, ["Pentavalent 2", "Pneumo2"]),
            ("4 Mois", 120, ["Pentavalent 3", "VPI"]),
            ("6 Mois", 183, ["Pneumo3_NewOnly"]),
            ("12 Mois", 365, ["Pneumo_Final"])
        ]
        self.scheduler.rules = {
            "BCG": { "min_age_days": 0, "max_age_days": 365 },
            "Pentavalent 1": { "min_age_days": 42 },
            "Pentavalent 2": {
                "min_age_days": 70,
                "dependencies": [{"vaccine": "Pentavalent 1", "min_interval_days": 28}]
            },
            "Pneumo1": {
                "Old": { "min_age_days": 42 },
                "New": { "min_age_days": 42, "offset_from_milestone_days": 14, "rupture_fallback_offset": True, "fallback_min_interval_days": 70 }
            },
            "Pneumo2": {
                "Old": {
                    "min_age_days": 98,
                    "dependencies": [{"vaccine": "Pneumo1", "min_interval_days": 56}]
                },
                "New": {
                    "min_age_days": 102,
                    "dependencies": [{"vaccine": "Pneumo1", "min_interval_days": 60}],
                    "offset_from_milestone_days": 14
                }
            },
            "Pneumo3_NewOnly": {
                "New": {
                    "min_age_days": 183,
                    "dependencies": [{"vaccine": "Pneumo2", "min_interval_days": 60}],
                    "offset_from_milestone_days": 14
                }
            },
            "Pneumo_Final": {
                "Old": {
                    "min_age_days": 335,
                    "dependencies": [{"vaccine": "Pneumo2", "min_interval_days": 180}]
                },
                "New": {
                    "min_age_days": 335,
                    "dependencies": [{"vaccine": "Pneumo3_NewOnly", "min_interval_days": 60}],
                    "offset_from_milestone_days": 14
                }
            }
        }
        
        self.center_schedule = {
            "default": [0, 1, 2, 3, 4, 5, 6] # All days allowed to avoid weekday shift complications in basic tests
        }

    def test_standard_progression_old_pneumo(self):
        dob = "2024-01-01"
        records = {
            "BCG": {"status": "Pending", "date_given": None, "due_date": ""},
            "Pentavalent 1": {"status": "Pending", "date_given": None, "due_date": ""},
            "Pneumo1": {"status": "Pending", "date_given": None, "due_date": ""}
        }
        
        updates = self.scheduler.calculate_updates(dob, records, self.center_schedule, pneumo_mode="Old")
        updates_dict = {vax: date for date, vax in updates}
        
        self.assertEqual(updates_dict["BCG"], "2024-01-01")  # Min age 0
        self.assertEqual(updates_dict["Pentavalent 1"], "2024-03-01") # Target 60 days
        self.assertEqual(updates_dict["Pneumo1"], "2024-03-01") # Old Pneumo aligns directly.

    def test_standard_progression_new_pneumo_offset(self):
        dob = "2024-01-01"
        records = {
            "Pentavalent 1": {"status": "Pending", "date_given": None, "due_date": ""},
            "Pneumo1": {"status": "Pending", "date_given": None, "due_date": ""}
        }
        
        updates = self.scheduler.calculate_updates(dob, records, self.center_schedule, pneumo_mode="New")
        updates_dict = {vax: date for date, vax in updates}
        
        self.assertEqual(updates_dict["Pentavalent 1"], "2024-03-01") # Target 60 days
        self.assertEqual(updates_dict["Pneumo1"], "2024-03-15") # Target 60 + 14 offset = 74 days

    def test_late_vaccine_cascade(self):
        # Child gets Pentavalent 1 very late
        dob = "2024-01-01"
        records = {
            "Pentavalent 1": {"status": "Done", "date_given": "2024-04-01", "due_date": ""}, # Given at 3 months (90 days)
            "Pentavalent 2": {"status": "Pending", "date_given": None, "due_date": ""}
        }
        
        updates = self.scheduler.calculate_updates(dob, records, self.center_schedule, pneumo_mode="Old")
        updates_dict = {vax: date for date, vax in updates}
        
        # Penta 2 shouldn't be min_age_days 70 (which is mid-March).
        # It should rely on the dependency: Penta 1 date + 28 days
        # 2024-04-01 + 28 days = 2024-04-29
        self.assertEqual(updates_dict["Pentavalent 2"], "2024-04-29")
        
    def test_pneumo_new_dependencies_respect(self):
        # Child gets Pneumo2 very late
        dob = "2024-01-01"
        records = {
            "Pneumo2": {"status": "Done", "date_given": "2024-06-01", "due_date": ""},
            "Pneumo3_NewOnly": {"status": "Pending", "date_given": None, "due_date": ""}
        }
        
        updates = self.scheduler.calculate_updates(dob, records, self.center_schedule, pneumo_mode="New")
        updates_dict = {vax: date for date, vax in updates}
        
        # New Pneumo 3 requires 60 days after Pneumo 2
        # 2024-06-01 + 60 days = 2024-07-31
        # Even with offset, the dependency is the primary driver when it eclipses min_age.
        self.assertEqual(updates_dict["Pneumo3_NewOnly"], "2024-07-31")

    def test_rupture_fallback_offset_pneumo1(self):
        records = {
            "Pentavalent 1": {"status": "Rupture", "date_given": None, "due_date": "2024-02-12"}
        }
        err_69 = self.scheduler.validate_vaccine_input("2024-01-01", records, "Pneumo1", "New", datetime(2024, 3, 10).date()) # 69 days
        self.assertIsNotNone(err_69)
        self.assertIn("L'âge minimum sans vaccins principaux", err_69)
        
        err_70 = self.scheduler.validate_vaccine_input("2024-01-01", records, "Pneumo1", "New", datetime(2024, 3, 11).date()) # 70 days
        self.assertIsNone(err_70)

if __name__ == '__main__':
    unittest.main()
