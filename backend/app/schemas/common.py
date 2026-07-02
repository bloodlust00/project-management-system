from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")

class ErrorDetail(BaseModel):
    field: Optional[str] = Field(None, description="The request parameter path where validation failed.")
    message: str = Field(..., description="Details outlining why the parameter is invalid.")
    type: Optional[str] = Field(None, description="The error type assertion identifier.")

class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[T] = None
    meta: dict = Field(default_factory=dict, description="Metadata dictionary matching request diagnostics.")

class APIErrorResponse(BaseModel):
    success: bool = False
    message: str = "An error occurred during request execution"
    errors: List[ErrorDetail] = []
    meta: dict = Field(default_factory=dict, description="Metadata error diagnostics info.")

class PaginationMeta(BaseModel):
    total: int = Field(..., description="Total count of active matching records.")
    page: int = Field(..., description="Current page index.")
    size: int = Field(..., description="Number of items per page.")
    pages: int = Field(..., description="Total number of matching pages.")

class PaginatedData(BaseModel, Generic[T]):
    items: List[T] = []
    pagination: PaginationMeta
