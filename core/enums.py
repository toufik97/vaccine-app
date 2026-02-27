from enum import Enum

class VaccineStatus(Enum):
    PENDING = "Pending"
    DONE = "Done"
    EXTERNE = "Externe"
    RUPTURE = "Rupture"
    MALADIE = "Maladie"

class PneumoProtocol(Enum):
    OLD = "Old"
    NEW = "New"
