"""
Pydantic schemas.

Request/response bodies are shaped to resemble FHIR resources
(resourceType, identifier, name, telecom, address, etc.) so that any
FHIR-aware client can consume this API with minimal translation, even
though internal storage uses a flatter relational model.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---------- Patient ----------

class PatientCreate(BaseModel):
    identifier: Optional[str] = Field(None, description="MRN or other external ID")
    family_name: str
    given_name: str
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address_line: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_postal_code: Optional[str] = None
    source_system: Optional[str] = None


class PatientUpdate(BaseModel):
    identifier: Optional[str] = None
    family_name: Optional[str] = None
    given_name: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address_line: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_postal_code: Optional[str] = None


class PatientOut(BaseModel):
    """Serialized as a minimal FHIR Patient resource."""

    resourceType: str = "Patient"
    id: str
    identifier: Optional[str] = None
    name: dict
    gender: Optional[str] = None
    birthDate: Optional[date] = None
    telecom: list[dict] = []
    address: Optional[dict] = None
    sourceSystem: Optional[str] = None

    @staticmethod
    def from_orm_model(p) -> "PatientOut":
        telecom = []
        if p.phone:
            telecom.append({"system": "phone", "value": p.phone})
        if p.email:
            telecom.append({"system": "email", "value": p.email})

        address = None
        if any([p.address_line, p.address_city, p.address_state, p.address_postal_code]):
            address = {
                "line": [p.address_line] if p.address_line else [],
                "city": p.address_city,
                "state": p.address_state,
                "postalCode": p.address_postal_code,
            }

        return PatientOut(
            id=p.id,
            identifier=p.identifier,
            name={"family": p.family_name, "given": [p.given_name]},
            gender=p.gender,
            birthDate=p.birth_date,
            telecom=telecom,
            address=address,
            sourceSystem=p.source_system,
        )


# ---------- Observation ----------

class ObservationCreate(BaseModel):
    patient_id: str
    code: str
    display: str
    value: str
    unit: Optional[str] = None
    status: str = "final"
    effective_datetime: Optional[datetime] = None


class ObservationOut(BaseModel):
    resourceType: str = "Observation"
    id: str
    status: str
    code: dict
    subject: dict
    valueString: str
    unit: Optional[str] = None
    effectiveDateTime: Optional[datetime] = None

    @staticmethod
    def from_orm_model(o) -> "ObservationOut":
        return ObservationOut(
            id=o.id,
            status=o.status,
            code={"coding": [{"code": o.code, "display": o.display}]},
            subject={"reference": f"Patient/{o.patient_id}"},
            valueString=o.value,
            unit=o.unit,
            effectiveDateTime=o.effective_datetime,
        )


# ---------- HL7 ingestion ----------

class HL7Message(BaseModel):
    message: str = Field(..., description="Raw HL7 v2.x message text (e.g. ADT^A01)")
