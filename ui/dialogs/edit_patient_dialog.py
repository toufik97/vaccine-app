from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QMessageBox
from datetime import datetime
from core.enums import Gender

class EditPatientDialog(QDialog):
    def __init__(self, parent, patient_data, secteurs):
        super().__init__(parent)
        self.setWindowTitle("Modifier le Dossier")
        
        self.p_id = patient_data[0]
        self.name = patient_data[1]
        self.dob_str = patient_data[2]
        self.sexe = Gender.to_ui(patient_data[3])
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
        h_layout1.addWidget(QLabel("Localité :"))
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

        layout.addSpacing(10)
        layout.addWidget(QLabel("<b>PROTOCOLES SPÉCIFIQUES</b>"))
        
        self.pneumo_in = QComboBox()
        self.pneumo_in.addItems(["Old", "New"])
        # We need the current patient's pneumo mode. We should pass it via patient_data or engine.
        # Since patient_data doesn't inherently include it in the generic fetch, we'll try to fetch or default
        try:
            current_mode = self.parent().engine.db.get_patient_pneumo_mode(self.p_id)
        except Exception:
            current_mode = "Old"
        self.pneumo_in.setCurrentText(current_mode)
        
        h_pneumo = QHBoxLayout()
        h_pneumo.addWidget(QLabel("Pneumocoque :"))
        h_pneumo.addWidget(self.pneumo_in)
        h_pneumo.addStretch()
        layout.addLayout(h_pneumo)
        
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
