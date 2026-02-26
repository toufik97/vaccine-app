from PyQt6.QtWidgets import QApplication
from ui.main_window import VaxApp
import sys
import traceback

print("Initializing app...")
app = QApplication(sys.argv)
window = VaxApp()

print("Registering dummy child via UI functions...")
try:
    window.dob_edit.setDate(window.dob_edit.date().currentDate().addYears(-1))
    window.save_patient()
    print("Patient saved. Current Patient ID:", window.current_patient_id)
    window.load_table_data(window.current_patient_id)
    print("load_table_data ran successfully.")
except Exception as e:
    print("CRASH during UI operations!")
    traceback.print_exc()

# also simulate switching protocol
print("Switching protocol to opposite...")
old_mode = window.settings.get("pneumo_mode", "Old")
new_mode = "New" if old_mode == "Old" else "Old"
window.settings["pneumo_mode"] = new_mode
window.engine.config["pneumo_mode"] = new_mode
window.engine.recalculate_schedule(window.current_patient_id, window.settings["center_schedule"])

try:
    window.load_table_data(window.current_patient_id)
    print("load_table_data ran successfully on NEW mode.")
except Exception as e:
    print("CRASH during UI operations after mode switch!")
    traceback.print_exc()
