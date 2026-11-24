from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    product_name: str = Field(min_length=1)
    content: str = Field(min_length=1)
    target: str = Field(min_length=1)


class AnalyzeResponse(BaseModel):
    session_id: str
    report_text: str


class SessionRequest(BaseModel):
    session_id: str = Field(min_length=1)


class TitleResponse(BaseModel):
    session_id: str
    title_text: str


class DifferentiateResponse(BaseModel):
    session_id: str
    title_text: str


class RefineRequest(SessionRequest):
    feedback: str = Field(min_length=1)


class RefineResponse(BaseModel):
    session_id: str
    title_text: str
