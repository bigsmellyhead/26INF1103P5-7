
from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    ForeignKey,
    DateTime,
    JSON,
    Text,
    func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.database import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    username: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )

    # The user's current allergies and dietary restrictions
    restrictions: Mapped[dict] = mapped_column(
        JSON, nullable=False
    )

    audit_logs: Mapped[list["AuditLog"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"), nullable=False
    )

    stall: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    dish: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    is_safe: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True
    )

    risk_level: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )

    risk_score: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    reasoning: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    # Save the restrictions that applied when this audit was performed
    restrictions_snapshot: Mapped[dict] = mapped_column(
        JSON, nullable=False
    )

    # Lists and nested structures are stored as JSON
    allergy_conflicts: Mapped[list] = mapped_column(
        JSON, nullable=False
    )

    hidden_ingredients: Mapped[list] = mapped_column(
        JSON, nullable=False
    )

    cross_contact_risks: Mapped[list] = mapped_column(
        JSON, nullable=False
    )

    ingredient_tree: Mapped[dict] = mapped_column(
        JSON, nullable=False
    )

    dietary_status: Mapped[dict] = mapped_column(
        JSON, nullable=False
    )

    flags: Mapped[list] = mapped_column(
        JSON, nullable=False
    )

    stall_knowledge: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )

    stall_specific_insights: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    user: Mapped["User"] = relationship(
        back_populates="audit_logs"
    )
