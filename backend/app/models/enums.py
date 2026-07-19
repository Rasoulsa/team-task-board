from enum import StrEnum


class OrganizationRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"
    GUEST = "guest"


class InvitationStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


class NotificationType(StrEnum):
    CARD_ASSIGNED = "card_assigned"
    CARD_MENTIONED = "card_mentioned"
    DUE_DATE_REMINDER = "due_date_reminder"
    ORGANIZATION_INVITATION = "organization_invitation"