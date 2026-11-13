# data_manager.py
from sqlalchemy import select, func

from database.database import SessionLocal, init_db
from database.models import User, AuditLog
from UserProfile import UserProfile
from profile_serializer import ProfileSerializer


# data_manager is the only class that has access to the database through SQLAlchemy. 
# Profiles are serialized/deserialized at the border, the rest of the code never sees raw data.
# After deserialization, rest of the code retrieves UserProfile objects, which are immutable and do not know about the database.

class DataManager:

    def __init__(self):
        # Composition: DataManager creates and owns its serializer
        self._serializer = ProfileSerializer()

    # creates the database tables if they do not exist yet. Does not delete existing data.
    def initialize_database(self):
        """Initialize the MySQL database tables."""
        init_db()

    # find user by username, returns None if not found. Case-insensitive.
    def _find_user(self, session, username):
        return session.scalar(
            select(User).where(func.lower(User.username) == username.strip().lower())
        )

    # takes user object from database, coverts to UserProfile object. Returns None if user is None.
    def _to_profile(self, user) -> UserProfile:
        return self._serializer.deserialize(user.username, user.restrictions)

    # load a user's profile as a UserProfile object, or None if they are new.
    def get_user_profile(self, username):
        if not username or not username.strip():
            return None

        with SessionLocal() as session:
            user = self._find_user(session, username)
            if user is None:
                return None
            return self._to_profile(user)

    # Register a new user or update their restrictions (serialize only here).
    def save_user_profile(self, profile: UserProfile):
        if not isinstance(profile, UserProfile):
            raise ValueError("save_user_profile expects a UserProfile.")
        if not profile.username or not profile.username.strip():
            raise ValueError("Username cannot be empty.")

        restrictions = self._serializer.serialize(profile)

        with SessionLocal.begin() as session:
            user = self._find_user(session, profile.username)
            if user is None:
                session.add(User(username=profile.username.strip(), restrictions=restrictions))
            else:
                user.restrictions = restrictions

    
    # adds a new audit record to the database
    def append_audit_log(self, profile: UserProfile, audit_record: dict):
        if not isinstance(profile, UserProfile):
            raise ValueError("append_audit_log expects a UserProfile.")
        if not isinstance(audit_record, dict):
            raise ValueError("Audit record must be a dictionary.")

        restrictions = self._serializer.serialize(profile)

        with SessionLocal.begin() as session:
            user = self._find_user(session, profile.username)

            # Create the user if they do not exist yet
            if user is None:
                user = User(username=profile.username.strip(), restrictions=restrictions)
                session.add(user)

            session.add(AuditLog(
                user=user,
                stall=audit_record.get("stall"),
                dish=audit_record.get("dish"),
                is_safe=audit_record.get("is_safe"),
                risk_level=audit_record.get("risk_level"),
                risk_score=audit_record.get("risk_score"),
                reasoning=audit_record.get("reasoning"),
                restrictions_snapshot=restrictions,
                allergy_conflicts=audit_record.get("allergy_conflicts") or [],
                hidden_ingredients=audit_record.get("hidden_ingredients") or [],
                cross_contact_risks=audit_record.get("cross_contact_risks") or [],
                ingredient_tree=audit_record.get("ingredient_tree") or {},
                dietary_status=audit_record.get("dietary_status") or {},
                flags=audit_record.get("flags") or [],
                stall_knowledge=audit_record.get("stall_knowledge"),
                stall_specific_insights=audit_record.get("stall_specific_insights"),
            ))

    # Below are functions used for admin seaches
    # search by username, returns UserProfile objects. Case-insensitive partial match.
    def search_user_profiles(self, name):
        if not name or not name.strip():
            return []

        with SessionLocal() as session:
            users = session.scalars(
                select(User)
                .where(func.lower(User.username).contains(name.strip().lower()))
                .order_by(User.username)
            ).all()
            return [self._to_profile(user) for user in users]

    # search for users who have a matching allergy or dietary restriction. Returns UserProfile objects.
    def search_dietary_restriction(self, restriction):
        if not restriction or not restriction.strip():
            return []

        search_term = restriction.strip().casefold()

        with SessionLocal() as session:
            profiles = [self._to_profile(user) for user in session.scalars(select(User)).all()]

        return [
            profile for profile in profiles
            if any(search_term in item.casefold() for item in profile.all_restriction_names())
        ]

    # filter audit history by selected restrictions, returns list of (AuditLog, User) tuples.
    def filter_audit_history_by_restrictions(self, selected_items):
        matches = []
        selected_lower = {item.casefold() for item in selected_items}

        with SessionLocal() as session:
            rows = session.execute(
                select(AuditLog, User)
                .join(User, AuditLog.user_id == User.user_id)
                .order_by(AuditLog.created_at.desc())
            ).all()

            for audit, user in rows:
                # Reuse the serializer so the snapshot is cleaned the same way as a profile
                snapshot = self._serializer.deserialize(user.username, audit.restrictions_snapshot)
                recorded_lower = {item.casefold() for item in snapshot.all_restriction_names()}

                if selected_lower & recorded_lower:
                    matches.append((audit, user))

        return matches
