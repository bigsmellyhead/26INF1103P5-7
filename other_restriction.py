
from restriction import Restriction
from severity_level import SeverityLevel

class OtherRestriction(Restriction):
    __severity_level: SeverityLevel #if nothing is passed in, it stays as None

    def __init__(self, name, severity_level: SeverityLevel = None) -> None: #parent class to store name
        super().__init__(name)
        self.__severity_level = severity_level #store severity privately

    @property # There is no setter, the level cannot be changed after the object is created
    def severity_level(self) -> SeverityLevel:
        return self.__severity_level