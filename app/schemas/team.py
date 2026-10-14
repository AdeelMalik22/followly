from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class TeamInvitationCreate(BaseModel):
    email: EmailStr
    role: str = Field(default="staff", pattern="^(admin|staff)$")


class TeamInvitationResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    status: str
    expires_at: datetime
    invitation_token: str | None = None

    class Config:
        from_attributes = True


class TeamInvitationAccept(BaseModel):
    token: str = Field(min_length=20)
    name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8)


class TeamRoleUpdate(BaseModel):
    role: str = Field(pattern="^(admin|staff)$")
