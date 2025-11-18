"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Careers-related schemas

class Job(BaseModel):
    """
    Job postings
    Collection name: "job"
    """
    title: str = Field(..., description="Role title")
    department: str = Field(..., description="Department or team")
    location: str = Field(..., description="Location, e.g., Brighton, UK / Remote")
    employment_type: str = Field(..., description="Full-time, Part-time, Contract")
    description: str = Field(..., description="Short role summary")
    responsibilities: List[str] = Field(default_factory=list, description="Key responsibilities")
    requirements: List[str] = Field(default_factory=list, description="Key requirements")
    salary_range: Optional[str] = Field(None, description="e.g., £40k–£55k DOE")
    remote: bool = Field(False, description="Is this remote-friendly?")

class Application(BaseModel):
    """
    Candidate applications
    Collection name: "application"
    """
    job_id: str = Field(..., description="ID of the job applied for")
    name: str = Field(..., description="Applicant full name")
    email: str = Field(..., description="Applicant email")
    phone: Optional[str] = Field(None, description="Phone number")
    linkedin: Optional[HttpUrl] = Field(None, description="LinkedIn profile URL")
    portfolio: Optional[HttpUrl] = Field(None, description="Portfolio or website URL")
    cover_letter: Optional[str] = Field(None, description="Short cover letter or note")
    consent: bool = Field(True, description="Consent to store data for recruitment purposes")

# Add your own schemas here:
# --------------------------------------------------

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
