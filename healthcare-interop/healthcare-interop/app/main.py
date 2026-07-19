"""
Healthcare System Interoperability - base project.

Demonstrates the core building blocks of healthcare interoperability:
  1. A FHIR-shaped REST API for Patient and Observation resources.
  2. HL7 v2 <-> FHIR conversion, so a legacy HL7-speaking system (e.g. a
     hospital ADT feed) and a modern FHIR-based system can exchange
     patient data through this service.

Run with:
    uvicorn app.main:app --reload

Then open http://127.0.0.1:8000/docs for interactive API docs.
"""
from fastapi import FastAPI

from app.database import Base, engine
from app.routers import hl7, observations, patients

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Healthcare System Interoperability",
    description=(
        "Base project demonstrating interoperability between a legacy "
        "HL7 v2 system and a modern FHIR-based system via a shared "
        "Patient/Observation data model."
    ),
    version="1.0.0",
)

app.include_router(patients.router)
app.include_router(observations.router)
app.include_router(hl7.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "status": "ok",
        "service": "Healthcare System Interoperability",
        "docs": "/docs",
    }
