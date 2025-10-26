from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional

# Each class name will become a collection name in lowercase

class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    category: str = Field(..., description="Category (e.g., Timber & Plywood, Steel & Rebar)")
    material_type: Optional[str] = Field(None, description="Material type/family")
    size: Optional[str] = Field(None, description="Size or dimensions")
    weight: Optional[str] = Field(None, description="Weight or density")
    images: List[str] = Field(default_factory=list, description="Image URLs")
    specs: Optional[dict] = Field(default_factory=dict, description="Key specs map")
    is_active: bool = Field(default=True, description="Visible on site")

class Project(BaseModel):
    title: str = Field(..., description="Project title")
    description: Optional[str] = Field(None, description="Short description")
    materials_used: List[str] = Field(default_factory=list, description="Materials used")
    images: List[str] = Field(default_factory=list, description="Gallery images")
    is_featured: bool = Field(default=False, description="Show on homepage preview")
    is_active: bool = Field(default=True)

class QuoteRequest(BaseModel):
    name: str
    company: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    message: Optional[str] = None
    product: Optional[str] = None

class ContactMessage(BaseModel):
    name: str
    company: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    message: str
    interest: Optional[str] = None
