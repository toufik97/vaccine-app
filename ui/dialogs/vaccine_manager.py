import json
import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, QLineEdit, 
                             QTextEdit, QSplitter, QTreeWidget, QTreeWidgetItem,
                             QMessageBox, QInputDialog, QComboBox, QSpinBox, QCheckBox,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QTabWidget, QFormLayout, QGroupBox)
from PyQt6.QtCore import Qt

class DoseFormDialog(QDialog):
    def __init__(self, parent=None, milestones=[], dose_data=None):
        super().__init__(parent)
        self.setWindowTitle("Éditer la Dose")
        self.dose_data = dose_data or {"id": "", "milestone": milestones[0] if milestones else "", "rules": {}}
        self.setup_ui(milestones)
        
    def setup_ui(self, milestones):
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # TAB 1: Essentiel
        tab_essential = QWidget()
        essential_layout = QVBoxLayout(tab_essential)
        
        group_id = QGroupBox("Identification")
        form_id = QFormLayout(group_id)
        
        self.id_input = QLineEdit(self.dose_data.get("id", ""))
        form_id.addRow("ID de la Dose (ex: VPO4) :", self.id_input)
        
        self.milestone_input = QComboBox()
        self.milestone_input.addItems(milestones)
        self.milestone_input.setCurrentText(self.dose_data.get("milestone", ""))
        form_id.addRow("Groupe d'âge (Milestone) :", self.milestone_input)
        
        rules = self.dose_data.get("rules", {})
        
        self.min_age_input = QSpinBox()
        self.min_age_input.setRange(0, 10000)
        self.min_age_input.setValue(rules.get("min_age_days", 0))
        form_id.addRow("Âge minimum absolu (jours) [0=aucun] :", self.min_age_input)
        
        self.offset_input = QSpinBox()
        self.offset_input.setRange(0, 10000)
        self.offset_input.setValue(rules.get("offset_from_milestone_days", 0))
        form_id.addRow("Décalage après milestone (jours) [0=aucun] :", self.offset_input)
        
        essential_layout.addWidget(group_id)
        
        group_admin = QGroupBox("Administration")
        form_admin = QFormLayout(group_admin)
        
        self.route_input = QComboBox()
        self.route_input.addItems(["IM", "SC", "ID", "Oral", ""])
        self.route_input.setCurrentText(rules.get("administration_route", ""))
        form_admin.addRow("Voie d'administration :", self.route_input)
        
        self.site_input = QComboBox()
        self.site_input.addItems(["Cuisse Droite (Antérolatérale)", "Cuisse Gauche (Antérolatérale)", "Deltoïde (IM)", "Deltoïde Gauche (Sous-cutanée)", "Intradermique (Bras Gauche)", "Oral", ""])
        self.site_input.setCurrentText(rules.get("default_injection_site", ""))
        form_admin.addRow("Site d'injection par défaut :", self.site_input)
        
        self.lifespan_input = QSpinBox()
        self.lifespan_input.setRange(0, 365)
        self.lifespan_input.setValue(rules.get("vial_lifespan_days", 0))
        form_admin.addRow("Durée de vie du flacon (jours) [0=unique] :", self.lifespan_input)
        
        essential_layout.addWidget(group_admin)
        essential_layout.addStretch()
        self.tabs.addTab(tab_essential, "Essentiel")
        
        # TAB 2: Règles Avancées
        tab_adv = QWidget()
        adv_layout = QVBoxLayout(tab_adv)
        
        adv_rules = {k: v for k, v in rules.items() if k not in ["min_age_days", "offset_from_milestone_days", "administration_route", "default_injection_site", "vial_lifespan_days"]}
        
        group_live = QGroupBox("Vaccin Vivant")
        form_live = QFormLayout(group_live)
        self.is_live_cb = QCheckBox("Vaccin Vivant Atténué")
        self.is_live_cb.setChecked(adv_rules.get("is_live", False))
        self.is_live_cb.setToolTip("Active la règle des 28 jours avec d'autres vaccins vivants.")
        form_live.addRow("", self.is_live_cb)
        
        self.live_conflict_exc_cb = QCheckBox("Exception au Conflit Vivant (ex: VPO)")
        self.live_conflict_exc_cb.setChecked(adv_rules.get("live_conflict_exception", False))
        form_live.addRow("", self.live_conflict_exc_cb)
        adv_layout.addWidget(group_live)
        
        group_deps = QGroupBox("Dépendances & Conflits")
        form_deps = QFormLayout(group_deps)
        
        self.dependencies_input = QLineEdit()
        self.dependencies_input.setPlaceholderText("ex: Penta1:28, VPO1:30")
        deps_str = ", ".join([f"{d['vaccine']}:{d['min_interval_days']}" for d in adv_rules.get("dependencies", [])])
        self.dependencies_input.setText(deps_str)
        form_deps.addRow("Dépendances :", self.dependencies_input)
        
        self.conflicts_input = QLineEdit()
        self.conflicts_input.setPlaceholderText("ex: RR,Amarile:28")
        conflicts_str = "; ".join([f"{','.join(c['vaccines'])}:{c['min_interval_days']}" for c in adv_rules.get("conflicts", [])])
        self.conflicts_input.setText(conflicts_str)
        form_deps.addRow("Conflits PNI :", self.conflicts_input)
        adv_layout.addWidget(group_deps)
        
        group_offset = QGroupBox("Décalage & Rupture")
        form_offset = QFormLayout(group_offset)
        
        self.offset_ref_input = QLineEdit()
        self.offset_ref_input.setPlaceholderText("ex: Penta3, VPI")
        ref_vaxes = adv_rules.get("offset_reference_vaccines", [])
        self.offset_ref_input.setText(", ".join(ref_vaxes))
        form_offset.addRow("Vaccins de Référence :", self.offset_ref_input)
        
        self.rupture_fallback_cb = QCheckBox("Utiliser le Décalage comme Exception de Rupture")
        self.rupture_fallback_cb.setChecked(adv_rules.get("rupture_fallback_offset", False))
        form_offset.addRow("", self.rupture_fallback_cb)
        
        self.fallback_min_age_input = QSpinBox()
        self.fallback_min_age_input.setRange(0, 10000)
        self.fallback_min_age_input.setValue(adv_rules.get("fallback_min_interval_days", 0))
        form_offset.addRow("Âge Min de Secours (j) [0=aucun] :", self.fallback_min_age_input)
        adv_layout.addWidget(group_offset)
        adv_layout.addStretch()
        self.tabs.addTab(tab_adv, "Règles Avancées")
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Valider")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
    def get_data(self):
        new_id = self.id_input.text().strip()
        new_milestone = self.milestone_input.currentText()
        
        rules = {}
        if self.min_age_input.value() > 0:
            rules["min_age_days"] = self.min_age_input.value()
        if self.offset_input.value() > 0:
            rules["offset_from_milestone_days"] = self.offset_input.value()
        if self.route_input.currentText():
            rules["administration_route"] = self.route_input.currentText()
        if self.site_input.currentText():
            rules["default_injection_site"] = self.site_input.currentText()
        if self.lifespan_input.value() > 0:
            rules["vial_lifespan_days"] = self.lifespan_input.value()
            
        # Parse Advanced UI Fields
        adv = {}
        if self.is_live_cb.isChecked():
            adv["is_live"] = True
        if self.live_conflict_exc_cb.isChecked():
            adv["live_conflict_exception"] = True
            
        # Parse dependencies
        deps_text = self.dependencies_input.text().strip()
        if deps_text:
            parsed_deps = []
            for part in deps_text.split(","):
                part = part.strip()
                if ":" in part:
                    vax, days = part.split(":", 1)
                    if days.strip().isdigit():
                        parsed_deps.append({"vaccine": vax.strip(), "min_interval_days": int(days.strip())})
            if parsed_deps:
                adv["dependencies"] = parsed_deps

        # Parse conflicts
        conflicts_text = self.conflicts_input.text().strip()
        if conflicts_text:
            parsed_confs = []
            for part in conflicts_text.split(";"):
                part = part.strip()
                if ":" in part:
                    vaxes_part, days = part.split(":", 1)
                    if days.strip().isdigit():
                        vaxes_list = [v.strip() for v in vaxes_part.split(",") if v.strip()]
                        if vaxes_list:
                            parsed_confs.append({"vaccines": vaxes_list, "min_interval_days": int(days.strip())})
            if parsed_confs:
                adv["conflicts"] = parsed_confs

        # Parse offset references
        ref_text = self.offset_ref_input.text().strip()
        if ref_text:
            parsed_refs = [v.strip() for v in ref_text.split(",") if v.strip()]
            if parsed_refs:
                adv["offset_reference_vaccines"] = parsed_refs

        if self.rupture_fallback_cb.isChecked():
            adv["rupture_fallback_offset"] = True
        
        if self.fallback_min_age_input.value() > 0:
            adv["fallback_min_interval_days"] = self.fallback_min_age_input.value()

        if adv:
            rules.update(adv)
            
        return {
            "id": new_id,
            "milestone": new_milestone,
            "rules": rules
        }

class MilestoneManagerDialog(QDialog):
    def __init__(self, parent=None, milestones_order=[]):
        super().__init__(parent)
        self.setWindowTitle("📅 Gestionnaire des Groupes d'âge (Milestones)")
        self.setMinimumSize(500, 400)
        # Deep copy to avoid modifying original until saved
        self.milestones = [{"name": m["name"], "target_days": m["target_days"]} for m in milestones_order]
        self.setup_ui()
        self.load_table()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        info = QLabel("Ajoutez ou supprimez des groupes d'âge. Le système les triera automatiquement par ordre chronologique lors de la sauvegarde.")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Nom du Groupe (ex: '10 Ans')", "Cible en Jours (ex: 3650)"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("➕ Ajouter un Groupe")
        btn_add.clicked.connect(self.add_row)
        btn_del = QPushButton("🗑️ Supprimer la sélection")
        btn_del.clicked.connect(self.delete_row)
        
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_del)
        layout.addLayout(btn_layout)
        
        save_layout = QHBoxLayout()
        save_btn = QPushButton("Valider")
        save_btn.clicked.connect(self.accept_data)
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        
        save_layout.addWidget(save_btn)
        save_layout.addWidget(cancel_btn)
        layout.addLayout(save_layout)
        
    def load_table(self):
        self.table.setRowCount(0)
        for m in self.milestones:
            self.add_row(m["name"], str(m["target_days"]))
            
    def add_row(self, name="", target="0"):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(name))
        
        target_item = QTableWidgetItem(str(target))
        self.table.setItem(row, 1, target_item)
        
    def delete_row(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            resp = QMessageBox.question(self, "Confirmation", "Voulez-vous vraiment supprimer ce groupe d'âge ?\nAttention : cela pourrait affecter les vaccins qui y sont liés.",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if resp == QMessageBox.StandardButton.Yes:
                self.table.removeRow(current_row)
                
    def accept_data(self):
        new_ms = []
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            target_item = self.table.item(row, 1)
            
            if not name_item or not target_item or not name_item.text().strip() or not target_item.text().strip():
                continue
                
            name = name_item.text().strip()
            try:
                target_days = int(target_item.text().strip())
            except ValueError:
                QMessageBox.warning(self, "Erreur de saisie", f"La valeur cible en jours pour '{name}' doit être un nombre entier.")
                return
                
            new_ms.append({"name": name, "target_days": target_days})
            
        # Sort chronologically by target days
        new_ms.sort(key=lambda x: x["target_days"])
        self.milestones = new_ms
        self.accept()
        
    def get_data(self):
        return self.milestones

class VaccineManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("💉 Gestionnaire de Vaccins")
        self.setMinimumSize(900, 600)
        
        self.data = {"vaccines": [], "milestones_order": []}
        
        self.current_vaccine_index = -1
        
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Splitter to divide list and details
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # LEFT: List of Vaccines
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        left_layout.addWidget(QLabel("<b>Familles de Vaccins</b>"))
        
        self.vax_list = QListWidget()
        self.vax_list.currentRowChanged.connect(self.on_vaccine_selected)
        left_layout.addWidget(self.vax_list)
        
        btn_layout = QHBoxLayout()
        self.btn_add_vax = QPushButton("➕ Ajouter")
        self.btn_add_vax.clicked.connect(self.add_vaccine)
        self.btn_del_vax = QPushButton("🗑️ Supprimer")
        self.btn_del_vax.clicked.connect(self.delete_vaccine)
        
        btn_layout.addWidget(self.btn_add_vax)
        btn_layout.addWidget(self.btn_del_vax)
        left_layout.addLayout(btn_layout)
        
        btn_manage_ms = QPushButton("📅 Gérer les Groupes d'âge")
        btn_manage_ms.setStyleSheet("background-color: #8e44ad; color: white; padding: 6px;")
        btn_manage_ms.clicked.connect(self.open_milestone_manager)
        left_layout.addWidget(btn_manage_ms)
        
        # RIGHT: Vaccine Details
        right_widget = QWidget()
        self.right_layout = QVBoxLayout(right_widget)
        
        self.right_layout.addWidget(QLabel("<b>Détails du Vaccin</b>"))
        
        self.tabs = QTabWidget()
        self.right_layout.addWidget(self.tabs)
        
        # TAB 1: Infos Générales
        tab_infos = QWidget()
        form_layout = QFormLayout(tab_infos)
        
        self.input_id = QLineEdit()
        self.input_id.setPlaceholderText("ID interne (ex: vpo, bcg)")
        form_layout.addRow("ID Interne:", self.input_id)
        
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Nom (ex: VPO, BCG)")
        form_layout.addRow("Nom Affiché:", self.input_name)
        
        self.input_desc = QTextEdit()
        self.input_desc.setMaximumHeight(60)
        self.input_desc.setPlaceholderText("Description du vaccin...")
        form_layout.addRow("Description:", self.input_desc)
        
        self.input_linked = QLineEdit()
        self.input_linked.setPlaceholderText("Famille liée (ex: DTC_Ag, Polio_Ag)")
        form_layout.addRow("Famille d'Antigène Liée (Optionnel):", self.input_linked)
        
        self.tabs.addTab(tab_infos, "Infos Générales")
        
        # TAB 2: Doses & Calendrier
        tab_doses = QWidget()
        doses_layout = QVBoxLayout(tab_doses)
        
        self.doses_tree = QTreeWidget()
        self.doses_tree.setHeaderLabels(["Dose ID", "Groupe d'âge (Milestone)", "Règles"])
        self.doses_tree.itemDoubleClicked.connect(self.edit_dose)
        doses_layout.addWidget(self.doses_tree)
        
        dose_btn_layout = QHBoxLayout()
        self.btn_add_dose = QPushButton("➕ Ajouter Dose")
        self.btn_add_dose.clicked.connect(self.add_dose)
        self.btn_del_dose = QPushButton("🗑️ Supprimer Dose")
        self.btn_del_dose.clicked.connect(self.delete_dose)
        dose_btn_layout.addWidget(self.btn_add_dose)
        dose_btn_layout.addWidget(self.btn_del_dose)
        doses_layout.addLayout(dose_btn_layout)
        
        self.tabs.addTab(tab_doses, "Doses & Calendrier")
        
        # TAB 3: Rattrapage
        tab_catchup = QWidget()
        catchup_layout = QVBoxLayout(tab_catchup)
        
        self.catchup_table = QTableWidget(0, 6)
        self.catchup_table.setHorizontalHeaderLabels(["Label Tranche", "Min (jours)", "Max (jours)", "Doses", "Produit", "Observations"])
        self.catchup_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        catchup_layout.addWidget(self.catchup_table)
        
        catchup_btn_layout = QHBoxLayout()
        self.btn_add_catchup = QPushButton("➕ Ajouter Règle")
        self.btn_add_catchup.clicked.connect(self.add_catchup_rule)
        self.btn_del_catchup = QPushButton("🗑️ Supprimer Règle")
        self.btn_del_catchup.clicked.connect(self.delete_catchup_rule)
        catchup_btn_layout.addWidget(self.btn_add_catchup)
        catchup_btn_layout.addWidget(self.btn_del_catchup)
        catchup_layout.addLayout(catchup_btn_layout)
        
        self.tabs.addTab(tab_catchup, "Rattrapage (Catch-up)")
        
        # Save Current Vaccine Buttons
        btn_save_vax = QPushButton("💾 Enregistrer les Modifications du Vaccin (BDD Temporaire)")
        btn_save_vax.setStyleSheet("background-color: #2980b9; color: white; padding: 6px;")
        btn_save_vax.clicked.connect(self.save_current_vaccine_info)
        self.right_layout.addWidget(btn_save_vax)
        
        # Add to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([250, 650])
        
        layout.addWidget(splitter)
        
        # Global Save
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        self.btn_save_all = QPushButton("💾 Sauvegarder dans la Base de Données")
        self.btn_save_all.setStyleSheet("background-color: #27ae60; color: white; padding: 10px; font-weight: bold;")
        self.btn_save_all.clicked.connect(self.save_to_db)
        bottom_layout.addWidget(self.btn_save_all)
        
        layout.addLayout(bottom_layout)
        self.clear_form()
        
    def load_data(self):
        try:
            main_app = self.parent().parent()
            if hasattr(main_app, 'engine'):
                self.data = main_app.engine.api.get_vaccine_families_with_doses()
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de contacter la base de données (Engine introuvable).")
                return
        except Exception as e:
            # Standalone mode dummy data
            self.data = {"vaccines": [], "milestones_order": []}
            
        self.refresh_vaccine_list()
        
    def refresh_vaccine_list(self):
        self.vax_list.clear()
        for v in self.data.get("vaccines", []):
            item = QListWidgetItem(v.get("name", "Inconnu"))
            self.vax_list.addItem(item)
            
    def clear_form(self):
        self.input_id.clear()
        self.input_name.clear()
        self.input_desc.clear()
        self.input_linked.clear()
        self.doses_tree.clear()
        self.catchup_table.setRowCount(0)
        self.btn_add_dose.setEnabled(False)
        self.btn_del_dose.setEnabled(False)
        self.btn_add_catchup.setEnabled(False)
        self.btn_del_catchup.setEnabled(False)
        self.current_vaccine_index = -1
        
    def on_vaccine_selected(self, index):
        if index < 0 or index >= len(self.data.get("vaccines", [])):
            self.clear_form()
            return
            
        self.current_vaccine_index = index
        vax = self.data["vaccines"][index]
        
        self.input_id.setText(vax.get("id", ""))
        self.input_name.setText(vax.get("name", ""))
        self.input_desc.setPlainText(vax.get("description", ""))
        self.input_linked.setText(vax.get("linked_antigen_family", ""))
        
        self.refresh_doses_tree()
        
        # Populate catchup rules
        self.catchup_table.setRowCount(0)
        for rule in vax.get("catchup_rules", []):
            row = self.catchup_table.rowCount()
            self.catchup_table.insertRow(row)
            self.catchup_table.setItem(row, 0, QTableWidgetItem(str(rule.get("label", ""))))
            self.catchup_table.setItem(row, 1, QTableWidgetItem(str(rule.get("min_age_days", "0"))))
            self.catchup_table.setItem(row, 2, QTableWidgetItem(str(rule.get("max_age_days", "9999"))))
            self.catchup_table.setItem(row, 3, QTableWidgetItem(str(rule.get("doses", "0"))))
            self.catchup_table.setItem(row, 4, QTableWidgetItem(str(rule.get("product", ""))))
            self.catchup_table.setItem(row, 5, QTableWidgetItem(str(rule.get("observation", ""))))
            
        self.btn_add_dose.setEnabled(True)
        self.btn_del_dose.setEnabled(True)
        self.btn_add_catchup.setEnabled(True)
        self.btn_del_catchup.setEnabled(True)
        
    def refresh_doses_tree(self):
        self.doses_tree.clear()
        if self.current_vaccine_index < 0: return
        
        vax = self.data["vaccines"][self.current_vaccine_index]
        for dose in vax.get("doses", []):
            item = QTreeWidgetItem([
                dose.get("id", ""), 
                dose.get("milestone", ""), 
                str(dose.get("rules", {}))
            ])
            self.doses_tree.addTopLevelItem(item)
            
    def save_current_vaccine_info(self):
        if self.current_vaccine_index < 0: return
        
        vax = self.data["vaccines"][self.current_vaccine_index]
        vax["id"] = self.input_id.text().strip()
        vax["name"] = self.input_name.text().strip()
        vax["description"] = self.input_desc.toPlainText().strip()
        vax["linked_antigen_family"] = self.input_linked.text().strip()
        
        # Parse Catch-up Rules from Table
        catchup_rules = []
        for row in range(self.catchup_table.rowCount()):
            label = self.catchup_table.item(row, 0).text() if self.catchup_table.item(row, 0) else ""
            min_age = self.catchup_table.item(row, 1).text() if self.catchup_table.item(row, 1) else "0"
            max_age = self.catchup_table.item(row, 2).text() if self.catchup_table.item(row, 2) else "9999"
            doses = self.catchup_table.item(row, 3).text() if self.catchup_table.item(row, 3) else "0"
            product = self.catchup_table.item(row, 4).text() if self.catchup_table.item(row, 4) else ""
            obs = self.catchup_table.item(row, 5).text() if self.catchup_table.item(row, 5) else ""
            
            catchup_rules.append({
                "label": label,
                "min_age_days": int(min_age) if min_age.isdigit() else 0,
                "max_age_days": int(max_age) if max_age.isdigit() else 9999,
                "doses": int(doses) if doses.isdigit() else 0,
                "product": product,
                "observation": obs
            })
            
        vax["catchup_rules"] = catchup_rules
        
        # update list visual
        self.vax_list.item(self.current_vaccine_index).setText(vax["name"])
        QMessageBox.information(self, "Succès", "Informations temporaires enregistrées.\nN'oubliez pas le bouton vert Global pour persister les changements en base.")
        
    def add_catchup_rule(self):
        if self.current_vaccine_index < 0: return
        row = self.catchup_table.rowCount()
        self.catchup_table.insertRow(row)
        self.catchup_table.setItem(row, 0, QTableWidgetItem("Nouvelle Tranche"))
        self.catchup_table.setItem(row, 1, QTableWidgetItem("0"))
        self.catchup_table.setItem(row, 2, QTableWidgetItem("365"))
        self.catchup_table.setItem(row, 3, QTableWidgetItem("1"))
        self.catchup_table.setItem(row, 4, QTableWidgetItem(""))
        self.catchup_table.setItem(row, 5, QTableWidgetItem(""))
        
    def delete_catchup_rule(self):
        curr = self.catchup_table.currentRow()
        if curr >= 0:
            self.catchup_table.removeRow(curr)
        
    def add_vaccine(self):
        name, ok = QInputDialog.getText(self, "Nouveau Vaccin", "Nom de la famille de vaccin :")
        if ok and name:
            new_vax = {
                "id": name.lower().replace(" ", "_"),
                "name": name,
                "description": "",
                "doses": []
            }
            if "vaccines" not in self.data:
                self.data["vaccines"] = []
            self.data["vaccines"].append(new_vax)
            self.refresh_vaccine_list()
            self.vax_list.setCurrentRow(len(self.data["vaccines"]) - 1)
            
    def delete_vaccine(self):
        if self.current_vaccine_index < 0: return
        
        # Confirm
        name = self.data["vaccines"][self.current_vaccine_index]["name"]
        resp = QMessageBox.question(self, "Confirmation", f"Voulez-vous vraiment supprimer le vaccin {name} et toutes ses doses ?\n(Les doses déjà administrées aux patients seront conservées dans les archives)", 
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if resp == QMessageBox.StandardButton.Yes:
            # Delete all doses of this vaccine from DB (Cascading PENDING deletes)
            try:
                main_app = self.parent().parent()
                if hasattr(main_app, 'engine'):
                    for d in self.data["vaccines"][self.current_vaccine_index]["doses"]:
                        main_app.engine.delete_vaccine_dose_in_db(d.get("id"))
            except Exception:
                pass
                
            del self.data["vaccines"][self.current_vaccine_index]
            self.refresh_vaccine_list()
            self.clear_form()
            
    def add_dose(self):
        if self.current_vaccine_index < 0: return
        
        milestones = [m.get("name", "") for m in self.data.get("milestones_order", [])]
        dialog = DoseFormDialog(self, milestones)
        
        if dialog.exec():
            new_dose = dialog.get_data()
            if not new_dose["id"]:
                QMessageBox.warning(self, "Erreur", "L'ID de la dose est requis.")
                return
                
            self.data["vaccines"][self.current_vaccine_index]["doses"].append(new_dose)
            self.refresh_doses_tree()
        
    def edit_dose(self, item, column):
        if self.current_vaccine_index < 0: return
        selected = self.doses_tree.currentItem()
        if not selected: return
        
        index = self.doses_tree.indexOfTopLevelItem(selected)
        if index < 0: return
        
        old_dose = self.data["vaccines"][self.current_vaccine_index]["doses"][index]
        old_id = old_dose.get("id", "")
        
        milestones = [m.get("name", "") for m in self.data.get("milestones_order", [])]
        dialog = DoseFormDialog(self, milestones, dose_data=old_dose)
        
        if dialog.exec():
            updated_dose = dialog.get_data()
            new_id = updated_dose["id"]
            
            if not new_id:
                QMessageBox.warning(self, "Erreur", "L'ID de la dose est requis.")
                return
                
            # Update RAM Data
            self.data["vaccines"][self.current_vaccine_index]["doses"][index] = updated_dose
            self.refresh_doses_tree()
            
            # Fire DB Update if ID changed
            if new_id != old_id:
                try:
                    main_app = self.parent().parent()
                    if hasattr(main_app, 'engine'):
                        main_app.engine.rename_vaccine_in_db(old_id, new_id)
                        QMessageBox.information(self, "Historique mis à jour", 
                                                f"Tous les dossiers patients existants ayant reçu '{old_id}' afficheront désormais '{new_id}'.")
                except Exception:
                    pass
        
    def delete_dose(self):
        if self.current_vaccine_index < 0: return
        selected = self.doses_tree.currentItem()
        if not selected: return
        
        index = self.doses_tree.indexOfTopLevelItem(selected)
        if index >= 0:
            dose_id_to_delete = self.data["vaccines"][self.current_vaccine_index]["doses"][index].get("id")
            
            resp = QMessageBox.question(self, "Confirmation", f"Voulez-vous supprimer la dose '{dose_id_to_delete}' ?\n(Les doses déjà administrées seront conservées dans les archives)", 
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if resp == QMessageBox.StandardButton.Yes:
                # Delete PENDING dose from DB
                try:
                    main_app = self.parent().parent()
                    if hasattr(main_app, 'engine'):
                        main_app.engine.delete_vaccine_dose_in_db(dose_id_to_delete)
                except Exception:
                    pass
                    
                del self.data["vaccines"][self.current_vaccine_index]["doses"][index]
                self.refresh_doses_tree()
            
    def save_to_db(self):
        try:
            main_app = self.parent().parent()
            if hasattr(main_app, 'engine') and hasattr(main_app.engine, 'api'):
                main_app.engine.api.save_protocols_to_api(self.data)
                QMessageBox.information(self, "Succès", "Sauvegardé avec succès via l'API Rest Django.")
            else:
                QMessageBox.warning(self, "Erreur", "Engine / API non trouvés.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde : {e}")

    def open_milestone_manager(self):
        dialog = MilestoneManagerDialog(self, self.data.get("milestones_order", []))
        if dialog.exec():
            self.data["milestones_order"] = dialog.get_data()
            QMessageBox.information(self, "Succès", "Groupes d'âge mis à jour temporairement.\nN'oubliez pas de 'Sauvegarder dans la Base de Données' pour appliquer les changements.")

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    dialog = VaccineManagerDialog()
    dialog.exec()
