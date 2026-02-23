import sys
import json
import os
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTableWidget, QTableWidgetItem, QLabel, QLineEdit, 
                             QComboBox, QMessageBox, QHeaderView, QDialog, QTextEdit, QFileDialog, 
                             QScrollArea, QTabWidget, QCalendarWidget, QCheckBox)
from PyQt6.QtCore import QDate, Qt, pyqtSignal, QMarginsF
from PyQt6.QtGui import QColor, QFont, QPageLayout
from PyQt6.QtPrintSupport import QPrinter
from logic import VaxEngine

class SortItem(QTableWidgetItem):
    def __lt__(self, other):
        col = self.tableWidget().column(self)
        t1 = self.text().strip()
        t2 = other.text().strip()
        
        if col == 0:
            try:
                id1, y1 = map(int, t1.split('/'))
                id2, y2 = map(int, t2.split('/'))
                if y1 != y2: return y1 < y2
                return id1 < id2
            except:
                pass
        elif col == 2:
            try:
                d1 = datetime.strptime(t1, "%d/%m/%Y")
                d2 = datetime.strptime(t2, "%d/%m/%Y")
                return d1 < d2
            except:
                pass
        return t1.lower() < t2.lower()

class DateLineEdit(QLineEdit):
    navigationRequested = pyqtSignal(int, int)

    def __init__(self, row, parent=None):
        super().__init__(parent)
        self.row = row

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Up:
            self.navigationRequested.emit(self.row, -1)
        elif event.key() == Qt.Key.Key_Down:
            self.navigationRequested.emit(self.row, 1)
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.navigationRequested.emit(self.row, 1)
        else:
            super().keyPressEvent(event)

class GrowthDialog(QDialog):
    def __init__(self, parent, engine, p_id, p_name):
        super().__init__(parent)
        self.engine = engine
        self.p_id = p_id
        self.setWindowTitle(f"⚖️ Constantes & Croissance - {p_name}")
        self.setMinimumSize(700, 450)
        
        layout = QVBoxLayout(self)
        
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Date", "Poids (kg)", "Taille (cm)", "IMC"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        
        layout.addWidget(QLabel("<b>Nouvelle prise de constantes :</b>"))
        form_layout = QHBoxLayout()
        
        self.date_in = QLineEdit()
        self.date_in.setPlaceholderText("JJ/MM/AA")
        self.date_in.setText(datetime.now().strftime("%d/%m/%Y"))
        self.date_in.setFixedWidth(80)
        
        self.weight_in = QLineEdit()
        self.weight_in.setPlaceholderText("Ex: 5.5")
        
        self.height_in = QLineEdit()
        self.height_in.setPlaceholderText("Ex: 60")
        
        add_btn = QPushButton("➕ Ajouter")
        add_btn.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold;")
        add_btn.clicked.connect(self.add_record)
        
        form_layout.addWidget(QLabel("Date:"))
        form_layout.addWidget(self.date_in)
        form_layout.addWidget(QLabel("Poids (kg):"))
        form_layout.addWidget(self.weight_in)
        form_layout.addWidget(QLabel("Taille (cm):"))
        form_layout.addWidget(self.height_in)
        form_layout.addWidget(add_btn)
        
        layout.addLayout(form_layout)
        
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.load_data()
        
    def load_data(self):
        self.table.setRowCount(0)
        records = self.engine.get_visits(self.p_id)
        
        def get_interpretation(metric, z):
            if z is None: return ""
            if metric == "Poids":
                if z < -3: return "Insuffisance sévère"
                elif z < -2: return "Insuffisance pondérale"
                elif z > 2: return "Poids élevé"
                else: return "Normal"
            elif metric == "Taille":
                if z < -3: return "Retard sévère"
                elif z < -2: return "Retard de croissance"
                elif z > 3: return "Très grande taille"
                elif z > 2: return "Grande taille"
                else: return "Normal"
            elif metric == "IMC":
                if z < -3: return "Malnutrition sévère"
                elif z < -2: return "Malnutrition"
                elif z > 3: return "Obésité"
                elif z > 2: return "Surpoids"
                elif z > 1: return "Risque surpoids"
                else: return "Normal"
            return ""

        def format_and_color_item(value, unit, z, metric):
            if z is None:
                return QTableWidgetItem(f"{value} {unit}")
                
            interp = get_interpretation(metric, z)
            text = f"{value} {unit} (Z: {z} | {interp})"
            item = QTableWidgetItem(text)
            
            color_severe = {"bg": "#f2d7d5", "text": "#922b21"} 
            color_alert  = {"bg": "#fbd0c9", "text": "#c0392b"} 
            color_warn   = {"bg": "#fcf3cf", "text": "#d35400"} 
            color_normal = {"bg": "#d5f5e3", "text": "#1e8449"} 
            
            c = color_normal
            
            if metric == "IMC":
                if z < -3 or z > 3: c = color_severe
                elif z < -2 or z > 2: c = color_alert
                elif z < -1 or z > 1: c = color_warn 
            elif metric == "Taille":
                if z < -3 or z > 3: c = color_severe
                elif z < -2 or z > 2: c = color_alert
                elif z < -1: c = color_warn 
            elif metric == "Poids":
                if z < -3: c = color_severe
                elif z < -2 or z > 2: c = color_alert
                elif z < -1: c = color_warn

            item.setBackground(QColor(c["bg"]))
            item.setForeground(QColor(c["text"]))
            
            if c == color_severe:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                
            return item

        for i, r in enumerate(records):
            self.table.insertRow(i)
            visit_date_str = r[0]
            weight = r[1]
            height = r[2]
            imc = r[3]
            
            date_fmt = datetime.strptime(visit_date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
            z_w, z_h, z_i = self.engine.get_visit_zscores(self.p_id, visit_date_str, weight, height, imc)
            
            w_item = format_and_color_item(weight, "kg", z_w, "Poids")
            h_item = format_and_color_item(height, "cm", z_h, "Taille")
            i_item = format_and_color_item(imc, "", z_i, "IMC")
            
            self.table.setItem(i, 0, QTableWidgetItem(date_fmt))
            self.table.setItem(i, 1, w_item)
            self.table.setItem(i, 2, h_item)
            self.table.setItem(i, 3, i_item)
            
    def add_record(self):
        text = self.date_in.text().strip().replace('-', '/').replace('.', '/')
        try:
            parsed_date = datetime.strptime(text, "%d/%m/%Y").date()
        except ValueError:
            try: parsed_date = datetime.strptime(text, "%d/%m/%y").date()
            except ValueError:
                QMessageBox.warning(self, "Erreur", "Format de date invalide.")
                return
        
        # --- NEW: Phase 1 Input Validation ---
        if parsed_date > datetime.now().date():
            QMessageBox.warning(self, "Erreur", "La date de la visite ne peut pas être dans le futur.")
            return
        # -------------------------------------
        try:
            w = float(self.weight_in.text().replace(',', '.'))
            h = float(self.height_in.text().replace(',', '.'))
            if w <= 0 or h <= 0: raise ValueError
                
            imc = round(w / ((h / 100) ** 2), 2)
            date_str = parsed_date.strftime("%Y-%m-%d")
            
            self.engine.add_visit(self.p_id, date_str, w, h, imc)
            self.weight_in.clear()
            self.height_in.clear()
            self.load_data()
        except ValueError:
            QMessageBox.warning(self, "Erreur", "Poids et taille doivent être numériques et supérieurs à 0.")

class HelpDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("❔ Guide d'utilisation")
        self.setMinimumSize(600, 550)
        layout = QVBoxLayout(self)
        
        help_text = """
        <h2 style="color: #2980b9;">Guide Rapide - Vaccine Tracker Pro</h2>
        <h3>🔍 Recherche Intelligente</h3>
        <ul>
            <li><b>Recherche par Nom/ID :</b> Tapez le nom pour trouver le dossier.</li>
            <li><b>Recherche par Date :</b> Tapez une date (ex: <code>21/02/26</code>). L'application affichera tous les enfants vaccinés ce jour-là !</li>
        </ul>
        <h3>🎨 Codes Couleurs</h3>
        <ul>
            <li><span style="background-color: #d4edda; color: #1b5e20; padding: 2px 5px; border-radius: 3px;"><b>🟢 VERT</b></span> : Administré / validé.</li>
            <li><span style="background-color: #fff3cd; color: #e65100; padding: 2px 5px; border-radius: 3px;"><b>🟡 JAUNE</b></span> : Prévu pour Aujourd'hui.</li>
            <li><span style="background-color: #f8d7da; color: #b71c1c; padding: 2px 5px; border-radius: 3px;"><b>🔴 ROUGE</b></span> : En retard.</li>
            <li><span style="background-color: #d2b4de; color: #4a235a; padding: 2px 5px; border-radius: 3px;"><b>🟣 VIOLET</b></span> : Rupture de Stock.</li>
            <li><span style="background-color: #fdebd0; color: #d35400; padding: 2px 5px; border-radius: 3px;"><b>🟠 ORANGE</b></span> : Maladie / Fièvre.</li>
        </ul>
        <h3>⌨️ Raccourcis Super-Rapides</h3>
        <ul>
            <li><b>'T' :</b> Aujourd'hui.</li>
            <li><b>'TE' :</b> Fait aujourd'hui en externe.</li>
            <li><b>'N' :</b> Naissance (HB Zéro).</li>
            <li><b>'R' :</b> Rupture de stock.</li>
            <li><b>'M' :</b> Maladie / Fièvre.</li>
        </ul>
        """
        text_area = QTextEdit()
        text_area.setHtml(help_text)
        text_area.setReadOnly(True)
        text_area.setStyleSheet("font-size: 13px; font-family: Arial, sans-serif;")
        layout.addWidget(text_area)
        
        close_btn = QPushButton("J'ai compris")
        close_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 8px; font-weight: bold;")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

class SettingsDialog(QDialog):
    def __init__(self, parent, current_settings):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Paramètres & Planning")
        self.setMinimumSize(550, 350)
        
        self.current_schedule = current_settings.get("center_schedule", {"default": [0, 1, 2, 3, 4]}).copy()
        
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        
        # --- ONGLET 1 : GÉNÉRAL ---
        self.tab_gen = QWidget()
        layout_gen = QVBoxLayout(self.tab_gen)
        
        layout_gen.addWidget(QLabel("<b>Thème de l'application :</b>"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Mode Sombre", "Mode Clair"])
        self.theme_combo.setCurrentText("Mode Sombre" if current_settings.get("dark_mode", True) else "Mode Clair")
        layout_gen.addWidget(self.theme_combo)
        layout_gen.addSpacing(10)
        
        layout_gen.addWidget(QLabel("<b>Affichage des vaccins :</b>"))
        self.fold_combo = QComboBox()
        self.fold_combo.addItems(["Groupes pliés (Vue condensée)", "Groupes ouverts (Vue détaillée)"])
        self.fold_combo.setCurrentText("Groupes pliés (Vue condensée)" if current_settings.get("fold_by_default", True) else "Groupes ouverts (Vue détaillée)")
        layout_gen.addWidget(self.fold_combo)
        layout_gen.addSpacing(10)
        
        layout_gen.addWidget(QLabel("<b>Vos Secteurs / Adresses :</b>\n(Séparez par des virgules)"))
        self.sectors_input = QLineEdit()
        self.sectors_input.setText(", ".join(current_settings.get("secteurs", [])))
        layout_gen.addWidget(self.sectors_input)
        layout_gen.addStretch()
        
        # --- ONGLET 2 : PLANNING DU CENTRE ---
        self.tab_plan = QWidget()
        layout_plan = QVBoxLayout(self.tab_plan)
        
        layout_plan.addWidget(QLabel("<b>📅 Jours d'administration des vaccins</b>"))
        layout_plan.addWidget(QLabel("Sélectionnez un vaccin pour configurer ses jours spécifiques.\n(0 = Lundi, 6 = Dimanche)"))
        
        self.vax_combo = QComboBox()
        self.vax_combo.addItem("📍 Règle Générale (Tous les vaccins)", "default")
        self.vax_combo.addItem("Vaccin BCG", "BCG")
        self.vax_combo.addItem("Vaccin RR1", "RR1")
        self.vax_combo.addItem("Rappel DTC", "Rappel DTC")
        self.vax_combo.currentIndexChanged.connect(self.load_days_for_vax)
        layout_plan.addWidget(self.vax_combo)
        
        self.day_cbs = []
        days_names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
        days_layout = QHBoxLayout()
        for i, d in enumerate(days_names):
            cb = QCheckBox(d)
            cb.stateChanged.connect(self.save_days_for_vax)
            self.day_cbs.append(cb)
            days_layout.addWidget(cb)
            
        layout_plan.addLayout(days_layout)
        layout_plan.addStretch()
        
        self.tabs.addTab(self.tab_gen, "🛠️ Général")
        self.tabs.addTab(self.tab_plan, "📆 Planning du Centre")
        layout.addWidget(self.tabs)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Enregistrer")
        save_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 8px; font-weight: bold;")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self.load_days_for_vax()
        
    def load_days_for_vax(self):
        vax_key = self.vax_combo.currentData()
        active_days = self.current_schedule.get(vax_key, self.current_schedule.get("default", [0, 1, 2, 3, 4]))
        for i, cb in enumerate(self.day_cbs):
            cb.blockSignals(True)
            cb.setChecked(i in active_days)
            cb.blockSignals(False)

    def save_days_for_vax(self):
        vax_key = self.vax_combo.currentData()
        active_days = [i for i, cb in enumerate(self.day_cbs) if cb.isChecked()]
        if not active_days:
            QMessageBox.warning(self, "Attention", "Vous devez sélectionner au moins un jour.")
            self.load_days_for_vax()
            return
        self.current_schedule[vax_key] = active_days

    def get_new_settings(self):
        sects = [s.strip() for s in self.sectors_input.text().split(",") if s.strip()]
        if not sects: sects = ["Secteur A"] 
        return {
            "dark_mode": self.theme_combo.currentText() == "Mode Sombre",
            "fold_by_default": self.fold_combo.currentText() == "Groupes pliés (Vue condensée)",
            "secteurs": sects,
            "center_schedule": self.current_schedule
        }

class AllPatientsDialog(QDialog):
    def __init__(self, parent, patients_data, secteurs, engine=None, title="Tous les Dossiers Enregistrés"):
        super().__init__(parent)
        self.engine = engine
        self.setWindowTitle(title)
        self.setMinimumSize(1050, 500)
        self.selected_id = None
        
        layout = QVBoxLayout(self)
        filter_layout = QHBoxLayout()
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Rechercher par Nom, ID, ou Date de vaccin (ex: 21/02/26)...")
        self.search_bar.textChanged.connect(self.filter_table)
        
        self.sector_filter = QComboBox()
        self.sector_filter.addItem("Tous les secteurs")
        self.sector_filter.addItems(secteurs)
        self.sector_filter.currentTextChanged.connect(self.filter_table)

        self.sexe_filter = QComboBox()
        self.sexe_filter.addItems(["Tous les sexes", "Masculin", "Féminin"])
        self.sexe_filter.currentTextChanged.connect(self.filter_table)
        
        filter_layout.addWidget(self.search_bar, 3)
        filter_layout.addWidget(QLabel("Secteur :"))
        filter_layout.addWidget(self.sector_filter, 1)
        filter_layout.addWidget(QLabel("Sexe :"))
        filter_layout.addWidget(self.sexe_filter, 1)
        layout.addLayout(filter_layout)
        
        self.table = QTableWidget(0, 7) 
        self.table.setHorizontalHeaderLabels(["ID", "Nom complet", "Date Naissance", "Sexe", "Secteur", "Téléphone", "Vaccin(s) du Jour"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        for i, p in enumerate(patients_data):
            self.table.insertRow(i)
            self.table.setItem(i, 0, SortItem(str(p[0])))
            self.table.setItem(i, 1, SortItem(str(p[1])))
            dob_fmt = datetime.strptime(p[2], "%Y-%m-%d").strftime("%d/%m/%Y")
            self.table.setItem(i, 2, SortItem(dob_fmt))
            self.table.setItem(i, 3, SortItem(str(p[3])))
            self.table.setItem(i, 4, SortItem(str(p[4])))
            self.table.setItem(i, 5, SortItem(str(p[6]) if len(p)>6 else ""))
            
            vax_data = str(p[9]) if len(p) > 9 else ""
            self.table.setItem(i, 6, SortItem(vax_data))
            
        self.table.setSortingEnabled(True)
        self.table.cellDoubleClicked.connect(self.on_double_click)
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        open_btn = QPushButton("📂 Ouvrir le dossier")
        open_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 8px; font-weight: bold;")
        open_btn.clicked.connect(self.on_open_clicked)
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(open_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def filter_table(self):
        search_text = self.search_bar.text().lower().strip()
        sector_text = self.sector_filter.currentText()
        sexe_text = self.sexe_filter.currentText()
        
        valid_date_data = None
        
        if search_text and self.engine:
            text_fmt = search_text.replace('-', '/').replace('.', '/')
            try:
                parsed = datetime.strptime(text_fmt, "%d/%m/%Y").date()
                date_str = parsed.strftime("%Y-%m-%d")
                res = self.engine.search_by_vaccine_date(date_str)
                valid_date_data = {str(p[0]): str(p[9]) for p in res if len(p) > 9}
            except ValueError:
                try: 
                    parsed = datetime.strptime(text_fmt, "%d/%m/%y").date()
                    date_str = parsed.strftime("%Y-%m-%d")
                    res = self.engine.search_by_vaccine_date(date_str)
                    valid_date_data = {str(p[0]): str(p[9]) for p in res if len(p) > 9}
                except ValueError:
                    pass

        for row in range(self.table.rowCount()):
            item_id = self.table.item(row, 0).text()
            item_sector = self.table.item(row, 4).text()
            item_sexe = self.table.item(row, 3).text()
            
            match_sector = (sector_text == "Tous les secteurs" or item_sector == sector_text)
            match_sexe = (sexe_text == "Tous les sexes" or item_sexe == sexe_text)
            match_search = False
            
            if not search_text:
                match_search = True
            elif valid_date_data is not None:
                if item_id in valid_date_data:
                    match_search = True
                    self.table.item(row, 6).setText(valid_date_data[item_id])
                else:
                    self.table.item(row, 6).setText("")
            else:
                self.table.item(row, 6).setText("")
                for col in range(6): 
                    item = self.table.item(row, col)
                    if item and search_text in item.text().lower():
                        match_search = True
                        break
                        
            self.table.setRowHidden(row, not (match_search and match_sector and match_sexe))
        
    def on_double_click(self, row, col):
        self.selected_id = self.table.item(row, 0).text()
        self.accept()
        
    def on_open_clicked(self):
        curr_row = self.table.currentRow()
        if curr_row >= 0:
            self.selected_id = self.table.item(curr_row, 0).text()
            self.accept()
        else:
            QMessageBox.warning(self, "Attention", "Sélectionnez un dossier.")

class EditPatientDialog(QDialog):
    def __init__(self, parent, patient_data, secteurs):
        super().__init__(parent)
        self.setWindowTitle("Modifier le Dossier")
        
        self.p_id = patient_data[0]
        self.name = patient_data[1]
        self.dob_str = patient_data[2]
        self.sexe = patient_data[3]
        self.address = patient_data[4]
        self.parent_name = patient_data[5] if len(patient_data) > 5 else ""
        self.phone = patient_data[6] if len(patient_data) > 6 else ""
        self.allergies = patient_data[7] if len(patient_data) > 7 else ""
        self.email = patient_data[8] if len(patient_data) > 8 else ""
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("<b>INFORMATIONS OBLIGATOIRES</b>"))
        layout.addWidget(QLabel("Nom de l'enfant :"))
        self.name_in = QLineEdit(self.name)
        layout.addWidget(self.name_in)
        
        h_layout1 = QHBoxLayout()
        self.sexe_in = QComboBox()
        self.sexe_in.addItems(["Masculin", "Féminin"])
        self.sexe_in.setCurrentText(self.sexe)
        h_layout1.addWidget(QLabel("Sexe :"))
        h_layout1.addWidget(self.sexe_in)
        
        self.address_in = QComboBox()
        self.address_in.addItems(secteurs)
        self.address_in.setCurrentText(self.address)
        h_layout1.addWidget(QLabel("Secteur :"))
        h_layout1.addWidget(self.address_in)
        layout.addLayout(h_layout1)
        
        layout.addWidget(QLabel("Date de Naissance :"))
        self.date_in = QLineEdit()
        self.date_in.setPlaceholderText("JJ/MM/AA")
        self.date_in.setText(datetime.strptime(self.dob_str, "%Y-%m-%d").strftime("%d/%m/%Y"))
        layout.addWidget(self.date_in)
        
        layout.addSpacing(10)
        layout.addWidget(QLabel("<b>INFORMATIONS FACULTATIVES</b>"))
        
        layout.addWidget(QLabel("Nom du parent / tuteur :"))
        self.parent_in = QLineEdit(self.parent_name)
        layout.addWidget(self.parent_in)
        
        layout.addWidget(QLabel("Téléphone :"))
        self.phone_in = QLineEdit(self.phone)
        layout.addWidget(self.phone_in)
        
        layout.addWidget(QLabel("Email :"))
        self.email_in = QLineEdit(self.email)
        layout.addWidget(self.email_in)
        
        layout.addWidget(QLabel("Allergies / Notes :"))
        self.allergies_in = QLineEdit(self.allergies)
        layout.addWidget(self.allergies_in)
        
        self.parsed_dob = None
        
        btn = QPushButton("Sauvegarder")
        btn.clicked.connect(self.validate_and_accept)
        layout.addWidget(btn)

    def validate_and_accept(self):
        if not self.name_in.text().strip():
            QMessageBox.warning(self, "Erreur", "Le nom de l'enfant est obligatoire.")
            self.name_in.setFocus()
            return
        text = self.date_in.text().strip().replace('-', '/').replace('.', '/')
        try:
            self.parsed_dob = datetime.strptime(text, "%d/%m/%Y").date()
        except ValueError:
            try:
                self.parsed_dob = datetime.strptime(text, "%d/%m/%y").date()
            except ValueError:
                QMessageBox.warning(self, "Erreur", "Format de date invalide.")
                self.date_in.setFocus()
                return
        self.accept()

class ReportDialog(QDialog):
    def __init__(self, parent, html_report, raw_text, patient_name):
        super().__init__(parent)
        self.setWindowTitle(f"Rapport de Session - {patient_name}")
        self.setMinimumSize(600, 700)
        self.html_report = html_report
        self.raw_text = raw_text
        self.patient_name = patient_name
        
        layout = QVBoxLayout(self)
        self.text_area = QTextEdit()
        self.text_area.setHtml(html_report) 
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)
        
        btn_layout = QHBoxLayout()
        
        export_txt_btn = QPushButton("💾 Exporter en TXT")
        export_txt_btn.clicked.connect(self.export_txt)
        
        export_pdf_btn = QPushButton("📄 Exporter en PDF")
        export_pdf_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 8px; font-weight: bold;")
        export_pdf_btn.clicked.connect(self.export_pdf)
        
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(export_txt_btn)
        btn_layout.addWidget(export_pdf_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
    def export_txt(self):
        safe_name = self.patient_name.replace(' ', '_')
        default_name = f"Rapport_{safe_name}.txt"
        file_path, _ = QFileDialog.getSaveFileName(self, "Sauvegarder en TXT", default_name, "Text Files (*.txt)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.raw_text)
                QMessageBox.information(self, "Succès", "Rapport TXT exporté avec succès.")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'exportation:\n{str(e)}")

    def export_pdf(self):
        safe_name = self.patient_name.replace(' ', '_')
        default_name = f"Rapport_{safe_name}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(self, "Sauvegarder en PDF", default_name, "PDF Files (*.pdf)")
        if file_path:
            try:
                printer = QPrinter(QPrinter.PrinterMode.HighResolution)
                printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
                printer.setOutputFileName(file_path)
                
                margins = QMarginsF(15.0, 15.0, 15.0, 15.0)
                printer.setPageMargins(margins, QPageLayout.Unit.Millimeter)
                
                self.text_area.document().print(printer)
                QMessageBox.information(self, "Succès", "Le rapport a été exporté en PDF avec succès ! 🚀")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Échec de l'exportation PDF:\n{str(e)}")

class DashboardDialog(QDialog):
    def __init__(self, parent, engine):
        super().__init__(parent)
        self.setWindowTitle("📊 Tableau de Bord des Statistiques")
        self.setMinimumSize(700, 500) 
        self.engine = engine
        
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        
        self.tab_daily = QWidget()
        daily_layout = QHBoxLayout(self.tab_daily)
        
        self.calendar = QCalendarWidget()
        self.calendar.selectionChanged.connect(self.update_daily)
        
        self.daily_table = QTableWidget(0, 2)
        self.daily_table.setHorizontalHeaderLabels(["Vaccin Administré", "Doses"])
        self.daily_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.daily_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        daily_layout.addWidget(self.calendar, 1)
        daily_layout.addWidget(self.daily_table, 1)
        
        self.tab_monthly = QWidget()
        monthly_layout = QVBoxLayout(self.tab_monthly)
        
        controls_layout = QHBoxLayout()
        self.month_combo = QComboBox()
        months = [("Janvier", "01"), ("Février", "02"), ("Mars", "03"), ("Avril", "04"), 
                  ("Mai", "05"), ("Juin", "06"), ("Juillet", "07"), ("Août", "08"),
                  ("Septembre", "09"), ("Octobre", "10"), ("Novembre", "11"), ("Décembre", "12")]
        for name, num in months:
            self.month_combo.addItem(name, num)
            
        self.year_combo = QComboBox()
        current_year = datetime.now().year
        self.year_combo.addItems([str(y) for y in range(2024, current_year + 5)])
        
        self.month_combo.setCurrentIndex(datetime.now().month - 1)
        self.year_combo.setCurrentText(str(current_year))
        
        self.month_combo.currentIndexChanged.connect(self.update_monthly)
        self.year_combo.currentIndexChanged.connect(self.update_monthly)
        
        controls_layout.addWidget(QLabel("<b>Mois :</b>"))
        controls_layout.addWidget(self.month_combo)
        controls_layout.addWidget(QLabel("<b>Année :</b>"))
        controls_layout.addWidget(self.year_combo)
        controls_layout.addStretch()
        
        self.monthly_table = QTableWidget(0, 3)
        self.monthly_table.setHorizontalHeaderLabels(["Vaccin Administré", "Total", "Détail des Dates (Jour/Mois)"])
        self.monthly_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.monthly_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.monthly_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.monthly_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        monthly_layout.addLayout(controls_layout)
        monthly_layout.addWidget(self.monthly_table)
        
        self.tabs.addTab(self.tab_daily, "📅 Statistiques Quotidiennes")
        self.tabs.addTab(self.tab_monthly, "📆 Statistiques Mensuelles")
        
        layout.addWidget(self.tabs)
        
        close_btn = QPushButton("Fermer le Tableau de Bord")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.update_daily()
        self.update_monthly()
        
    def update_daily(self):
        selected_date = self.calendar.selectedDate().toPyDate().strftime("%Y-%m-%d")
        stats = self.engine.get_daily_stats(selected_date)
        
        self.daily_table.setRowCount(len(stats))
        for i, (vax, count) in enumerate(stats):
            self.daily_table.setItem(i, 0, QTableWidgetItem(vax))
            self.daily_table.setItem(i, 1, QTableWidgetItem(str(count)))

    def update_monthly(self):
        month_num = self.month_combo.currentData()
        year_str = self.year_combo.currentText()
        query_str = f"{year_str}-{month_num}%"
        
        stats = self.engine.get_monthly_stats(query_str)
        
        self.monthly_table.setRowCount(len(stats))
        for i, (vax, count, dates_str) in enumerate(stats):
            self.monthly_table.setItem(i, 0, QTableWidgetItem(vax))
            count_item = QTableWidgetItem(str(count))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.monthly_table.setItem(i, 1, count_item)
            self.monthly_table.setItem(i, 2, QTableWidgetItem(dates_str))

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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = VaxApp()
    window.show()
    sys.exit(app.exec())