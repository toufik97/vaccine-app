from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QCalendarWidget, QTableWidget, QHeaderView, QComboBox, QLabel, QPushButton, QTableWidgetItem
from PyQt6.QtCore import Qt
from datetime import datetime

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
