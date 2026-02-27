from datetime import datetime, timedelta
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from ui.widgets.date_line_edit import DateLineEdit

class PatientTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(0, 3, parent)
        self.main_app = parent  # Reference to VaxApp controller
        self.setHorizontalHeaderLabels(["Étape / Vaccin", "Date Prévue", "Date Administrée"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.cellClicked.connect(self.toggle_group)
        self.collapsed_groups = set()

    def toggle_group(self, row, col):
        if col == 0:
            item = self.item(row, col)
            if item:
                data = item.data(Qt.ItemDataRole.UserRole)
                if data and data[0] == "group":
                    milestone = data[1]
                    if milestone in self.collapsed_groups:
                        self.collapsed_groups.remove(milestone)
                    else:
                        self.collapsed_groups.add(milestone)
                    
                    if self.main_app and self.main_app.current_patient_id:
                        self.main_app.load_table_data(self.main_app.current_patient_id)

    def populate(self, dob_str, records, engine, settings, pending_focus_row):
        # Prevent row hidden state leakage from previous patients
        self.setRowCount(0)
        self.clearContents()
        
        grouped = {}
        for r in records:
            m = r[0]
            if m not in grouped: grouped[m] = []
            grouped[m].append(r)
            
        total_rows = len(grouped) + len(records)
        self.setRowCount(total_rows)
        self.setShowGrid(True)
        self.verticalHeader().setVisible(False)
        today = datetime.now().date()
        
        milestone_days = {m[0]: m[1] for m in engine.milestones}

        if settings.get("dark_mode", True):
            bg_group = QColor("#222b3b") 
            bg_vax = QColor("#1e1e1e")   
            bg_group_done = QColor("#064e3b")
            bg_vax_done = QColor("#022c22")
            bg_group_late = QColor("#7f1d1d")
            bg_vax_late = QColor("#450a0a")
            bg_group_today = QColor("#9a6000")
            bg_vax_today = QColor("#451a03")
            bg_group_rupture = QColor("#4c1d95")
            bg_vax_rupture = QColor("#2e1065")
            bg_group_maladie = QColor("#9a3412")
            bg_vax_maladie = QColor("#431407") 
            text_color = QColor("#f8fafc")
            text_rupture = QColor("#c084fc")
            text_maladie = QColor("#fdba74")
            input_style_done = "background-color: transparent; border: none; font-weight: bold; color: #10b981;"
            input_style_empty = "background-color: #334155; border: 1px solid #475569; border-radius: 4px; padding: 4px; color: #f1f5f9; font-weight: bold;"
            input_style_group = "background-color: #1e293b; border: 1px solid #334155; border-radius: 4px; padding: 4px; color: #94a3b8; font-weight: bold;"
            input_style_rupture = "background-color: transparent; border: none; font-weight: bold; color: #d8b4fe;"
            input_style_maladie = "background-color: transparent; border: none; font-weight: bold; color: #fed7aa;"
        else:
            bg_group = QColor("#cbd5e1") 
            bg_vax = QColor("#ffffff")   
            bg_group_done = QColor("#a7f3d0") 
            bg_vax_done = QColor("#ecfdf5")   
            bg_group_late = QColor("#fecaca") 
            bg_vax_late = QColor("#fef2f2")   
            bg_group_today = QColor("#fde047") 
            bg_vax_today = QColor("#fefce8")   
            bg_group_rupture = QColor("#e9d5ff")
            bg_vax_rupture = QColor("#faf5ff")
            bg_group_maladie = QColor("#fed7aa")
            bg_vax_maladie = QColor("#fff7ed") 
            text_color = QColor("#0f172a") 
            text_rupture = QColor("#7e22ce")
            text_maladie = QColor("#c2410c")
            input_style_done = "background-color: transparent; border: none; font-weight: bold; color: #059669;"
            input_style_empty = "background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; padding: 4px; color: #334155; font-weight: bold;"
            input_style_group = "background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; padding: 4px; color: #64748b; font-weight: bold;"
            input_style_rupture = "background-color: transparent; border: none; font-weight: bold; color: #6b21a8;"
            input_style_maladie = f"background-color: transparent; border: none; font-weight: bold; color: {text_maladie.name()};"

        bold_font = QFont()
        bold_font.setBold(True)

        row_idx = 0
        milestone_order = {m[0].strip().lower(): idx for idx, m in enumerate(engine.milestones)}
        
        sorted_milestones = sorted(list(grouped.keys()), key=lambda x: milestone_order.get(x.strip().lower(), 999))
        
        for milestone in sorted_milestones:
            vax_list = grouped[milestone]
            all_completed = all(v_data[3] in ["Done", "Externe"] for v_data in vax_list)
            
            dates_list = [v_data[4] for v_data in vax_list if v_data[3] in ["Done", "Externe"] and v_data[4]]
            group_date_str = max(set(dates_list), key=dates_list.count) if (all_completed and dates_list) else None
            
            due_date_str = vax_list[0][2]
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
            
            target_offset_days = milestone_days.get(milestone, 0)
            base_target = datetime.strptime(dob_str, "%Y-%m-%d").date() + timedelta(days=target_offset_days)
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
            
            # CONNECT SIGNAL TO MAIN WINDOW
            group_widget.navigationRequested.connect(
                lambda r, d, is_g=True, m=milestone, v=None, st=group_status, gs=group_date_str, dob=dob_str: 
                self.main_app.handle_navigation(r, d, is_g, m, v, st, gs, dob)
            )

            if all_completed and group_date_str:
                if group_date_str == "Inconnue":
                    group_fmt = "Inconnue"
                else:
                    group_fmt = datetime.strptime(group_date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
                all_externe = all(v_data[3] == "Externe" for v_data in vax_list)
                tag = " (Naiss.)" if (all_externe and group_date_str == dob_str) else (" (Ext.)" if all_externe else "")
                if len(set(dates_list)) > 1: tag += " *"
                    
                group_widget.setText(f"{group_fmt}{tag}")
                group_widget.setStyleSheet(input_style_done)
                lbl_group.setBackground(bg_group_done)
                due_group.setBackground(bg_group_done)
                bg_container = QTableWidgetItem()
                bg_container.setBackground(bg_group_done)
                self.setItem(row_idx, 2, bg_container)
            else:
                group_widget.setStyleSheet(input_style_group)
                if is_late:
                    lbl_group.setBackground(bg_group_late)
                    due_group.setBackground(bg_group_late)
                elif is_today:
                    lbl_group.setBackground(bg_group_today)
                    due_group.setBackground(bg_group_today)
                else:
                    lbl_group.setBackground(bg_group)
                    due_group.setBackground(bg_group)
                self.setItem(row_idx, 2, QTableWidgetItem())
                
            self.setItem(row_idx, 0, lbl_group)
            self.setItem(row_idx, 1, due_group)
            self.setCellWidget(row_idx, 2, group_widget)
            
            self.setRowHeight(row_idx, 45)
            self.setRowHidden(row_idx, False)  # VERY IMPORTANT: explicitly unhide group rows!
            row_idx += 1

            for v_data in vax_list:
                milestone_name, vax_name, due_date_str, status, given_str, obs = v_data
                
                display_name = vax_name
                if vax_name == "Pneumo3_NewOnly":
                    display_name = "Pneumo3 (6 Mois)"
                elif vax_name == "Pneumo_Final":
                    display_name = "Pneumo3 (12 Mois)" if settings.get("pneumo_mode", "Old") == "Old" else "Pneumo4 (12 Mois)"
                    
                lbl_text = f"      ↳ {display_name}"
                if obs: lbl_text += " ℹ️"
                    
                lbl_vax = QTableWidgetItem(lbl_text)
                if obs: lbl_vax.setToolTip(obs)
                lbl_vax.setForeground(text_color)
                lbl_vax.setFlags(lbl_vax.flags() & ~Qt.ItemFlag.ItemIsEditable)
                due_vax_text = ""
                if due_date_str:
                    due_vax_text = datetime.strptime(due_date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
                    if status in ["Done", "Externe"]:
                        due_vax_text += " ✅"
                    elif is_late:
                        due_vax_text += " ⚠️"
                    elif is_today:
                        due_vax_text += " ⏳"
                    
                vax_widget = DateLineEdit(row_idx)
                vax_widget.setPlaceholderText("Date, T, N, E, R, M")
                vax_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                if vax_name == "Pneumo3_NewOnly" and settings.get("pneumo_mode", "Old") == "Old":
                    due_vax_text = "Non requis 🚫"
                    vax_widget.setReadOnly(True)
                    vax_widget.setEnabled(False)
                    vax_widget.setPlaceholderText("-")
                    status = "Pending"
                    is_late = False
                    is_today = False
                    
                due_vax = QTableWidgetItem(due_vax_text) 
                due_vax.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                due_vax.setFlags(due_vax.flags() & ~Qt.ItemFlag.ItemIsEditable)
                
                vax_widget.navigationRequested.connect(
                    lambda r, d, is_g=False, m=milestone, v=vax_name, st=status, gs=given_str, dob=dob_str: 
                    self.main_app.handle_navigation(r, d, is_g, m, v, st, gs, dob)
                )

                if status in ["Done", "Externe"] and given_str:
                    if given_str == "Inconnue":
                        given_fmt = "Inconnue"
                    else:
                        given_fmt = datetime.strptime(given_str, "%Y-%m-%d").strftime("%d/%m/%Y")
                    tag = " (Naiss.)" if given_str == dob_str else " (Ext.)" if status == "Externe" else ""
                    vax_widget.setText(f"{given_fmt}{tag}")
                    lbl_vax.setBackground(bg_vax_done)
                    due_vax.setBackground(bg_vax_done)
                    vax_widget.setStyleSheet(input_style_done)
                    bg_container = QTableWidgetItem()
                    bg_container.setBackground(bg_vax_done)
                    self.setItem(row_idx, 2, bg_container)
                    
                elif status in ["Rupture", "Maladie"]:
                    if status == "Rupture":
                        vax_widget.setText("Rupture de stock")
                        lbl_vax.setBackground(bg_vax_rupture)
                        due_vax.setBackground(bg_vax_rupture)
                        lbl_vax.setForeground(text_rupture)
                        due_vax.setForeground(text_rupture)
                        vax_widget.setStyleSheet(input_style_rupture)
                        bg_container = QTableWidgetItem()
                        bg_container.setBackground(bg_vax_rupture)
                    else:
                        vax_widget.setText("Reporté (Maladie)")
                        lbl_vax.setBackground(bg_vax_maladie)
                        due_vax.setBackground(bg_vax_maladie)
                        lbl_vax.setForeground(text_maladie)
                        due_vax.setForeground(text_maladie)
                        vax_widget.setStyleSheet(input_style_maladie)
                        bg_container = QTableWidgetItem()
                        bg_container.setBackground(bg_vax_maladie)
                    self.setItem(row_idx, 2, bg_container)
                    
                else:
                    vax_widget.setStyleSheet(input_style_empty)
                    if is_late:
                        due_vax.setBackground(bg_vax_late)
                        lbl_vax.setBackground(bg_vax_late)
                        bg_container = QTableWidgetItem()
                        bg_container.setBackground(bg_vax_late)
                        self.setItem(row_idx, 2, bg_container)
                    elif is_today:
                        due_vax.setBackground(bg_vax_today)
                        lbl_vax.setBackground(bg_vax_today)
                        bg_container = QTableWidgetItem()
                        bg_container.setBackground(bg_vax_today)
                        self.setItem(row_idx, 2, bg_container)
                    else:
                        due_vax.setBackground(bg_vax)
                        lbl_vax.setBackground(bg_vax)
                        bg_container = QTableWidgetItem()
                        bg_container.setBackground(bg_vax)
                        self.setItem(row_idx, 2, bg_container)

                self.setItem(row_idx, 0, lbl_vax)
                self.setItem(row_idx, 1, due_vax)
                self.setCellWidget(row_idx, 2, vax_widget)
                
                self.setRowHeight(row_idx, 38)
                self.setRowHidden(row_idx, is_collapsed)
                row_idx += 1

        if pending_focus_row is not None:
            widget = self.cellWidget(pending_focus_row, 2)
            if widget:
                widget.setFocus()
                widget.selectAll()

