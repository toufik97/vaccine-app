import json
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

class VaxApp(QWidget):
    def __init__(self):
        super().__init__()
        self.engine = VaxEngine()
        self.current_patient_id = None
        self.pending_focus_row = None 
        self.collapsed_groups = set() 
        
        self.settings_file = "config.json"
        self.load_settings()
        
        self.initUI()
        self.apply_theme()

    def load_settings(self):
        default_settings = {
            "dark_mode": True,
            "fold_by_default": True,
            "secteurs": ["Secteur A", "Secteur B", "Secteur C", "Hors Secteur"],
            "center_schedule": {"default": [0, 1, 2, 3, 4]} 
        }
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    self.settings = json.load(f)
                    if "center_schedule" not in self.settings:
                        self.settings["center_schedule"] = default_settings["center_schedule"]
            except Exception:
                self.settings = default_settings.copy()
        else:
            self.settings = default_settings.copy()

    def save_settings(self):
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=4)

    def initUI(self):
        self.setWindowTitle('Vaccine Tracker Pro - Morocco 2026')
        self.setMinimumSize(1100, 750)
        main_layout = QHBoxLayout()

        left_panel_widget = QWidget()
        left_panel = QVBoxLayout(left_panel_widget)
        
        top_btns_layout = QHBoxLayout()
        self.help_btn = QPushButton("❔ Guide")
        self.help_btn.setStyleSheet("background-color: #3498db; color: white; padding: 8px; font-weight: bold;")
        self.help_btn.clicked.connect(self.show_help)
        top_btns_layout.addWidget(self.help_btn)
        
        self.settings_btn = QPushButton("⚙️ Paramètres") 
        self.settings_btn.setStyleSheet("background-color: #7f8c8d; color: white; padding: 8px; font-weight: bold;")
        self.settings_btn.clicked.connect(self.open_settings)
        top_btns_layout.addWidget(self.settings_btn)
        left_panel.addLayout(top_btns_layout)
        
        self.stats_btn = QPushButton("📊 Tableau de Bord")
        self.stats_btn.setStyleSheet("background-color: #8e44ad; color: white; padding: 10px; font-weight: bold;")
        self.stats_btn.clicked.connect(self.show_dashboard)
        left_panel.addWidget(self.stats_btn)
        
        self.view_all_btn = QPushButton("📂 Tous les Dossiers")
        self.view_all_btn.setStyleSheet("background-color: #2980b9; color: white; padding: 10px; font-weight: bold;")
        self.view_all_btn.clicked.connect(self.show_all_patients)
        left_panel.addWidget(self.view_all_btn)
        
        left_panel.addSpacing(15)
        left_panel.addWidget(QLabel("<b>RECHERCHE RAPIDE</b>"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nom, ID, ou Date (ex: 21/02/26)")
        self.search_input.returnPressed.connect(self.handle_search)
        left_panel.addWidget(self.search_input)
        
        left_panel.addSpacing(15)
        left_panel.addWidget(QLabel("<b>INFORMATIONS OBLIGATOIRES</b>"))
        
        self.name_in = QLineEdit()
        self.name_in.setPlaceholderText("Nom de l'enfant")
        left_panel.addWidget(self.name_in)
        
        h_info = QHBoxLayout()
        self.sexe_in = QComboBox()
        self.sexe_in.addItems(["Masculin", "Féminin"])
        h_info.addWidget(self.sexe_in)
        
        self.address_in = QComboBox()
        self.address_in.addItems(self.settings["secteurs"])
        h_info.addWidget(self.address_in)
        left_panel.addLayout(h_info)
        
        self.date_in = QLineEdit()
        self.date_in.setPlaceholderText("JJ/MM/AA (Naissance)")
        left_panel.addWidget(self.date_in)
        
        left_panel.addSpacing(10)
        left_panel.addWidget(QLabel("<b>INFORMATIONS FACULTATIVES</b>"))
        
        self.parent_in = QLineEdit()
        self.parent_in.setPlaceholderText("Nom du parent / Tuteur")
        left_panel.addWidget(self.parent_in)
        
        self.phone_in = QLineEdit()
        self.phone_in.setPlaceholderText("N° de Téléphone")
        left_panel.addWidget(self.phone_in)
        
        self.email_in = QLineEdit()
        self.email_in.setPlaceholderText("Adresse Email")
        left_panel.addWidget(self.email_in)
        
        self.allergies_in = QLineEdit()
        self.allergies_in.setPlaceholderText("Allergies / Notes médicales")
        left_panel.addWidget(self.allergies_in)
        
        save_btn = QPushButton("Enregistrer Nouveau")
        save_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 10px; font-weight: bold;")
        save_btn.clicked.connect(self.handle_save)
        left_panel.addWidget(save_btn)
        left_panel.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(left_panel_widget)
        scroll.setFixedWidth(300)

        right_panel = QVBoxLayout()
        self.info_lbl = QLabel("Veuillez charger un dossier patient")
        self.info_lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.info_lbl.setWordWrap(True)
        right_panel.addWidget(self.info_lbl)
        
        action_layout = QHBoxLayout()
        self.edit_btn = QPushButton("✏️ Modifier le Dossier")
        self.edit_btn.setEnabled(False)
        self.edit_btn.clicked.connect(self.edit_patient)
        
        self.growth_btn = QPushButton("⚖️ Constantes & Croissance")
        self.growth_btn.setEnabled(False)
        self.growth_btn.clicked.connect(self.open_growth_dialog)
        
        self.report_btn = QPushButton("📄 Rapport Patient")
        self.report_btn.setEnabled(False)
        self.report_btn.clicked.connect(self.generate_report)
        
        action_layout.addWidget(self.edit_btn)
        action_layout.addWidget(self.growth_btn)
        action_layout.addWidget(self.report_btn)
        right_panel.addLayout(action_layout)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Étape / Vaccin", "Date Prévue", "Date Administrée"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.cellClicked.connect(self.toggle_group)
        right_panel.addWidget(self.table)

        main_layout.addWidget(scroll)
        main_layout.addLayout(right_panel, 1)
        self.setLayout(main_layout)

    def show_help(self):
        dialog = HelpDialog(self)
        dialog.exec()

    def open_settings(self):
        dialog = SettingsDialog(self, self.settings)
        if dialog.exec():
            self.settings = dialog.get_new_settings()
            self.save_settings()
            current_addr = self.address_in.currentText()
            self.address_in.clear()
            self.address_in.addItems(self.settings["secteurs"])
            if current_addr in self.settings["secteurs"]:
                self.address_in.setCurrentText(current_addr)
            self.apply_theme()
            if self.current_patient_id:
                if self.settings.get("fold_by_default", True):
                    self.collapsed_groups = set(m[0] for m in self.engine.milestones)
                else:
                    self.collapsed_groups.clear()
                self.load_table_data(self.current_patient_id)

    def apply_theme(self):
        if self.settings.get("dark_mode", True):
            self.setStyleSheet("""
                QWidget { background-color: #1e1e1e; color: #ffffff; }
                QTableWidget { background-color: #2b2b2b; color: #ffffff; gridline-color: #444444; }
                QHeaderView::section { background-color: #333333; color: white; padding: 4px; border: 1px solid #444; }
                QLineEdit, QComboBox, QDateEdit, QTextEdit { background-color: #333333; color: white; border: 1px solid #555; }
                QToolTip { background-color: #34495e; color: white; border: 1px solid #2980b9; padding: 5px; border-radius: 3px; }
            """)
        else:
            self.setStyleSheet("""
                QToolTip { background-color: #ecf0f1; color: black; border: 1px solid #bdc3c7; padding: 5px; border-radius: 3px; }
            """)

    def handle_save(self):
        name = self.name_in.text().strip()
        if not name:
            QMessageBox.warning(self, "Action requise", "Le nom de l'enfant est obligatoire.")
            self.name_in.setFocus()
            return
            
        dob_text = self.date_in.text().strip().replace('-', '/').replace('.', '/')
        try:
            parsed_dob = datetime.strptime(dob_text, "%d/%m/%Y").date()
        except ValueError:
            try: parsed_dob = datetime.strptime(dob_text, "%d/%m/%y").date()
            except ValueError:
                QMessageBox.warning(self, "Erreur", "Format de date de naissance invalide.")
                self.date_in.setFocus()
                return

        # --- NEW: Phase 1 Input Validation (No Future DOB) ---
        if parsed_dob > datetime.now().date():
            QMessageBox.warning(self, "Erreur", "La date de naissance ne peut pas être dans le futur.")
            self.date_in.setFocus()
            return
        # -----------------------------------------------------

        parent = self.parent_in.text().strip()
        phone = self.phone_in.text().strip()
        allergies = self.allergies_in.text().strip()
        email = self.email_in.text().strip()
        
        new_id = self.engine.register_child(name, parsed_dob, self.sexe_in.currentText(), self.address_in.currentText(), parent, phone, allergies, email, self.settings["center_schedule"])
        
        self.name_in.clear()
        self.date_in.clear()
        self.parent_in.clear()
        self.phone_in.clear()
        self.email_in.clear()
        self.allergies_in.clear()
        
        self.search_input.setText(new_id)
        self.handle_search()

    def handle_search(self):
        search_text = self.search_input.text().strip()
        if not search_text: return
        
        is_date = False
        search_date_str = ""
        text_fmt = search_text.replace('-', '/').replace('.', '/')
        
        try:
            parsed = datetime.strptime(text_fmt, "%d/%m/%Y").date()
            search_date_str = parsed.strftime("%Y-%m-%d")
            is_date = True
        except ValueError:
            try: 
                parsed = datetime.strptime(text_fmt, "%d/%m/%y").date()
                search_date_str = parsed.strftime("%Y-%m-%d")
                is_date = True
            except ValueError: pass
            
        if is_date:
            results = self.engine.search_by_vaccine_date(search_date_str)
        else:
            results = self.engine.search_patients(search_text)
            
        if not results:
            if is_date: QMessageBox.information(self, "Recherche", f"Aucun patient vacciné le {parsed.strftime('%d/%m/%Y')}.")
            else: QMessageBox.warning(self, "Recherche", "Aucun dossier trouvé.")
            return
            
        if len(results) > 1 or is_date:
            title = f"Résultats de recherche ({len(results)} dossiers trouvés)"
            if is_date: title = f"Vaccinés le {parsed.strftime('%d/%m/%Y')} ({len(results)} dossiers)"
            
            dialog = AllPatientsDialog(self, results, self.settings["secteurs"], engine=self.engine, title=title)
            if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_id:
                self.search_input.setText(dialog.selected_id)
                self.handle_search()
            return
            
        p = results[0] 
        self.current_patient_name = p[1] 
        
        if self.current_patient_id != p[0]:
            self.current_patient_id = p[0]
            if self.settings.get("fold_by_default", True):
                self.collapsed_groups = set(m[0] for m in self.engine.milestones)
            else:
                self.collapsed_groups.clear()
        
        dob_formatted = datetime.strptime(p[2], "%Y-%m-%d").strftime("%d/%m/%Y")
        lbl_color = "#3498db" if self.settings.get("dark_mode", True) else "#2c3e50"
        
        profile_text = f"Dossier N° {p[0]} : {p[1]} ({p[3]}) | {p[4]} | Né(e) le: {dob_formatted}"
        
        options_text = []
        if len(p) > 5 and p[5]: options_text.append(f"Parent: {p[5]}")
        if len(p) > 6 and p[6]: options_text.append(f"Tél: {p[6]}")
        if len(p) > 8 and p[8]: options_text.append(f"Email: {p[8]}")
        
        if options_text:
            profile_text += f"\n<span style='font-size: 13px; font-weight: normal;'>{' | '.join(options_text)}</span>"
            
        if len(p) > 7 and p[7]:
            profile_text += f"\n<span style='color: #e74c3c;'>⚠️ Allergies / Notes : {p[7]}</span>"

        self.info_lbl.setStyleSheet(f"font-size: 16px; color: {lbl_color}; font-weight: bold;")
        self.info_lbl.setText(profile_text)
        
        self.edit_btn.setEnabled(True)
        self.growth_btn.setEnabled(True)
        self.report_btn.setEnabled(True)
        
        self.load_table_data(p[0])

    def show_dashboard(self):
        dialog = DashboardDialog(self, self.engine)
        dialog.exec()

    def show_all_patients(self):
        patients = self.engine.get_all_patients()
        if not patients:
            QMessageBox.information(self, "Dossiers", "La base de données est actuellement vide.")
            return
        dialog = AllPatientsDialog(self, patients, self.settings["secteurs"], engine=self.engine)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_id:
            self.search_input.setText(dialog.selected_id)
            self.handle_search()

    def open_growth_dialog(self):
        if self.current_patient_id:
            dialog = GrowthDialog(self, self.engine, self.current_patient_id, self.current_patient_name)
            dialog.exec()

    def toggle_group(self, row, col):
        if col == 0:
            item = self.table.item(row, col)
            if item:
                data = item.data(Qt.ItemDataRole.UserRole)
                if data and data[0] == "group":
                    milestone = data[1]
                    if milestone in self.collapsed_groups:
                        self.collapsed_groups.remove(milestone)
                    else:
                        self.collapsed_groups.add(milestone)
                    self.load_table_data(self.current_patient_id)

    def load_table_data(self, p_id):
        p_data = self.engine.get_patient(p_id)
        dob_str = p_data[2]
        records = self.engine.get_records(p_id)
        
        grouped = {}
        for r in records:
            m = r[0]
            if m not in grouped: grouped[m] = []
            grouped[m].append(r)
            
        total_rows = len(grouped) + len(records)
        self.table.setRowCount(total_rows)
        today = datetime.now().date()
        
        milestone_days = {m[0]: m[1] for m in self.engine.milestones}

        if self.settings.get("dark_mode", True):
            bg_group = QColor("#34495e")
            bg_done = QColor("#1b5e20")
            bg_late = QColor("#b71c1c")
            bg_today = QColor("#e65100")
            bg_rupture = QColor("#8e44ad") 
            bg_maladie = QColor("#d35400") 
            text_color = QColor("#ffffff")
            text_rupture = QColor("#ffffff")
            text_maladie = QColor("#ffffff")
            input_style_done = "background-color: transparent; border: none; font-weight: bold; color: #ffffff;"
            input_style_empty = "background-color: #333333; border: 1px solid #555; color: #ffffff;"
            input_style_group = "background-color: #2c3e50; border: 1px solid #555; color: #ffffff; font-weight: bold;"
            input_style_rupture = "background-color: transparent; border: none; font-weight: bold; color: #ffffff;"
            input_style_maladie = "background-color: transparent; border: none; font-weight: bold; color: #ffffff;"
        else:
            bg_group = QColor("#e0e6ed")
            bg_done = QColor("#d4edda")
            bg_late = QColor("#f8d7da")
            bg_today = QColor("#fff3cd")
            bg_rupture = QColor("#d2b4de") 
            bg_maladie = QColor("#fdebd0") 
            text_color = QColor("#000000")
            text_rupture = QColor("#4a235a")
            text_maladie = QColor("#d35400")
            input_style_done = "background-color: transparent; border: none; font-weight: bold; color: #000000;"
            input_style_empty = "background-color: white; border: 1px solid #ccc; color: #000000;"
            input_style_group = "background-color: white; border: 1px solid #999; color: #000000; font-weight: bold;"
            input_style_rupture = "background-color: transparent; border: none; font-weight: bold; color: #4a235a;"
            input_style_maladie = f"background-color: transparent; border: none; font-weight: bold; color: {text_maladie.name()};"

        bold_font = QFont()
        bold_font.setBold(True)

        row_idx = 0
        for milestone, vax_list in grouped.items():
            all_completed = all(v[3] in ["Done", "Externe"] for v in vax_list)
            
            dates_list = [v[4] for v in vax_list if v[3] in ["Done", "Externe"] and v[4]]
            group_date_str = max(set(dates_list), key=dates_list.count) if (all_completed and dates_list) else None
            
            due_date_str = vax_list[0][2]
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
            
            base_target = datetime.strptime(dob_str, "%Y-%m-%d").date() + timedelta(days=milestone_days[milestone])
            icon_delay = " 🕒" if (due_date - base_target).days > 7 else ""
            
            is_late = False
            is_today = False
            if milestone.upper() == "NAISSANCE":
                if today > due_date + timedelta(days=30): is_late = True
            else:
                if today > due_date: is_late = True
            
            if today == due_date: is_today = True
            
            group_status = "Done" if all_completed else "Pending"
            is_collapsed = milestone in self.collapsed_groups
            arrow = "▶" if is_collapsed else "▼"

            lbl_group = QTableWidgetItem(f"{arrow} {milestone.upper()}")
            lbl_group.setFont(bold_font)
            lbl_group.setForeground(text_color)
            lbl_group.setFlags(lbl_group.flags() & ~Qt.ItemFlag.ItemIsEditable)
            lbl_group.setData(Qt.ItemDataRole.UserRole, ("group", milestone))
            
            due_group = QTableWidgetItem(due_date.strftime("%d/%m/%Y") + icon_delay)
            due_group.setFont(bold_font)
            due_group.setForeground(text_color)
            due_group.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            due_group.setFlags(due_group.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            group_widget = DateLineEdit(row_idx)
            group_widget.setPlaceholderText("Valider le groupe")
            group_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            group_widget.navigationRequested.connect(
                lambda r, d, is_g=True, m=milestone, v=None, st=group_status, gs=group_date_str, dob=dob_str: 
                self.handle_navigation(r, d, is_g, m, v, st, gs, dob)
            )

            if all_completed and group_date_str:
                group_fmt = datetime.strptime(group_date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
                all_externe = all(v[3] == "Externe" for v in vax_list)
                tag = " (Naiss.)" if (all_externe and group_date_str == dob_str) else (" (Ext.)" if all_externe else "")
                if len(set(dates_list)) > 1: tag += " *"
                    
                group_widget.setText(f"{group_fmt}{tag}")
                group_widget.setStyleSheet(input_style_done)
                lbl_group.setBackground(bg_done)
                due_group.setBackground(bg_done)
                bg_container = QTableWidgetItem()
                bg_container.setBackground(bg_done)
                self.table.setItem(row_idx, 2, bg_container)
            else:
                group_widget.setStyleSheet(input_style_group)
                if is_late:
                    lbl_group.setBackground(bg_late)
                    due_group.setBackground(bg_late)
                elif is_today:
                    lbl_group.setBackground(bg_today)
                    due_group.setBackground(bg_today)
                else:
                    lbl_group.setBackground(bg_group)
                    due_group.setBackground(bg_group)
                self.table.setItem(row_idx, 2, QTableWidgetItem())
                
            self.table.setItem(row_idx, 0, lbl_group)
            self.table.setItem(row_idx, 1, due_group)
            self.table.setCellWidget(row_idx, 2, group_widget)
            row_idx += 1

            for v_data in vax_list:
                _, vax_name, _, status, given_str, obs = v_data
                
                lbl_text = f"      ↳ {vax_name}"
                if obs: lbl_text += " ℹ️"
                    
                lbl_vax = QTableWidgetItem(lbl_text)
                if obs: lbl_vax.setToolTip(obs)
                lbl_vax.setForeground(text_color)
                lbl_vax.setFlags(lbl_vax.flags() & ~Qt.ItemFlag.ItemIsEditable)
                
                due_vax = QTableWidgetItem("") 
                due_vax.setFlags(due_vax.flags() & ~Qt.ItemFlag.ItemIsEditable)
                
                vax_widget = DateLineEdit(row_idx)
                vax_widget.setPlaceholderText("Date, T, N, E, R, M")
                vax_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                vax_widget.navigationRequested.connect(
                    lambda r, d, is_g=False, m=milestone, v=vax_name, st=status, gs=given_str, dob=dob_str: 
                    self.handle_navigation(r, d, is_g, m, v, st, gs, dob)
                )

                if status in ["Done", "Externe"] and given_str:
                    given_fmt = datetime.strptime(given_str, "%Y-%m-%d").strftime("%d/%m/%Y")
                    tag = " (Naiss.)" if given_str == dob_str else " (Ext.)" if status == "Externe" else ""
                    vax_widget.setText(f"{given_fmt}{tag}")
                    lbl_vax.setBackground(bg_done)
                    due_vax.setBackground(bg_done)
                    vax_widget.setStyleSheet(input_style_done)
                    bg_container = QTableWidgetItem()
                    bg_container.setBackground(bg_done)
                    self.table.setItem(row_idx, 2, bg_container)
                    
                elif status in ["Rupture", "Maladie"]:
                    if status == "Rupture":
                        vax_widget.setText("Rupture de stock")
                        lbl_vax.setBackground(bg_rupture)
                        due_vax.setBackground(bg_rupture)
                        lbl_vax.setForeground(text_rupture)
                        due_vax.setForeground(text_rupture)
                        vax_widget.setStyleSheet(input_style_rupture)
                        bg_container = QTableWidgetItem()
                        bg_container.setBackground(bg_rupture)
                    else:
                        vax_widget.setText("Reporté (Maladie)")
                        lbl_vax.setBackground(bg_maladie)
                        due_vax.setBackground(bg_maladie)
                        lbl_vax.setForeground(text_maladie)
                        due_vax.setForeground(text_maladie)
                        vax_widget.setStyleSheet(input_style_maladie)
                        bg_container = QTableWidgetItem()
                        bg_container.setBackground(bg_maladie)
                    self.table.setItem(row_idx, 2, bg_container)
                    
                else:
                    vax_widget.setStyleSheet(input_style_empty)
                    if is_late:
                        due_vax.setBackground(bg_late)
                        lbl_vax.setBackground(bg_late)
                    elif is_today:
                        due_vax.setBackground(bg_today)
                        lbl_vax.setBackground(bg_today)
                    self.table.setItem(row_idx, 2, QTableWidgetItem())

                self.table.setItem(row_idx, 0, lbl_vax)
                self.table.setItem(row_idx, 1, due_vax)
                self.table.setCellWidget(row_idx, 2, vax_widget)
                
                self.table.setRowHidden(row_idx, is_collapsed)
                row_idx += 1

        if self.pending_focus_row is not None:
            widget = self.table.cellWidget(self.pending_focus_row, 2)
            if widget:
                widget.setFocus()
                widget.selectAll()
            self.pending_focus_row = None

    def handle_navigation(self, current_row, direction, is_group, milestone, vax_name, current_status, given_str, dob_str):
        if not self.current_patient_id: return
        
        widget = self.table.cellWidget(current_row, 2)
        text = widget.text().strip().upper()
        needs_update = False
        selected_date = None
        status_to_save = "Done" 
        
        next_row = current_row + direction
        while 0 <= next_row < self.table.rowCount():
            if not self.table.isRowHidden(next_row):
                break
            next_row += direction
            
        if not (0 <= next_row < self.table.rowCount()) or self.table.isRowHidden(next_row):
            next_row = current_row
            
        text = text.replace("(NAISS.)", "").replace("(EXT.)", "").replace("(RUPTURE)", "").replace("DE STOCK", "").replace("REPORTÉ", "").replace("(MALADIE)", "").replace("*", "").strip()
        
        if not text:
            if current_status in ["Done", "Externe", "Rupture", "Maladie"]:
                needs_update = True 
        else:
            parsed_date = None
            
            if text in ["T", "TODAY", "AUJ", "AUJOURD'HUI"]:
                parsed_date = datetime.now().date()
                status_to_save = "Done"
            elif text in ["T E", "TE", "T EXT"]:
                parsed_date = datetime.now().date()
                status_to_save = "Externe"
            elif text in ["N", "NAISS", "NAISSANCE"]:
                if is_group or vax_name != "HB Zéro":
                    QMessageBox.warning(self, "Erreur Médicale", "Le raccourci 'N' est strictement réservé au vaccin 'HB Zéro' fait à la maternité.")
                    widget.setFocus()
                    widget.selectAll()
                    return
                parsed_date = datetime.strptime(dob_str, "%Y-%m-%d").date()
                status_to_save = "Externe" 
            elif text in ["R", "RUPTURE"]:
                parsed_date = datetime.now().date()
                status_to_save = "Rupture"
            elif text in ["M", "MALADIE", "FIEVRE"]:
                parsed_date = datetime.now().date()
                status_to_save = "Maladie"
            else:
                if text.endswith("EXT"):
                    status_to_save = "Externe"
                    text = text[:-3].strip()
                elif text.endswith("E"):
                    status_to_save = "Externe"
                    text = text[:-1].strip()
                elif text.endswith("RUPTURE"):
                    status_to_save = "Rupture"
                    text = text.replace("RUPTURE", "").strip()
                elif text.endswith("MALADIE"):
                    status_to_save = "Maladie"
                    text = text.replace("MALADIE", "").strip()
                elif text.endswith(" R"):
                    status_to_save = "Rupture"
                    text = text[:-2].strip()
                elif text.endswith(" M"):
                    status_to_save = "Maladie"
                    text = text[:-2].strip()

                text_fmt = text.replace('-', '/').replace('.', '/')
                try:
                    parsed_date = datetime.strptime(text_fmt, "%d/%m/%Y").date()
                except ValueError:
                    try: parsed_date = datetime.strptime(text_fmt, "%d/%m/%y").date()
                    except ValueError: pass
            
            if not parsed_date:
                QMessageBox.warning(self, "Erreur", "Format invalide.\n- JJ/MM/AA\n- T (Aujourd'hui)\n- N (HB0 Naissance)\n- R (Rupture)\n- M (Maladie)")
                widget.setFocus()
                widget.selectAll()
                return 
            
            # --- NEW: Phase 1 Input Validation (No Future Dates) ---
            if parsed_date > datetime.now().date():
                QMessageBox.warning(self, "Erreur de Saisie", "Action refusée : Impossible de valider un vaccin dans le futur.")
                widget.setFocus()
                widget.selectAll()
                return
            # -------------------------------------------------------
            selected_date = parsed_date.strftime("%Y-%m-%d")
            if current_status != status_to_save or given_str != selected_date:
                needs_update = True

        if not needs_update:
            next_w = self.table.cellWidget(next_row, 2)
            if next_w:
                next_w.setFocus()
                next_w.selectAll()
            return

        if status_to_save == "Rupture":
            if is_group: self.engine.mark_milestone_rupture(self.current_patient_id, milestone, parsed_date.strftime("%d/%m/%Y"))
            else: self.engine.mark_rupture(self.current_patient_id, milestone, vax_name, parsed_date.strftime("%d/%m/%Y"))
        elif status_to_save == "Maladie":
            if is_group: self.engine.mark_milestone_maladie(self.current_patient_id, milestone, parsed_date.strftime("%d/%m/%Y"))
            else: self.engine.mark_maladie(self.current_patient_id, milestone, vax_name, parsed_date.strftime("%d/%m/%Y"))
        else:
            if is_group:
                if not text:
                    self.engine.cancel_milestone(self.current_patient_id, milestone)
                else:
                    self.engine.update_milestone_status(self.current_patient_id, milestone, status_to_save, selected_date)
                    if milestone in self.collapsed_groups:
                        self.collapsed_groups.remove(milestone)
            else:
                if not text:
                    self.engine.cancel_vaccine(self.current_patient_id, milestone, vax_name)
                else:
                    self.engine.update_vax_status(self.current_patient_id, milestone, vax_name, status_to_save, selected_date)
            
        self.engine.recalculate_schedule(self.current_patient_id, self.settings["center_schedule"])
        
        self.pending_focus_row = next_row
        self.load_table_data(self.current_patient_id)

    def edit_patient(self):
        if not self.current_patient_id: return
        p_data = self.engine.get_patient(self.current_patient_id)
        
        if p_data:
            dialog = EditPatientDialog(self, p_data, self.settings["secteurs"])
            if dialog.exec():
                new_name = dialog.name_in.text()
                new_dob = dialog.parsed_dob
                new_sexe = dialog.sexe_in.currentText()
                new_address = dialog.address_in.currentText()
                new_parent = dialog.parent_in.text()
                new_phone = dialog.phone_in.text()
                new_allergies = dialog.allergies_in.text()
                new_email = dialog.email_in.text()
                
                self.engine.update_patient(self.current_patient_id, new_name, new_dob, new_sexe, new_address, new_parent, new_phone, new_allergies, new_email, self.settings["center_schedule"])
                self.search_input.setText(self.current_patient_id)
                self.handle_search()

    def generate_report(self):
        if not self.current_patient_id: return
        p_data = self.engine.get_patient(self.current_patient_id)
        dob_str = p_data[2]
        records = self.engine.get_records(self.current_patient_id)
        
        dob_fmt = datetime.strptime(dob_str, "%Y-%m-%d").strftime("%d/%m/%Y")
        
        # --- HTML REPORT GENERATION (Phase 1 PNI Format) ---
        html_report = f"""
        <html>
        <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 11pt; color: #333; }}
            .header {{ text-align: center; border-bottom: 2px solid #27ae60; padding-bottom: 10px; margin-bottom: 20px; }}
            .msh-logo {{ font-size: 14pt; font-weight: bold; color: #2c3e50; }}
            .pni-title {{ font-size: 18pt; color: #27ae60; margin: 5px 0; font-weight: bold; text-transform: uppercase; }}
            .subtitle {{ color: #7f8c8d; font-size: 10pt; }}
            h2 {{ font-size: 14pt; color: #2c3e50; background-color: #ecf0f1; padding: 5px; border-left: 4px solid #2980b9; margin-top: 20px; }}
            table {{ width: 100%; font-size: 11pt; border-collapse: collapse; margin-top: 10px; }}
            th {{ background-color: #ecf0f1; text-align: left; padding: 8px; border: 1px solid #bdc3c7; }}
            td {{ padding: 8px; border: 1px solid #bdc3c7; }}
            .vax-table th {{ background-color: #2980b9; color: white; }}
            .alert {{ color: #c0392b; font-weight: bold; font-size: 11pt; margin-top: 10px; padding: 5px; border: 1px dashed #c0392b; display: inline-block; }}
            .done {{ color: #27ae60; font-weight: bold; }}
            .pending {{ color: #7f8c8d; font-style: italic; }}
            .rupture {{ color: #c0392b; font-weight: bold; }}
        </style>
        </head>
        <body>
            <div class="header">
                <div class="msh-logo">Royaume du Maroc - Ministère de la Santé et de la Protection Sociale</div>
                <div class="pni-title">Programme National d'Immunisation (PNI)</div>
                <div class="subtitle">Extrait Officiel du Registre Numérique | Édité le : {datetime.now().strftime('%d/%m/%Y à %H:%M')}</div>
            </div>
            
            <h2>INFORMATIONS DE L'ENFANT</h2>
            <table>
                <tr>
                    <th>Dossier N°</th><td>{p_data[0]}</td>
                    <th>Secteur / CSCA</th><td>{p_data[4]}</td>
                </tr>
                <tr>
                    <th>Nom Complet</th><td><b>{p_data[1]}</b></td>
                    <th>Date de Naissance</th><td>{dob_fmt}</td>
                </tr>
                <tr>
                    <th>Sexe</th><td>{p_data[3]}</td>
                    <th>Téléphone (Parent)</th><td>{p_data[6] if len(p_data)>6 else 'Non renseigné'}</td>
                </tr>
            </table>
        """
        
        if len(p_data) > 7 and p_data[7]:
            html_report += f"<div class='alert'>⚠️ ALLERGIES / NOTES MÉDICALES : {p_data[7]}</div>"
            
        html_report += """
            <h2>CALENDRIER VACCINAL</h2>
            <table class="vax-table">
                <tr>
                    <th>Âge / Palier</th>
                    <th>Vaccin</th>
                    <th>Date Prévue</th>
                    <th>Statut / Date d'Administration</th>
                </tr>
        """

        # --- RAW TEXT GENERATION (For TXT Export) ---
        raw_text = f"RAPPORT DE VACCINATION (PNI MAROC)\nGénéré le : {datetime.now().strftime('%d/%m/%Y à %H:%M')}\n{'='*50}\n"
        raw_text += f"INFORMATIONS PATIENT\n{'-'*50}\nDossier N° : {p_data[0]}\nNom : {p_data[1]}\nDate Naissance : {dob_fmt}\nSexe : {p_data[3]}\nSecteur : {p_data[4]}\n"
        if len(p_data) > 7 and p_data[7]: raw_text += f"ALLERGIES / NOTES : {p_data[7]}\n"
        raw_text += f"\n{'='*50}\nCALENDRIER VACCINAL\n"

        # --- LOOP THROUGH RECORDS TO BUILD BOTH HTML AND TXT ---
        for milestone, vax_name, due, status, given, obs in records:
            due_fmt = datetime.strptime(due, "%Y-%m-%d").strftime("%d/%m/%Y")
            
            # HTML Row Start
            html_report += f"<tr><td><b>{milestone.upper()}</b></td><td>{vax_name}</td><td>{due_fmt}</td>"
            
            # Raw Text Row Start
            raw_text_line = f"[{milestone.upper()}] {vax_name:<15} | Prévu: {due_fmt} | "

            if status in ["Done", "Externe"]:
                given_fmt = datetime.strptime(given, "%Y-%m-%d").strftime("%d/%m/%Y")
                tag_html = " (Maternité)" if (status == "Externe" and given == dob_str) else (" (Externe)" if status == "Externe" else "")
                tag_raw = " (Mat.)" if (status == "Externe" and given == dob_str) else (" (Ext.)" if status == "Externe" else "")
                
                html_report += f"<td class='done'>✅ Fait le {given_fmt}{tag_html}</td></tr>"
                raw_text += raw_text_line + f"✅ Fait le {given_fmt}{tag_raw}\n"
                
            elif status == "Rupture":
                html_report += f"<td class='rupture'>❌ Rupture de stock ({obs})</td></tr>"
                raw_text += raw_text_line + f"❌ Rupture de stock ({obs})\n"
                
            elif status == "Maladie":
                html_report += f"<td style='color: #d35400;'>🤒 Reporté maladie ({obs})</td></tr>"
                raw_text += raw_text_line + f"🤒 Reporté maladie ({obs})\n"
                
            else:
                html_report += f"<td class='pending'>⏳ En attente</td></tr>"
                raw_text += raw_text_line + f"⏳ En attente\n"
                
        html_report += "</table></body></html>"

        dialog = ReportDialog(self, html_report, raw_text, p_data[1])
        dialog.exec()
