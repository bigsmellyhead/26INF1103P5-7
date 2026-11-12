# Data.py
from abc import ABC, abstractmethod
from UserProfile import UserProfile
# ==========================================
# AUDIT DATA BRANCH
# ==========================================

class BaseAuditData():
    _user_profile: UserProfile
    _stall : str
    _dish : str

    def __init__(self, user_profile: UserProfile, stall: str, dish: str):
        self._user_profile = user_profile
        self._stall = stall
        self._dish = dish
        
    @property
    def user_profile(self) -> UserProfile:
        return self._user_profile

    @property
    def stall(self) -> str:
        return self._stall

    @property
    def dish(self) -> str:
        return self._dish

    def to_dict(self) -> dict:
        return {
            "username": self._user_profile.username,
            "restrictions": self._user_profile.restrictions,
            "stall": self._stall,
            "dish": self._dish,
        }

# Sent by AIManager to LogicManager: the AI's validated reply plus what logic needs to build the final record
class AIAuditData(BaseAuditData):
    _ai_result: dict

    def __init__(self, user_profile: UserProfile, stall: str, dish: str, ai_result: dict,):
        super().__init__(user_profile, stall, dish)
        self._ai_result = ai_result

    @property
    def ai_result(self) -> dict:
        return self._ai_result

    def to_dict(self) -> dict:
        return {
            **super().to_dict(), 
            "ai_result": self._ai_result
                }



# Sent by LogicManager once the rules have been applied; used for displaying and saving the audit
class ResultAuditData(BaseAuditData):
    _result: dict

    def __init__(self, user_profile: UserProfile, stall: str, dish: str, result: dict):
        super().__init__(user_profile, stall, dish)
        self._result = result

    @property
    def result(self) -> dict:
        return self._result

    # Same flat record so the saved data keeps the same shape
    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            **self._result,
        }
