from Restriction import Restriction
from severity_level import SeverityLevel

class OtherRestriction(Restriction):
    __severity_level: SeverityLevel

    def __init__(self, name, severity_level: SeverityLevel = None) -> None:
        super().__init__(name)
        self.__severity_level = severity_level

    @property
    def severity_level(self) -> SeverityLevel:
        return self.__severity_level