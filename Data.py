# Data.py
from abc import ABC, abstractmethod

# Base class for everything sent through the Bus
# It cannot be created directly: every payload must be able to turn itself into a dictionary
class Data(ABC):

    @abstractmethod
    def to_dict(self) -> dict:
        pass


# Sent by IOManager to ask AIManager for an audit
class AIQueryData(Data):
    _username : str
    _stall : str
    _dish : str
    _restrictions: dict #To change into Restrictions class

    def __init__(self, username: str, stall: str, dish: str, restrictions: dict):
        self._username = username
        self._stall = stall
        self._dish = dish
        self._restrictions = restrictions

    @property
    def username(self) -> str:
        return self._username

    @property
    def stall(self) -> str:
        return self._stall

    @property
    def dish(self) -> str:
        return self._dish

    @property
    def restrictions(self) -> dict:
        return self._restrictions

    @property
    def to_dict(self) -> dict:
        return {
            "username": self._username,
            "stall": self._stall,
            "dish": self._dish,
            "restrictions": self._restrictions,
        }


# Sent by AIManager to LogicManager: the AI's validated reply plus what logic needs to build the final record
class ValidateProcessData(Data):
    _ai_result: dict
    _restrictions: dict
    _username: str
    _stall: str
    _dish: str

    def __init__(self, ai_result: dict, restrictions: dict, username: str, stall: str, dish: str):
        self._ai_result = ai_result
        self._restrictions = restrictions
        self._username = username
        self._stall = stall
        self._dish = dish

    @property
    def ai_result(self) -> dict:
        return self._ai_result

    @property
    def restrictions(self) -> dict:
        return self._restrictions

    @property
    def username(self) -> str:
        return self._username

    @property
    def stall(self) -> str:
        return self._stall

    @property
    def dish(self) -> str:
        return self._dish

    def to_dict(self) -> dict:
        return {
            "ai_result": self._ai_result,
            "restrictions": self._restrictions,
            "username": self._username,
            "stall": self._stall,
            "dish": self._dish,
        }


# Sent by LogicManager once the rules have been applied; used for displaying and saving the audit
class AuditResultData(Data):
    _username : str
    _stall : str
    _dish : str
    _restrictions: dict #To change into Restrictions class
    _result : dict

    def __init__(self, username: str, stall: str, dish: str, restrictions: dict, result: dict):
        self._username = username
        self._stall = stall
        self._dish = dish
        self._restrictions = restrictions
        self._result = result

    @property
    def username(self) -> str:
        return self._username
    
    @property
    def stall(self) -> str:
        return self._stall

    @property
    def dish(self) -> str:
        return self._dish

    @property
    def restrictions(self) -> dict:
        return self._restrictions

    @property
    def result(self) -> dict:
        return self._result

    # Same flat record so the saved data keeps the same shape
    def to_dict(self) -> dict:
        return {
            "username": self._username,
            "restrictions": self._restrictions,
            "stall": self._stall,
            "dish": self._dish,
            **self._result,
        }


# Sent by AIManager when one API attempt fails
class AttemptErrorData(Data):
    _attempt : str
    _max_tries : int
    _error : str

    def __init__(self, attempt: int, max_tries: int, error: str):
        self._attempt = attempt
        self._max_tries = max_tries
        # str() so an exception object can be passed in directly
        self._error = str(error)

    @property
    def attempt(self) -> int:
        return self._attempt

    @property
    def max_tries(self) -> int:
        return self._max_tries

    @property
    def error(self) -> str:
        return self._error

    def to_dict(self) -> dict:
        return {
            "attempt": self._attempt,
            "max_tries": self._max_tries,
            "error": self._error,
        }


# Sent by AIManager when the API key is missing
class APIKeyErrorData(Data):
    _error_msg : str
    def __init__(self, error_msg: str):
        self._error_msg = error_msg

    @property
    def error_msg(self) -> str:
        return self._error_msg

    def to_dict(self) -> dict:
        return {"error_msg": self._error_msg}
