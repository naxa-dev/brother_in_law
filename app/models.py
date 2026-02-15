"""
ORM model definitions for the AX dashboard application.

These SQLAlchemy models represent the core entities in the system:
snapshots, champions, strategy categories, projects, project events,
and audit logs. Composite primary keys are used where the combination
of fields uniquely identifies a row (for example, projects are scoped
per snapshot). Relationships are not defined explicitly in order to
keep the schema simple and avoid unnecessary eager loading. Instead
foreign keys are declared where appropriate and joins can be
constructed explicitly in queries.
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    PrimaryKeyConstraint,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


class Snapshot(Base):
    """Represents an uploaded snapshot of AX data.

    Each snapshot corresponds to a single Excel file upload. The
    snapshot_date field comes from the file name (YYYY-MM-DD). The
    uploaded_at field records when the snapshot was processed. The
    source_filename records the original file name for auditing.
    """

    __tablename__ = "snapshots"

    snapshot_id = Column(Integer, primary_key=True, index=True)
    snapshot_date = Column(Date, unique=True, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    source_filename = Column(String, nullable=False)


class Champion(Base):
    """Represents a Champion (owner) of AX projects.

    The `name` field is unique. The is_active flag allows champions to
    be deactivated without removing historical references. When a
    champion name appears in an upload that is not yet present in the
    table, a new row is created automatically.
    """

    __tablename__ = "champions"

    champion_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)


class StrategyCategory(Base):
    """Represents a strategy/category for AX projects.

    The `name` field is unique. New categories can be added via CRUD
    operations if required by the business. The is_active flag
    indicates whether the category is currently in use.
    """

    __tablename__ = "strategy_categories"

    strategy_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)


class Project(Base):
    """Represents a project within a specific snapshot.

    Projects are uniquely identified by the combination of snapshot_id
    and project_id. Many fields may be null to allow for incomplete
    data during initial uploads. The org_unit field denotes the
    performing department (e.g. 'ax그룹', '기타'). The current_status
    indicates the approval state such as '제안', '심의중', '승인(진행중)',
    '완료', or '보류'.
    """

    __tablename__ = "projects"
    snapshot_id = Column(Integer, ForeignKey("snapshots.snapshot_id"), nullable=False)
    project_id = Column(String, nullable=False)
    project_name = Column(String, nullable=False)
    champion_id = Column(Integer, ForeignKey("champions.champion_id"), nullable=True)
    strategy_id = Column(Integer, ForeignKey("strategy_categories.strategy_id"), nullable=True)
    org_unit = Column(String, nullable=True)
    current_status = Column(String, nullable=False)
    proposed_month = Column(String, nullable=True)
    approved_month = Column(String, nullable=True)

    __table_args__ = (
        PrimaryKeyConstraint("snapshot_id", "project_id", name="pk_projects"),
    )

    # Relationships for easy access in templates
    champion = relationship("Champion", lazy="joined")
    strategy = relationship("StrategyCategory", lazy="joined")


class ProjectMonthlyEvent(Base):
    """Represents monthly events for a project within a snapshot.

    Events denote whether a project was newly proposed or approved in a
    given month. They are uniquely identified by the combination of
    snapshot_id, month_key, and project_id. Champion_id is stored
    redundantly to capture the champion at the time of the event.
    """

    __tablename__ = "project_monthly_events"
    snapshot_id = Column(Integer, ForeignKey("snapshots.snapshot_id"), nullable=False)
    month_key = Column(String, nullable=False)  # YYYY-MM
    project_id = Column(String, nullable=False)
    champion_id = Column(Integer, ForeignKey("champions.champion_id"), nullable=True)
    is_new_proposal = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)
    note = Column(Text, nullable=True)

    __table_args__ = (
        PrimaryKeyConstraint("snapshot_id", "month_key", "project_id", name="pk_project_monthly_events"),
    )


class AuditLog(Base):
    """Records changes made via CRUD operations for auditing purposes.

    Each entry captures the entity affected, the action taken, the
    before and after state as JSON strings, the user (actor), and a
    timestamp. This table allows administrators to trace changes and
    satisfy governance requirements.
    """

    __tablename__ = "audit_logs"

    audit_id = Column(Integer, primary_key=True, index=True)
    snapshot_id = Column(Integer, ForeignKey("snapshots.snapshot_id"), nullable=False)
    entity_type = Column(String, nullable=False)  # e.g. 'project', 'event'
    entity_key = Column(String, nullable=False)   # e.g. '123' or '2026-02|123'
    action = Column(String, nullable=False)       # 'INSERT', 'UPDATE', 'DELETE'
    changed_fields = Column(String, nullable=True)  # comma-separated list
    before_json = Column(Text, nullable=True)
    after_json = Column(Text, nullable=True)
    actor = Column(String, nullable=False)
    acted_at = Column(DateTime, default=datetime.utcnow)