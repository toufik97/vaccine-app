from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QCalendarWidget, QTableWidget, QHeaderView, QComboBox, QLabel, QPushButton, QTableWidgetItem, QFileDialog, QMessageBox, QTextEdit, QDateEdit, QAbstractItemView
from PyQt6.QtCore import Qt, QMarginsF, QDate
from PyQt6.QtGui import QPageLayout, QTextDocument
from PyQt6.QtPrintSupport import QPrinter
from datetime import datetime
from core.report_builder import ReportBuilder

class DashboardDialog(QDialog):
    def __init__(self, parent, engine):
        super().__init__(parent)
        self.setWindowTitle("📊 Tableau de Bord des Statistiques")
        self.setMinimumSize(850, 600) 
        self.engine = engine
        
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e9ecef;
                color: #495057;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #2c3e50;
                border: 1px solid #ddd;
                border-bottom-color: white;
            }
            QLabel {
                font-size: 13px;
                color: #333;
            }
            QComboBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
                min-width: 100px;
                font-size: 13px;
            }
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                gridline-color: #f0f0f0;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
                font-size: 13px;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #c0392b; }
            QPushButton:pressed { background-color: #a53125; }
        """)
        
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        
        # Shared controls data
        months = [("Janvier", "01"), ("Février", "02"), ("Mars", "03"), ("Avril", "04"), 
                  ("Mai", "05"), ("Juin", "06"), ("Juillet", "07"), ("Août", "08"),
                  ("Septembre", "09"), ("Octobre", "10"), ("Novembre", "11"), ("Décembre", "12")]
        current_year = datetime.now().year
        
        # --- TAB: STATISTIQUES QUOTIDIENNES ---
        self.tab_daily = QWidget()
        daily_layout = QVBoxLayout(self.tab_daily)
        
        daily_controls = QHBoxLayout()
        self.daily_month_combo = QComboBox()
        for name, num in months:
            self.daily_month_combo.addItem(name, num)
            
        self.daily_year_combo = QComboBox()
        self.daily_year_combo.addItems([str(y) for y in range(2024, current_year + 5)])
        
        self.daily_month_combo.setCurrentIndex(datetime.now().month - 1)
        self.daily_year_combo.setCurrentText(str(current_year))
        
        self.daily_month_combo.currentIndexChanged.connect(self.update_daily)
        self.daily_year_combo.currentIndexChanged.connect(self.update_daily)
        
        daily_controls.addWidget(QLabel("<b>Mois :</b>"))
        daily_controls.addWidget(self.daily_month_combo)
        daily_controls.addWidget(QLabel("<b>Année :</b>"))
        daily_controls.addWidget(self.daily_year_combo)
        
        self.btn_export_daily = QPushButton("📄 Exporter Registre Journalier (PDF)")
        self.btn_export_daily.clicked.connect(self.export_daily_pdf)
        
        self.btn_export_daily_excel = QPushButton("📊 Exporter Registre Journalier (Excel)")
        self.btn_export_daily_excel.setStyleSheet("background-color: #27ae60; color: white;")
        self.btn_export_daily_excel.clicked.connect(self.export_daily_excel)
        
        daily_controls.addWidget(self.btn_export_daily)
        daily_controls.addWidget(self.btn_export_daily_excel)
        daily_controls.addStretch()
        
        self.daily_table = QTableWidget(0, 0)
        self.daily_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        daily_layout.addLayout(daily_controls)
        daily_layout.addWidget(self.daily_table)
        
        # --- TAB: STATISTIQUES MENSUELLES ---
        self.tab_monthly = QWidget()
        monthly_layout = QVBoxLayout(self.tab_monthly)
        
        controls_layout = QHBoxLayout()
        self.month_combo = QComboBox()
        for name, num in months:
            self.month_combo.addItem(name, num)
            
        self.year_combo = QComboBox()
        self.year_combo.addItems([str(y) for y in range(2024, current_year + 5)])
        
        self.month_combo.setCurrentIndex(datetime.now().month - 1)
        self.year_combo.setCurrentText(str(current_year))
        
        self.month_combo.currentIndexChanged.connect(self.update_monthly)
        self.year_combo.currentIndexChanged.connect(self.update_monthly)
        
        controls_layout.addWidget(QLabel("<b>Mois :</b>"))
        controls_layout.addWidget(self.month_combo)
        controls_layout.addWidget(QLabel("<b>Année :</b>"))
        controls_layout.addWidget(self.year_combo)
        
        self.btn_export_monthly = QPushButton("📄 Exporter Fiche Mensuelle (PDF)")
        self.btn_export_monthly.clicked.connect(self.export_monthly_pdf)
        
        self.btn_export_monthly_excel = QPushButton("📊 Exporter Fiche Mensuelle (Excel)")
        self.btn_export_monthly_excel.setStyleSheet("background-color: #27ae60; color: white;")
        self.btn_export_monthly_excel.clicked.connect(self.export_monthly_excel)
        
        controls_layout.addWidget(self.btn_export_monthly)
        controls_layout.addWidget(self.btn_export_monthly_excel)
        
        controls_layout.addStretch()
        
        self.monthly_table = QTableWidget(0, 3)
        self.monthly_table.setHorizontalHeaderLabels(["Vaccin Administré", "Total", "Détail des Dates (Jour/Mois)"])
        self.monthly_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.monthly_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.monthly_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.monthly_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        monthly_layout.addLayout(controls_layout)
        monthly_layout.addWidget(self.monthly_table)
        
        # --- TAB: REGISTRE NUTRITION ---
        self.tab_nutrition = QWidget()
        nutrition_layout = QVBoxLayout(self.tab_nutrition)
        
        nutr_controls = QHBoxLayout()
        left_controls = QHBoxLayout()
        
        self.nutr_start_date = QDateEdit()
        self.nutr_start_date.setCalendarPopup(True)
        self.nutr_start_date.setDate(QDate.currentDate().addDays(-7))
        self.nutr_start_date.dateChanged.connect(self.update_nutrition_table)
        
        self.nutr_end_date = QDateEdit()
        self.nutr_end_date.setCalendarPopup(True)
        self.nutr_end_date.setDate(QDate.currentDate())
        self.nutr_end_date.dateChanged.connect(self.update_nutrition_table)
        
        left_controls.addWidget(QLabel("<b>Du:</b>"))
        left_controls.addWidget(self.nutr_start_date)
        left_controls.addWidget(QLabel("<b>Au:</b>"))
        left_controls.addWidget(self.nutr_end_date)
        left_controls.addStretch()
        
        right_controls = QVBoxLayout()
        self.btn_export_nutr = QPushButton("📄 Exporter Registre (PDF)")
        self.btn_export_nutr.clicked.connect(self.export_nutrition_pdf)
        
        self.btn_export_nutr_excel = QPushButton("📊 Exporter Registre (Excel)")
        self.btn_export_nutr_excel.setStyleSheet("background-color: #27ae60; color: white;")
        self.btn_export_nutr_excel.clicked.connect(self.export_nutrition_excel)
        
        right_controls.addWidget(self.btn_export_nutr)
        right_controls.addWidget(self.btn_export_nutr_excel)
        right_controls.addStretch()
        
        nutr_controls.addLayout(left_controls)
        nutr_controls.addSpacing(20)
        nutr_controls.addLayout(right_controls)
        nutr_controls.addStretch()
        
        self.nutr_table = QTableWidget(0, 7)
        self.nutr_table.setHorizontalHeaderLabels([
            "N° SMI", "Noms & Prénoms", "Sexe", "Âge", "Poids", "Taille", "Vaccins / Motif"
        ])
        self.nutr_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.nutr_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        nutrition_layout.addLayout(nutr_controls)
        nutrition_layout.addWidget(self.nutr_table)
        
        self.tabs.addTab(self.tab_daily, "📅 Statistiques Quotidiennes")
        self.tabs.addTab(self.tab_monthly, "📆 Statistiques Mensuelles")
        self.tabs.addTab(self.tab_nutrition, "🥗 Registre Nutrition")
        
        layout.addWidget(self.tabs)
        
        close_btn = QPushButton("Fermer le Tableau de Bord")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.update_daily()
        self.update_monthly()
        self.update_nutrition_table()
        
    def get_nutrition_date_range(self):
        start_qdate = self.nutr_start_date.date()
        end_qdate = self.nutr_end_date.date()
        if start_qdate > end_qdate:
            return []
            
        dates = []
        current = start_qdate
        while current <= end_qdate:
            dates.append(current.toString("yyyy-MM-dd"))
            current = current.addDays(1)
        return dates

    def update_nutrition_table(self):
        dates = self.get_nutrition_date_range()
        if not dates:
            self.nutr_table.setRowCount(0)
            return
            
        # Optimization: Only pass the dates, backend skips empty days natively
        data = self.engine.db.get_nutrition_register_data(dates)
        
        self.nutr_table.setRowCount(len(data))
        for r_idx, row in enumerate(data):
            # Calc Age
            try:
                dob = datetime.strptime(row['dob'], "%Y-%m-%d").date()
                today = datetime.now().date()
                age_months = (today - dob).days / 30.44
                age_str = f"{age_months:.1f} m"
            except:
                age_str = "N/A"
            
            motif = ", ".join(row['vaccines']) if row['vaccines'] else "Mesures Croissance"
            
            items = [
                row['patient_id'],
                row['name'],
                "M" if row['sexe'] in ["Garçon", "M"] else "F",
                age_str,
                str(row['weight']) if row['weight'] else "-",
                str(row['height']) if row['height'] else "-",
                f"[{row['record_date']}] {motif}" # Prefix motif with the date for clarity in the table
            ]
            
            for c_idx, val in enumerate(items):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter if c_idx not in [1, 6] else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.nutr_table.setItem(r_idx, c_idx, item)
                
    def update_daily(self):
        import calendar
        from core.report_builder import ReportBuilder
        
        month_num = int(self.daily_month_combo.currentData())
        year_str = int(self.daily_year_combo.currentText())
        query_str = f"{year_str}-{month_num:02d}%"
        
        _, num_days = calendar.monthrange(year_str, month_num)
        stats_data = self.engine.db.get_detailed_export_stats(query_str)
        
        vax_rows = [
            ("HB0_24h", "HB0 (Dans les 24h)"), ("HB0_BCG", "HB0 (Plus tard)"), ("BCG", "BCG"),
            ("VPO0", "VPO 0"), ("VPO1", "VPO 1"), ("VPO2", "VPO 2"), ("VPO3", "VPO 3"),
            ("VPI", "VPI 1"), ("VPI2", "VPI 2"),
            ("Pentavalent 1", "Penta 1"), ("Pentavalent 2", "Penta 2"), ("Pentavalent 3", "Penta 3"),
            ("Rota1", "Rota 1"), ("Rota2", "Rota 2"), ("Rota3", "Rota 3"),
            ("PCV1", "Pneumo 1"), ("PCV2", "Pneumo 2"), ("PCV3", "Pneumo 3"), ("PCV4", "Pneumo 4"),
            ("RR1", "RR 1 (9 mois)"), ("RR2", "RR 2 (18 mois)"),
            ("VPO (18 Mois)", "Rappel VPO (18m)"), ("VPO (5 Ans)", "Rappel VPO (5 ans)"),
            ("Rappel DTC1", "Rappel DTC 1"), ("Rappel DTC2", "Rappel DTC 2"),
        ]
        
        grid = {db_name: {d: 0 for d in range(1, num_days + 1)} for db_name, _ in vax_rows}
        day_totals = {d: 0 for d in range(1, num_days + 1)}
        
        for record in stats_data:
            mapped_name = ReportBuilder._map_vax_name(record)
            day = int(record["date_given"][-2:])
            if mapped_name in grid and 1 <= day <= num_days:
                grid[mapped_name][day] += 1
                day_totals[day] += 1
                
        active_days = [d for d in range(1, num_days + 1) if day_totals[d] > 0]
        
        self.daily_table.clear()
        self.daily_table.setColumnCount(len(active_days) + 2)
        
        headers = ["Vaccin"] + [f"{d:02d}/{month_num:02d}" for d in active_days] + ["Total"]
        self.daily_table.setHorizontalHeaderLabels(headers)
        self.daily_table.setRowCount(len(vax_rows) + 1)
        
        for r_idx, (db_name, label) in enumerate(vax_rows):
            item = QTableWidgetItem(label)
            self.daily_table.setItem(r_idx, 0, item)
            row_tot = sum(grid[db_name][d] for d in range(1, num_days + 1))
            
            for col_idx, d in enumerate(active_days):
                val = grid[db_name][d]
                cnt_item = QTableWidgetItem(str(val) if val > 0 else "")
                cnt_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.daily_table.setItem(r_idx, col_idx + 1, cnt_item)
                
            tot_item = QTableWidgetItem(str(row_tot) if row_tot > 0 else "")
            tot_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.daily_table.setItem(r_idx, len(active_days) + 1, tot_item)
            
        footer_idx = len(vax_rows)
        foot_label = QTableWidgetItem("Total Doses")
        self.daily_table.setItem(footer_idx, 0, foot_label)
        
        grand_tot = sum(day_totals[d] for d in range(1, num_days + 1))
        
        for col_idx, d in enumerate(active_days):
            val = day_totals[d]
            t_item = QTableWidgetItem(str(val) if val > 0 else "")
            t_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.daily_table.setItem(footer_idx, col_idx + 1, t_item)
            
        gt_item = QTableWidgetItem(str(grand_tot) if grand_tot > 0 else "")
        gt_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.daily_table.setItem(footer_idx, len(active_days) + 1, gt_item)
        
        self.daily_table.resizeColumnsToContents()

    def update_monthly(self):
        from core.report_builder import ReportBuilder
        
        month_num = int(self.month_combo.currentData())
        year_str = int(self.year_combo.currentText())
        query_str = f"{year_str}-{month_num:02d}%"
        
        stats_data = self.engine.db.get_detailed_export_stats(query_str)
        
        vax_rows = [
            ("HB0_24h", "HB0 (Dans les 24h)"), ("HB0_BCG", "HB0 (Plus tard)"), ("BCG", "BCG"),
            ("VPO0", "VPO 0"), ("VPO1", "VPO 1"), ("VPO2", "VPO 2"), ("VPO3", "VPO 3"),
            ("VPI", "VPI 1"), ("VPI2", "VPI 2"),
            ("Pentavalent 1", "Penta 1"), ("Pentavalent 2", "Penta 2"), ("Pentavalent 3", "Penta 3"),
            ("Rota1", "Rota 1"), ("Rota2", "Rota 2"), ("Rota3", "Rota 3"),
            ("PCV1", "Pneumo 1"), ("PCV2", "Pneumo 2"), ("PCV3", "Pneumo 3"), ("PCV4", "Pneumo 4"),
            ("RR1", "RR 1 (9 mois)"), ("RR2", "RR 2 (18 mois)"),
            ("VPO (18 Mois)", "Rappel VPO (18m)"), ("VPO (5 Ans)", "Rappel VPO (5 ans)"),
            ("Rappel DTC1", "Rappel DTC 1"), ("Rappel DTC2", "Rappel DTC 2"),
        ]
        
        # Aggregate counts and collect dates
        counts = {db_name: 0 for db_name, _ in vax_rows}
        dates_lists = {db_name: set() for db_name, _ in vax_rows}
        
        for record in stats_data:
            mapped_name = ReportBuilder._map_vax_name(record)
            if mapped_name in counts:
                counts[mapped_name] += 1
                
                # Format date as DD/MM
                d_str = record["date_given"]
                if d_str and len(d_str) >= 10:
                    d_fmt = f"{d_str[8:10]}/{d_str[5:7]}"
                    dates_lists[mapped_name].add(d_fmt)
                    
        self.monthly_table.setRowCount(len(vax_rows) + 1)
        grand_total = 0
        
        for idx, (db_name, label) in enumerate(vax_rows):
            count = counts[db_name]
            grand_total += count
            dates_str = ", ".join(sorted(list(dates_lists[db_name]))) if count > 0 else ""
            
            self.monthly_table.setItem(idx, 0, QTableWidgetItem(label))
            
            count_item = QTableWidgetItem(str(count) if count > 0 else "")
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.monthly_table.setItem(idx, 1, count_item)
            
            self.monthly_table.setItem(idx, 2, QTableWidgetItem(dates_str))
            
        footer_idx = len(vax_rows)
        self.monthly_table.setItem(footer_idx, 0, QTableWidgetItem("Total Doses Mensuelles"))
        gt_item = QTableWidgetItem(str(grand_total) if grand_total > 0 else "")
        gt_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.monthly_table.setItem(footer_idx, 1, gt_item)
        self.monthly_table.setItem(footer_idx, 2, QTableWidgetItem(""))

    def export_monthly_pdf(self):
        month_num = self.month_combo.currentData()
        year_str = self.year_combo.currentText()
        query_str = f"{year_str}-{month_num}%"
        
        stats_data = self.engine.db.get_detailed_export_stats(query_str)
        if not stats_data:
            QMessageBox.information(self, "Export", f"Aucune donnée à exporter pour {month_num}/{year_str}.")
            return
            
        # Get Center Info from App parent Settings
        center_name = self.parent().settings.get("center_name", "Centre inconnu")
        center_type = self.parent().settings.get("center_type", "Urbain")
        
        html_content = ReportBuilder.generate_fiche_html(stats_data, year_str, month_num, center_name, center_type)
        self._print_pdf(html_content, f"Fiche_Mensuelle_{year_str}_{month_num}.pdf")
        
    def export_daily_pdf(self):
        month_num = self.daily_month_combo.currentData()
        year_str = self.daily_year_combo.currentText()
        query_str = f"{year_str}-{month_num}%"
        
        # Test if we have data
        stats_data = self.engine.db.get_detailed_export_stats(query_str)
        if not stats_data:
            QMessageBox.information(self, "Export", f"Aucune donnée à exporter pour {month_num}/{year_str}.")
            return
            
        center_name = self.parent().settings.get("center_name", "Centre inconnu")
        center_type = self.parent().settings.get("center_type", "Urbain")
        
        # It's actually a month of breakdown
        html_content = ReportBuilder.generate_daily_breakdown_html(self.engine, year_str, month_num, center_name, center_type)
        self._print_pdf(html_content, f"Registre_Journalier_{year_str}_{month_num}.pdf")

    def export_monthly_excel(self):
        month_num = self.month_combo.currentData()
        year_str = self.year_combo.currentText()
        query_str = f"{year_str}-{month_num}%"
        
        stats_data = self.engine.db.get_detailed_export_stats(query_str)
        if not stats_data:
            QMessageBox.information(self, "Export", f"Aucune donnée à exporter pour {month_num}/{year_str}.")
            return
            
        center_name = self.parent().settings.get("center_name", "Centre inconnu")
        center_type = self.parent().settings.get("center_type", "Urbain")
        
        wb = ReportBuilder.generate_fiche_excel(stats_data, year_str, month_num, center_name, center_type)
        self._save_excel(wb, f"Fiche_Mensuelle_{year_str}_{month_num}.xlsx")

    def export_daily_excel(self):
        month_num = self.daily_month_combo.currentData()
        year_str = self.daily_year_combo.currentText()
        query_str = f"{year_str}-{month_num}%"
        
        stats_data = self.engine.db.get_detailed_export_stats(query_str)
        if not stats_data:
            QMessageBox.information(self, "Export", f"Aucune donnée à exporter pour {month_num}/{year_str}.")
            return
            
        center_name = self.parent().settings.get("center_name", "Centre inconnu")
        center_type = self.parent().settings.get("center_type", "Urbain")
        
        wb = ReportBuilder.generate_daily_breakdown_excel(self.engine, year_str, month_num, center_name, center_type)
        self._save_excel(wb, f"Registre_Journalier_{year_str}_{month_num}.xlsx")

    def export_nutrition_pdf(self):
        dates = self.get_nutrition_date_range()
        if not dates:
            QMessageBox.information(self, "Export", "La plage de dates est invalide.")
            return
            
        data = self.engine.db.get_nutrition_register_data(dates)
        
        if not data:
            QMessageBox.information(self, "Export", "Aucune donnée à exporter pour cette période.")
            return
            
        # Automatically filter dates to only those that have actual data
        actual_dates = sorted(list(set(r["record_date"] for r in data)))
            
        center_name = self.parent().settings.get("center_name", "Centre inconnu")
        center_type = self.parent().settings.get("center_type", "Urbain")
        
        html_content = ReportBuilder.generate_multi_nutrition_html(data, actual_dates, center_name, center_type)
        self._print_pdf(html_content, f"Registre_Nutrition_{actual_dates[0]}_au_{actual_dates[-1]}.pdf")

    def export_nutrition_excel(self):
        dates = self.get_nutrition_date_range()
        if not dates:
            QMessageBox.information(self, "Export", "La plage de dates est invalide.")
            return
            
        data = self.engine.db.get_nutrition_register_data(dates)
        
        if not data:
            QMessageBox.information(self, "Export", "Aucune donnée à exporter pour cette période.")
            return
            
        # Automatically filter dates to only those that have actual data
        actual_dates = sorted(list(set(r["record_date"] for r in data)))
            
        center_name = self.parent().settings.get("center_name", "Centre inconnu")
        center_type = self.parent().settings.get("center_type", "Urbain")
        
        wb = ReportBuilder.generate_multi_nutrition_excel(data, actual_dates, center_name, center_type)
        self._save_excel(wb, f"Registre_Nutrition_{actual_dates[0]}_au_{actual_dates[-1]}.xlsx")

    def _save_excel(self, wb, default_name):
        file_path, _ = QFileDialog.getSaveFileName(self, "Sauvegarder en Excel", default_name, "Excel Files (*.xlsx)")
        if file_path:
            try:
                wb.save(file_path)
                QMessageBox.information(self, "Succès", "Le rapport a été exporté en Excel avec succès ! 📊")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Échec de l'exportation Excel:\n{str(e)}")
        
    def _print_pdf(self, html_content, default_name):
        file_path, _ = QFileDialog.getSaveFileName(self, "Sauvegarder en PDF", default_name, "PDF Files (*.pdf)")
        if file_path:
            try:
                printer = QPrinter(QPrinter.PrinterMode.HighResolution)
                printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
                printer.setOutputFileName(file_path)
                printer.setPageOrientation(QPageLayout.Orientation.Landscape)
                
                margins = QMarginsF(10.0, 10.0, 10.0, 10.0)
                printer.setPageMargins(margins, QPageLayout.Unit.Millimeter)
                
                # Render HTML to PDF invisibly using QTextDocument
                doc = QTextDocument()
                doc.setHtml(html_content)
                doc.print(printer)
                
                QMessageBox.information(self, "Succès", "Le rapport a été exporté en PDF avec succès ! 🚀")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Échec de l'exportation PDF:\n{str(e)}")
