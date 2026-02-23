import os

with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

vaxapp_lines = lines[790:1588]

imports = """import json
import os
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTableWidget, QTableWidgetItem, QLabel, QLineEdit, 
                             QComboBox, QMessageBox, QHeaderView, QDialog, 
                             QScrollArea)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

from core.engine import VaxEngine
from ui.widgets.date_line_edit import DateLineEdit
from ui.dialogs.growth_dialog import GrowthDialog
from ui.dialogs.help_dialog import HelpDialog
from ui.dialogs.settings_dialog import SettingsDialog
from ui.dialogs.all_patients_dialog import AllPatientsDialog
from ui.dialogs.edit_patient_dialog import EditPatientDialog
from ui.dialogs.report_dialog import ReportDialog
from ui.dialogs.dashboard_dialog import DashboardDialog

"""

os.makedirs('ui', exist_ok=True)
with open('ui/main_window.py', 'w', encoding='utf-8') as f:
    f.write(imports)
    f.writelines(vaxapp_lines)
