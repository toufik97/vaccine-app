from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton

class HelpDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("❔ Guide d'utilisation")
        self.setMinimumSize(600, 550)
        layout = QVBoxLayout(self)
        
        help_text = """
        <h2 style="color: #2980b9;">Guide Rapide - Vaccine Tracker Pro</h2>
        <h3>🔍 Recherche Intelligente</h3>
        <ul>
            <li><b>Recherche par Nom/ID :</b> Tapez le nom pour trouver le dossier.</li>
            <li><b>Recherche par Date :</b> Tapez une date (ex: <code>21/02/26</code>). L'application affichera tous les enfants vaccinés ce jour-là !</li>
        </ul>
        <h3>🎨 Codes Couleurs</h3>
        <ul>
            <li><span style="background-color: #d4edda; color: #1b5e20; padding: 2px 5px; border-radius: 3px;"><b>🟢 VERT</b></span> : Administré / validé.</li>
            <li><span style="background-color: #fff3cd; color: #e65100; padding: 2px 5px; border-radius: 3px;"><b>🟡 JAUNE</b></span> : Prévu pour Aujourd'hui.</li>
            <li><span style="background-color: #f8d7da; color: #b71c1c; padding: 2px 5px; border-radius: 3px;"><b>🔴 ROUGE</b></span> : En retard.</li>
            <li><span style="background-color: #d2b4de; color: #4a235a; padding: 2px 5px; border-radius: 3px;"><b>🟣 VIOLET</b></span> : Rupture de Stock.</li>
            <li><span style="background-color: #fdebd0; color: #d35400; padding: 2px 5px; border-radius: 3px;"><b>🟠 ORANGE</b></span> : Maladie / Fièvre.</li>
        </ul>
        <h3>⌨️ Raccourcis Super-Rapides</h3>
        <ul>
            <li><b>'T' :</b> Aujourd'hui.</li>
            <li><b>'TE' :</b> Fait aujourd'hui en externe.</li>
            <li><b>'N' :</b> Naissance (HB Zéro).</li>
            <li><b>'R' :</b> Rupture de stock.</li>
            <li><b>'M' :</b> Maladie / Fièvre.</li>
        </ul>
        """
        text_area = QTextEdit()
        text_area.setHtml(help_text)
        text_area.setReadOnly(True)
        text_area.setStyleSheet("font-size: 13px; font-family: Arial, sans-serif;")
        layout.addWidget(text_area)
        
        close_btn = QPushButton("J'ai compris")
        close_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 8px; font-weight: bold;")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
