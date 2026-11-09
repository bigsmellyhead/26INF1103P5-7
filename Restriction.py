from RestrictionCategory import RestrictionCategory
class Restriction:
    __name : str # e.g., "Peanuts", "Halal", "Low Sodium"
    __category: RestrictionCategory # Specifies which bucket it falls into. eg. Allergy, Dietary restriction or others

    #Initialise Restriction
    def __init__(self, name, category):
        self.__name = name
        self.__category = category

    @property
    def name(self):
        return self.__name

    @property 
    def category(self):
        return self.category