# python_backend/models/Untels_models.py
from pydantic import BaseModel, Field
from typing import Optional

# Represents a single entry of Untels Information (e.g., from ROF, MOF, TUPA)
class UntelsInformation(BaseModel):
    title: str = Field(..., description="The title or name of the Untels document/procedure.")
    content: str = Field(..., description="The detailed content or description of the information.")
    source: Optional[str] = Field(None, description="The source document (e.g., ROF, MOF, TUPA, D.S. N°XXX).")
    section: Optional[str] = Field(None, description="The specific section or article within the source document.")
    keywords: Optional[list[str]] = Field(default_factory=list, description="Keywords to help with search and categorization.")

    class Config:
        schema_extra = {
            "example": {
                "title": "Registro Único de Contribuyentes (RUC)",
                "content": "El Registro Único de Contribuyentes (RUC) es el padrón que contiene los datos de identificación de la actividad económica y tributaria de los contribuyentes, administrado por la SUNAT.",
                "source": "TUPA",
                "section": "Procedimiento 001",
                "keywords": ["RUC", "SUNAT", "contribuyente", "trámite"]
            }
        }

# Represents a search query for Untels information
class UntelsQuery(BaseModel):
    query: str = Field(..., description="The user's query for Untels information.")
    max_results: int = Field(5, description="Maximum number of results to return.", ge=1, le=10)

# Represents a response containing relevant Untels information
class UntelsInfoResponse(BaseModel):
    query: str = Field(..., description="The original query from the user.")
    results: list[UntelsInformation] = Field(default_factory=list, description="List of relevant Untels information entries.")
    message: str = Field("Información encontrada.", description="A message describing the result of the search.")
    error: Optional[str] = Field(None, description="Error message if the search failed.")