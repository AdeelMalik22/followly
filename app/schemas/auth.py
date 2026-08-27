from pydantic import BaseModel, EmailStr, Field, model_validator

class UserCreate(BaseModel):
    email: EmailStr
    owner_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8)
    confirm_password: str = Field(min_length=8)
    business_name: str = Field(min_length=2, max_length=200)
    industry: str = "Dental Clinic"
    terms_accepted: bool

    @model_validator(mode="after")
    def passwords_match_and_terms_accepted(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        if not self.terms_accepted:
            raise ValueError("Terms must be accepted")
        return self

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    email: str
    business_id: int
    role: str

    class Config:
        from_attributes = True
