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

class Gender(Enum):
    MALE = "M"
    FEMALE = "F"
    
    @classmethod
    def from_ui(cls, text: str) -> str:
        text = text.lower().strip()
        if text.startswith("m") or text == "garçon":
            return cls.MALE.value
        elif text.startswith("f") or text == "fille":
            return cls.FEMALE.value
        raise ValueError(f"Sexe non reconnu: {text}")

    @classmethod
    def to_ui(cls, value: str) -> str:
        if value == cls.MALE.value:
            return "Masculin"
        elif value == cls.FEMALE.value:
            return "Féminin"
        return value

class InjectionSite(Enum):
    LEFT_THIGH_ANTERO = "Cuisse Gauche (Antérolatérale)"
    RIGHT_THIGH_ANTERO = "Cuisse Droite (Antérolatérale)"
    LEFT_DELTOID_SC = "Deltoïde Gauche (Sous-cutanée)"
    RIGHT_DELTOID_SC = "Deltoïde Droit (Sous-cutanée)"
    DELTOID = "Deltoïde (IM)"
    ORAL = "Oral"
    INTRADERMAL_LEFT_ARM = "Intradermique (Bras Gauche)"

class VaccineType(Enum):
    LIVE_ATTENUATED = "Vivant Atténué"
    INACTIVATED = "Inactivé"
    TOXOID = "Anatoxine"
    SUBUNIT = "Sous-unité/Conjugué"
