from pydantic import BaseModel
from typing import List, Optional, Literal

class FileNode(BaseModel):
    name: str
    path: str
    type: Literal["file", "directory"]
    children: Optional[List["FileNode"]] = None
    size: Optional[int] = None

class FileContentRequest(BaseModel):
    path: str

class FileContentResponse(BaseModel):
    path: str
    content: str
    encoding: str = "utf-8"

class FileSaveRequest(BaseModel):
    path: str
    content: str
