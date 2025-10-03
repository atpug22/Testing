from pydantic import BaseModel
from typing import Annotated


class TaskCreate(BaseModel):
    title: Annotated[str, "Title must be 1-100 characters"]
    description: Annotated[str, "Description must be 1-1000 characters"]
