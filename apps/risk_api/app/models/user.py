from pydantic import BaseModel, EmailStr, Field, ConfigDict 

class UserSchema(BaseModel):
    fullname: str = Field(...)
    email: EmailStr = Field(...)
    password: str = Field(...)

        
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "fullname": "Arthur Griffith",
                "email": "arthur@gmail.com",
                "password": "someweakpassword"
            }
        }
    )

class UserLoginSchema(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(...)
        
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "arthur@gmail.com",
                "password": "someweakpassword"
            }
        }
    )