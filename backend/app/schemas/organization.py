from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.enums import OrganizationRole


class OrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    role: OrganizationRole  # Current user's role in this org
    created_at: datetime
    updated_at: datetime


class OrganizationMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    organization_id: UUID
    full_name: str
    email: EmailStr
    role: OrganizationRole
    created_at: datetime


class MyMembershipResponse(BaseModel):
    organization_id: UUID
    role: OrganizationRole