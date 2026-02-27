from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton

class HelpDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("❔ Guide d'utilisation")
        self.setMinimumSize(600, 550)
        layout = QVBoxLayout(self)
        
        help_text = """
        <h2 style="color: #2980b9;">Guide Rapide - VaxPro</h2>
        
        <h3>🔍 Recherche Intelligente</h3>
        <ul>
            <li><b>Recherche par Nom/ID :</b> Tapez le nom/prénom ou l'ID (ex: <code>205/25</code>) pour trouver le dossier.</li>
            <li><b>Recherche par Date :</b> Tapez une date d'administration (ex: <code>21/02</code>). L'application affichera tous les enfants vaccinés ce jour-là !</li>
            <li><b>Auto-Déploiement :</b> En ouvrant un dossier, l'application déplie automatiquement la prochaine étape vaccinale attendue.</li>
        </ul>
        
        <h3>🎨 Code Couleur (Groupes)</h3>
        <ul>
            <li><span style="background-color: #d1fae5; color: #064e3b; padding: 2px 5px; border-radius: 3px;"><b>🟢 VERT</b></span> : Groupe entièrement validé.</li>
            <li><span style="background-color: #fef08a; color: #9a6000; padding: 2px 5px; border-radius: 3px;"><b>🟡 JAUNE</b></span> : Vaccination(s) prévue(s) pour aujourd'hui.</li>
            <li><span style="background-color: #fee2e2; color: #7f1d1d; padding: 2px 5px; border-radius: 3px;"><b>🔴 ROUGE</b></span> : Groupe en retard.</li>
            <li><span style="background-color: #f3e8ff; color: #4c1d95; padding: 2px 5px; border-radius: 3px;"><b>🟣 VIOLET</b></span> : Rupture de Stock.</li>
            <li><span style="background-color: #ffedd5; color: #9a3412; padding: 2px 5px; border-radius: 3px;"><b>🟠 ORANGE</b></span> : Maladie / Fièvre.</li>
        </ul>
        
        <h3>📅 Indicateurs Visuels (Dates)</h3>
        <ul>
            <li>✅: Vaccin déjà administré dans le centre (ou Externe).</li>
            <li>⏳: À faire aujourd'hui ou dans les jours qui viennent.</li>
            <li>⚠️: En retard (date prévue dépassée de plus d'une semaine).</li>
            <li>🚫: Vaccin non requis pour ce profil (ex: Ancien protocole).</li>
        </ul>
        
        <h3>⌨️ Raccourcis Clavier (Tableau)</h3>
        <ul>
            <li><b>'T' :</b> Marque le vaccin comme fait aujourd'hui (Done).</li>
            <li><b>'E' :</b> Marque le vaccin comme fait aujourd'hui en externe (Externe).</li>
            <li><b>'N' :</b> Naissance (HB Zéro).</li>
            <li><b>'R' :</b> Signaler comme Rupture de stock.</li>
            <li><b>'M' :</b> Signaler un report pour cause de Maladie.</li>
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
