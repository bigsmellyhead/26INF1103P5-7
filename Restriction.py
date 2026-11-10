class Restriction:
    __name : str # e.g., "Peanuts", "Halal", "Low Sodium"
    #Initialise Restriction
    def __init__(self, name: str) -> None:
        self.__name = name
    @property
    def name(self) -> str:
        return self.__name