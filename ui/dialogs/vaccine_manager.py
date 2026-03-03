import json
import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, QLineEdit, 
                             QTextEdit, QSplitter, QTreeWidget, QTreeWidgetItem,
                             QMessageBox, QInputDialog, QComboBox, QSpinBox)
from PyQt6.QtCore import Qt

class DoseFormDialog(QDialog):
    def __init__(self, parent=None, milestones=[], dose_data=None):
        super().__init__(parent)
        self.setWindowTitle("Éditer la Dose")
        self.dose_data = dose_data or {"id": "", "milestone": milestones[0] if milestones else "", "rules": {}}
        self.setup_ui(milestones)
        
    def setup_ui(self, milestones):
        layout = QVBoxLayout(self)
        
        # ID
        layout.addWidget(QLabel("ID de la Dose (ex: VPO4) :"))
        self.id_input = QLineEdit(self.dose_data.get("id", ""))
        layout.addWidget(self.id_input)
        
        # Milestone
        layout.addWidget(QLabel("Groupe d'âge (Milestone) :"))
        self.milestone_input = QComboBox()
        self.milestone_input.addItems(milestones)
        self.milestone_input.setCurrentText(self.dose_data.get("milestone", ""))
        layout.addWidget(self.milestone_input)
        
        # Rules (Common)
        rules = self.dose_data.get("rules", {})
        
        layout.addWidget(QLabel("Âge minimum absolu (en jours) [0 = aucun] :"))
        self.min_age_input = QSpinBox()
        self.min_age_input.setRange(0, 10000)
        self.min_age_input.setValue(rules.get("min_age_days", 0))
        layout.addWidget(self.min_age_input)
        
        layout.addWidget(QLabel("Décalage après le milestone (en jours) [0 = aucun] :"))
        self.offset_input = QSpinBox()
        self.offset_input.setRange(0, 10000)
        self.offset_input.setValue(rules.get("offset_from_milestone_days", 0))
        layout.addWidget(self.offset_input)
        
        layout.addWidget(QLabel("Règles avancées (JSON: dependencies, etc.) :"))
        self.rules_json_input = QTextEdit()
        adv_rules = {k: v for k, v in rules.items() if k not in ["min_age_days", "offset_from_milestone_days"]}
        self.rules_json_input.setText(json.dumps(adv_rules, indent=2) if adv_rules else "")
        self.rules_json_input.setMaximumHeight(80)
        layout.addWidget(self.rules_json_input)
        
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
            
        try:
            adv_text = self.rules_json_input.toPlainText().strip()
            if adv_text:
                adv = json.loads(adv_text)
                if isinstance(adv, dict):
                    rules.update(adv)
        except Exception as e:
            QMessageBox.warning(self, "Erreur JSON", f"Le JSON avancé est invalide (ignoré):\n{e}")
            
        return {
            "id": new_id,
            "milestone": new_milestone,
            "rules": rules
        }

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
        
        # RIGHT: Vaccine Details
        right_widget = QWidget()
        self.right_layout = QVBoxLayout(right_widget)
        
        self.right_layout.addWidget(QLabel("<b>Détails du Vaccin</b>"))
        
        # Properties
        form_layout = QVBoxLayout()
        
        self.input_id = QLineEdit()
        self.input_id.setPlaceholderText("ID interne (ex: vpo, bcg)")
        form_layout.addWidget(QLabel("ID Interne:"))
        form_layout.addWidget(self.input_id)
        
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Nom (ex: VPO, BCG)")
        form_layout.addWidget(QLabel("Nom Affiché:"))
        form_layout.addWidget(self.input_name)
        
        self.input_desc = QTextEdit()
        self.input_desc.setMaximumHeight(60)
        self.input_desc.setPlaceholderText("Description du vaccin...")
        form_layout.addWidget(QLabel("Description:"))
        form_layout.addWidget(self.input_desc)
        
        btn_save_vax = QPushButton("💾 Enregistrer les infos du vaccin")
        btn_save_vax.clicked.connect(self.save_current_vaccine_info)
        form_layout.addWidget(btn_save_vax)
        
        self.right_layout.addLayout(form_layout)
        self.right_layout.addSpacing(15)
        
        # Doses Tree
        self.right_layout.addWidget(QLabel("<b>Doses Administrées</b>"))
        self.doses_tree = QTreeWidget()
        self.doses_tree.setHeaderLabels(["Dose ID", "Groupe d'âge (Milestone)", "Règles"])
        self.doses_tree.itemDoubleClicked.connect(self.edit_dose)
        self.right_layout.addWidget(self.doses_tree)
        
        dose_btn_layout = QHBoxLayout()
        self.btn_add_dose = QPushButton("➕ Ajouter Dose")
        self.btn_add_dose.clicked.connect(self.add_dose)
        self.btn_del_dose = QPushButton("🗑️ Supprimer Dose")
        self.btn_del_dose.clicked.connect(self.delete_dose)
        
        dose_btn_layout.addWidget(self.btn_add_dose)
        dose_btn_layout.addWidget(self.btn_del_dose)
        self.right_layout.addLayout(dose_btn_layout)
        
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
                self.data = main_app.engine.db.get_all_vaccine_families_with_doses()
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
        self.doses_tree.clear()
        self.btn_add_dose.setEnabled(False)
        self.btn_del_dose.setEnabled(False)
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
        
        self.refresh_doses_tree()
        self.btn_add_dose.setEnabled(True)
        self.btn_del_dose.setEnabled(True)
        
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
        
        # update list visual
        self.vax_list.item(self.current_vaccine_index).setText(vax["name"])
        QMessageBox.information(self, "Succès", "Informations temporaires enregistrées.")
        
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

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    dialog = VaccineManagerDialog()
    dialog.exec()
