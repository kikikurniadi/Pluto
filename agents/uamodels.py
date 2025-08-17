from pydantic import BaseModel


class StoreChat(BaseModel):
    entry_id: str | None = None
    entry: str
