from pydantic import BaseModel, Field, field_validator

MAX_MESSAGE_LENGTH = 4000


class ChatRequest(BaseModel):
    thread_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1, max_length=MAX_MESSAGE_LENGTH)
    selected_files: list[str] | None = None
    page: int | None = None

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("message must not be blank or whitespace-only")
        return stripped

    @field_validator("thread_id")
    @classmethod
    def thread_id_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("thread_id must not be blank or whitespace-only")
        return stripped

class ChatResponse(BaseModel):
    thread_id: str
    reply: str