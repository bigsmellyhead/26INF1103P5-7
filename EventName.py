from enum import Enum
class EventName(Enum):
    APIKEYERROR = 1,
    ATTEMPTERROR = 2,
    AUDITRESULTDATA = 3,
    AIQUERYDATA = 4,
    VALIDATEPROCESSDATA = 5
    SAVETODATABASE = 6