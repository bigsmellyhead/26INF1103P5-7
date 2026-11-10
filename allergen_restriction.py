from allergen_grp import AllergenGrp
from severity_level import SeverityLevel
from restriction import Restriction
class AllergenRestriction(Restriction):
    __allergen_grp: AllergenGrp
    __severity_level: SeverityLevel

    def __init__(self, name, allergen_grp: AllergenGrp, severity_level: SeverityLevel) -> None:
        super().__init__(name)
        self.__allergen_grp = allergen_grp
        self.__severity_level = severity_level

    @property
    def allergen_grp(self) -> AllergenGrp:
        return self.__allergen_grp

    @property
    def severity_level(self) -> SeverityLevel:
        return self.__severity_level