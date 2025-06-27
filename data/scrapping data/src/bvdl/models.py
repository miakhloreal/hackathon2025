"""Data models for Bazaarvoice API responses."""

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ApiError(BaseModel):
    """Represents an error returned by the Bazaarvoice API."""
    
    code: str = Field(alias="Code")
    message: str = Field(alias="Message")


class ApiItem(BaseModel):
    """Represents a product item from the Bazaarvoice API."""
    
    id: str = Field(alias="Id")
    
    model_config = {"extra": "allow"}  # Allow additional fields to be captured


class ApiPage(BaseModel):
    """Represents a page of results from the Bazaarvoice API."""
    
    total_results: int = Field(alias="TotalResults")
    results: List[ApiItem] = Field(alias="Results", default_factory=list)
    errors: List[ApiError] = Field(alias="Errors", default_factory=list)