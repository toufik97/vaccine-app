from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QFileDialog, QMessageBox
from PyQt6.QtGui import QPageLayout
from PyQt6.QtCore import QMarginsF
from PyQt6.QtPrintSupport import QPrinter

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
