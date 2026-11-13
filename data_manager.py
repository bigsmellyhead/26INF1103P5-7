
from sqlalchemy import select, func

from database.database import SessionLocal, init_db
from database.models import User, AuditLog

class DataManager:

    def __init__(self):
        pass

    def initialize_database(self):
        """Initialize the MySQL database tables."""
        init_db()


    def get_user_profile(self, username):
        """Retrieve a user's profile using their username."""
        if not username or not username.strip():
            return None

        normalized_username = username.strip().lower()

        with SessionLocal() as session:
            user = session.scalar(
                select(User).where(
                    func.lower(User.username) == normalized_username
                )
            )

            if user is None:
                return None

            return {
                "username": user.username,
                "restrictions": user.restrictions
            }


    def save_user_profile(self, username, restrictions):
        """Register a new user or update their restrictions."""
        if not username or not username.strip():
            raise ValueError("Username cannot be empty.")

        if not isinstance(restrictions, dict):
            raise ValueError("Restrictions must be a dictionary.")

        normalized_username = username.strip().lower()

        with SessionLocal.begin() as session:
            user = session.scalar(
                select(User).where(
                    func.lower(User.username) == normalized_username
                )
            )

            if user is None:
                user = User(
                    username=username.strip(),
                    restrictions=restrictions
                )
                session.add(user)
            else:
                user.restrictions = restrictions


    def append_audit_log(self, audit_record):
        """Save an audit result into MySQL."""
        if not isinstance(audit_record, dict):
            raise ValueError("Audit record must be a dictionary.")

        username = audit_record.get("username")

        if not isinstance(username, str) or not username.strip():
            raise ValueError("Audit record must contain a valid username.")

        restrictions = audit_record.get("restrictions") or {
            "allergies": [],
            "dietary_restrictions": [],
            "other": []
        }

        if not isinstance(restrictions, dict):
            raise ValueError("Restrictions must be a dictionary.")

        normalized_username = username.strip().lower()

        with SessionLocal.begin() as session:
            user = session.scalar(
                select(User).where(
                    func.lower(User.username) == normalized_username
                )
            )

            # Create the user if they do not exist yet
            if user is None:
                user = User(
                    username=username.strip(),
                    restrictions=restrictions
                )
                session.add(user)

            # Store the audit result in the appropriate columns
            audit = AuditLog(
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
                stall_specific_insights=audit_record.get(
                    "stall_specific_insights"
                )
            )

            session.add(audit)

    def search_user_profiles(self, name):
        """Find user profiles by a partial username match."""
        if not name or not name.strip():
            return []

        search_term = name.strip().casefold()

        with SessionLocal() as session:
            users = session.scalars(
                select(User)
                .where(
                    func.lower(User.username).contains(search_term)
                )
                .order_by(User.username)
            ).all()

            return users


    def search_dietary_restriction(self, restriction):
        """Find users who have a matching allergy or dietary restriction."""
        if not restriction or not restriction.strip():
            return []

        search_term = restriction.strip().casefold()

        with SessionLocal() as session:
            users = session.scalars(select(User)).all()

            matching_users = []

            for user in users:
                user_restrictions = user.restrictions or {}

                for category in ("allergies", "dietary_restrictions", "other"):
                    items = user_restrictions.get(category, [])

                    if isinstance(items, str):
                        items = [items]

                    if any(
                        search_term in item.casefold()
                        for item in items
                        if isinstance(item, str)
                    ):
                        matching_users.append(user)
                        break

            return matching_users


    def filter_audit_history_by_restrictions(self, selected_items):
        """Find audit records containing any selected restriction."""

        matches = []

        with SessionLocal() as session:
            rows = session.execute(
                select(AuditLog, User)
                .join(User, AuditLog.user_id == User.user_id)
                .order_by(AuditLog.created_at.desc())
            ).all()

            for audit, user in rows:
                restrictions = audit.restrictions_snapshot or {}

                recorded_items = []

                for category in (
                    "allergies",
                    "dietary_restrictions",
                    "other"
                ):
                    items = restrictions.get(category, [])

                    if isinstance(items, str):
                        items = [items]

                    recorded_items.extend(
                        item for item in items
                        if isinstance(item, str)
                    )

                recorded_lower = {
                    item.casefold() for item in recorded_items
                }

                if any(
                    item.casefold() in recorded_lower
                    for item in selected_items
                ):
                    matches.append((audit, user))

        return matches
