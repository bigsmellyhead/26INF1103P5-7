from Restriction import Restriction
class UserProfile:
    __username : str
    __restrictions: set[Restriction]

    def __init__(self, username: str, restrictions: set[Restriction]):
        self.__username = username
        self.__restrictions = restrictions

    @property
    def username(self):
        return self.__username

    @property
    def restrictions(self):
        return self.__restrictions