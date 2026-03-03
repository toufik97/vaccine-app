from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QComboBox, QLineEdit, QCheckBox, QPushButton, QTabWidget, QMessageBox
from PyQt6.QtCore import Qt
from ui.dialogs.vaccine_manager import VaccineManagerDialog

class SettingsDialog(QDialog):
    def __init__(self, parent, current_settings):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Paramètres & Planning")
        self.setMinimumSize(600, 400)
        
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
        
        layout_gen.addWidget(QLabel("<b>Détails de l'Etablissement :</b>"))
        self.center_name_input = QLineEdit()
        self.center_name_input.setPlaceholderText("Nom du Centre de Santé")
        self.center_name_input.setText(current_settings.get("center_name", ""))
        layout_gen.addWidget(self.center_name_input)
        
        self.center_type_combo = QComboBox()
        self.center_type_combo.addItems(["Urbain", "Rural"])
        self.center_type_combo.setCurrentText(current_settings.get("center_type", "Urbain"))
        layout_gen.addWidget(self.center_type_combo)
        layout_gen.addSpacing(10)

        layout_gen.addWidget(QLabel("<b>Vos Localités :</b>\n(Séparez par des virgules)"))
        self.sectors_input = QLineEdit()
        self.sectors_input.setText(", ".join(current_settings.get("secteurs", [])))
        layout_gen.addWidget(self.sectors_input)
        layout_gen.addSpacing(10)
        
        layout_gen.addWidget(QLabel("<b>Protocole Pneumo (PCV) Actif :</b>"))
        self.pneumo_combo = QComboBox()
        self.pneumo_combo.addItems(["Old (3 Doses: 2, 4, 11 mois)", "New (4 Doses: 2, 4, 11, 13 mois avec décalage de 14j)"])
        
        saved_mode = current_settings.get("pneumo_mode", "Old")
        if saved_mode == "New":
            self.pneumo_combo.setCurrentIndex(1)
        else:
            self.pneumo_combo.setCurrentIndex(0)
            
        layout_gen.addWidget(self.pneumo_combo)
        layout_gen.addSpacing(10)
        
        self.future_dates_cb = QCheckBox("Autoriser la validation des dates dans le futur (Mode Test)")
        self.future_dates_cb.setChecked(current_settings.get("allow_future_dates", False))
        layout_gen.addWidget(self.future_dates_cb)
        
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
        self.vax_combo.addItem("Rappel DTC1", "Rappel DTC1")
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

        # --- ONGLET 3 : PROTOCOLES (ADMIN) ---
        self.tab_admin = QWidget()
        layout_admin = QVBoxLayout(self.tab_admin)
        
        warn_lbl = QLabel("<b>⚠️ Zone Sensible : Configuration du Calendrier Vaccinal</b><br>"
                          "<i>Note : Cette section sera bientôt restreinte par mot de passe (Admin/Infirmier Chef).</i>")
        warn_lbl.setStyleSheet("color: #e74c3c; font-size: 13px;")
        layout_admin.addWidget(warn_lbl)
        layout_admin.addSpacing(10)
        
        desc_lbl = QLabel("Le calendrier vaccinal est géré par le fichier <b>protocols.json</b>. "
                          "Si le Ministère de la Santé met à jour le PNI (ex: ajout d'une dose), vous pouvez modifier ce fichier.")
        desc_lbl.setWordWrap(True)
        layout_admin.addWidget(desc_lbl)
        
        btn_open = QPushButton("💉 Ouvrir le Gestionnaire de Vaccins")
        btn_open.setStyleSheet("background-color: #34495e; color: white; padding: 8px; font-weight: bold;")
        btn_open.clicked.connect(self.open_vaccine_manager)
        layout_admin.addWidget(btn_open)
        
        btn_reload = QPushButton("🔄 Recharger les protocoles en mémoire")
        btn_reload.setStyleSheet("background-color: #2980b9; color: white; padding: 8px; font-weight: bold;")
        btn_reload.clicked.connect(self.reload_protocols)
        layout_admin.addWidget(btn_reload)
        layout_admin.addStretch()
        
        self.tabs.addTab(self.tab_gen, "🛠️ Général")
        self.tabs.addTab(self.tab_plan, "📆 Planning du Centre")
        self.tabs.addTab(self.tab_admin, "🔐 Protocoles (Admin)")
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

    # --- ORIGINAL HELPER METHODS ---
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
            "center_name": self.center_name_input.text().strip(),
            "center_type": self.center_type_combo.currentText(),
            "dark_mode": self.theme_combo.currentText() == "Mode Sombre",
            "fold_by_default": self.fold_combo.currentText() == "Groupes pliés (Vue condensée)",
            "secteurs": sects,
            "center_schedule": self.current_schedule,
            "pneumo_mode": "New" if self.pneumo_combo.currentIndex() == 1 else "Old",
            "allow_future_dates": self.future_dates_cb.isChecked()
        }

    def open_vaccine_manager(self):
        manager = VaccineManagerDialog(self)
        manager.exec()

    def reload_protocols(self):
        try:
            self.parent().engine.load_protocols()
            QMessageBox.information(self, "Succès", "Protocoles rechargés avec succès !\nTous les nouveaux dossiers utiliseront ce calendrier.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur Critique", f"Erreur lors du rechargement. Vérifiez la syntaxe de votre fichier JSON.\n\nDétail: {e}")
