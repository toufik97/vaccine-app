from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QLabel, QTableWidget, QHeaderView, QPushButton, QMessageBox
from PyQt6.QtCore import Qt
from datetime import datetime
from core.enums import Gender
from ui.widgets.sort_item import SortItem

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
            self.table.setItem(i, 3, SortItem(Gender.to_ui(str(p[3]))))
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
