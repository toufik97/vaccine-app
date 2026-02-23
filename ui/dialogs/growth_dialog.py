from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QLineEdit, QPushButton, QHeaderView, QMessageBox
from PyQt6.QtGui import QColor, QFont
from datetime import datetime

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
