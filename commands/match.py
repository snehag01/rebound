from typing import List, Dict, Any
from pydantic import BaseModel, Field

class Skill(BaseModel):
    name: str # e.g., "Python", "Django", "AWS"
    level: float = 0.0 # Proficiency (0.1 to 1.0)

class JobPosting(BaseModel):
    """Standardized representation of any job posting."""
    job_id: str
    title: str
    company: str
    location: str
    description: str
    required_skills: List[Skill] = Field(default=[])
    responsibilities: List[str] = Field(default_=[] )
    experience_years: float | None = None
    salary_range: str | None = None

# Example Adapter Output Structure
class SourceAdapterInterface:
    """Abstract base class for connecting to external data sources."""
    @staticmethod
    def normalize_source(data: Dict[str, Any]) -> List[JobPosting]:
        """
        Takes raw source API/DB payload and converts it into a list of normalized JobPostings.
        Implementation must handle unique mappings (e.g., 'proficient' -> 0.7).
        """
        raise NotImplementedError("Subclasses must implement normalization logic.")

# Example concrete implementation stub (for demonstration)
class LinkedInAdapter(SourceAdapterInterface):
    @staticmethod
    def normalize_source(data: Dict[str, Any]) -> List[JobPosting]:
        # Mock conversion logic from complex LinkedIn JSON structure
        print("INFO: Running LinkedIn data parsing and normalization...")
        return [
            JobPosting(
                job_id="LNK123",
                title="Senior Backend Engineer (Python/AWS)",
                company="TechGiant Inc.",
                location="Remote",
                description="Develop microservices using Python, focusing on cloud architecture...",
                required_skills=[
                    Skill(name="Python", level=0.9),
                    Skill(name="AWS", level=0.8),
                    Skill(name="SQLAlchemy", level=0.7)
                ],
                responsibilities=["Build APIs", "Manage Cloud Infrastructure"],
                experience_years=5.0,
            )
        ]