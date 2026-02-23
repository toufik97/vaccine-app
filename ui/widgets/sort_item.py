from PyQt6.QtWidgets import QTableWidgetItem
from datetime import datetime

class SortItem(QTableWidgetItem):
    def __lt__(self, other):
        col = self.tableWidget().column(self)
        t1 = self.text().strip()
        t2 = other.text().strip()
        
        if col == 0:
            try:
                id1, y1 = map(int, t1.split('/'))
                id2, y2 = map(int, t2.split('/'))
                if y1 != y2: return y1 < y2
                return id1 < id2
            except:
                pass
        elif col == 2:
            try:
                d1 = datetime.strptime(t1, "%d/%m/%Y")
                d2 = datetime.strptime(t2, "%d/%m/%Y")
                return d1 < d2
            except:
                pass
        return t1.lower() < t2.lower()
