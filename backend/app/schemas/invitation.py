import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.enums import InvitationStatus, OrganizationRole


class InvitationCreate(BaseModel):
    email: EmailStr
    role: OrganizationRole = OrganizationRole.MEMBER


class InvitationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    inviter_id: uuid.UUID
    email: EmailStr
    token: str
    role: OrganizationRole
    status: InvitationStatus
    expires_at: datetime
    accepted_at: datetime | None
    created_at: datetime


class InvitationRevokeResponse(BaseModel):
    message: str
