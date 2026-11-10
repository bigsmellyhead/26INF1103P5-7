from abc import ABC
class Restriction(ABC):
    __name : str # e.g., "Peanuts", "Halal", "Low Sodium"
    #Initialise Restriction
    def __init__(self, name: str) -> None:
        self.__name = name
    
    @property
    def name(self) -> str:
        return self.__name

    def __eq__(self, other):
        if not isinstance(other, Restriction):
            return False
        return self.name.lower() == other.name.lower()

    def __hash__(self):
        return hash(self.name.lower())
    
    def __repr__(self): #For Readibility
        return f"{type(self).__name__}({self.name!r})"