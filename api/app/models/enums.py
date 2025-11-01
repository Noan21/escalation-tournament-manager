from __future__ import annotations

from enum import StrEnum


class OrganizationVisibility(StrEnum):
    PRIVATE = "private"
    UNLISTED = "unlisted"
    PUBLIC = "public"


class SeasonStatus(StrEnum):
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETE = "complete"
    ARCHIVED = "archived"


class ParticipantStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    RETIRED = "retired"


class TeamStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class TeamMemberRole(StrEnum):
    CAPTAIN = "captain"
    MEMBER = "member"
    ALTERNATE = "alternate"


class EventStatus(StrEnum):
    DRAFT = "draft"
    REGISTRATION = "registration"
    ACTIVE = "active"
    COMPLETE = "complete"
    ARCHIVED = "archived"


class StageStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"


class RegistrationSubjectType(StrEnum):
    PARTICIPANT = "participant"
    TEAM = "team"


class RegistrationStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    WITHDRAWN = "withdrawn"


class CheckInMethod(StrEnum):
    SELF_SERVICE = "self_service"
    ADMIN_MANUAL = "admin_manual"
    KIOSK = "kiosk"


class RoundStatus(StrEnum):
    SCHEDULED = "scheduled"
    PAIRING = "pairing"
    ACTIVE = "active"
    LOCKED = "locked"
    PUBLISHED = "published"


class MatchState(StrEnum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BYE = "bye"
    FORFEIT = "forfeit"
    CANCELLED = "cancelled"


class MatchOutcome(StrEnum):
    WIN_A = "win_a"
    WIN_B = "win_b"
    DRAW = "draw"
    PENDING = "pending"


class StandingSubjectType(StrEnum):
    PARTICIPANT = "participant"
    TEAM = "team"


class HeadToHeadResult(StrEnum):
    AHEAD = "ahead"
    BEHIND = "behind"
    TIED = "tied"


class NotificationSubjectType(StrEnum):
    PARTICIPANT = "participant"
    TEAM = "team"
    ADMIN = "admin"


class NotificationChannel(StrEnum):
    EMAIL = "email"
    DISCORD_WEBHOOK = "discord_webhook"
    SLACK_WEBHOOK = "slack_webhook"
    SMS = "sms"
    WEBHOOK = "webhook"


class NotificationStatus(StrEnum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"


class CleanupTarget(StrEnum):
    STALE_REGISTRATIONS = "stale_registrations"
    ARCHIVED_EVENTS = "archived_events"
    LOGS = "logs"
    NOTIFICATIONS = "notifications"
    SESSIONS = "sessions"


class ArchiveMode(StrEnum):
    SOFT_DELETE = "soft_delete"
    MOVE_TO_COLD_STORAGE = "move_to_cold_storage"
    EXPORT = "export"


class MigrationStatus(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"


__all__ = [
    "ArchiveMode",
    "CheckInMethod",
    "CleanupTarget",
    "EventStatus",
    "HeadToHeadResult",
    "MatchOutcome",
    "MatchState",
    "MigrationStatus",
    "NotificationChannel",
    "NotificationStatus",
    "NotificationSubjectType",
    "OrganizationVisibility",
    "ParticipantStatus",
    "RegistrationStatus",
    "RegistrationSubjectType",
    "RoundStatus",
    "SeasonStatus",
    "StageStatus",
    "StandingSubjectType",
    "TeamMemberRole",
    "TeamStatus",
]
