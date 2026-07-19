"""
ORM models.

These are intentionally simplified relative to the full FHIR spec (which
has dozens of optional fields per resource) but capture the core elements
needed to demonstrate real interoperability: stable identifiers, name,
demographics, contact info, and linked clinical Observations.
"""
import uuid

from sqlalchemy import Column, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Patient(Base):
    __tablename__ = "patients"

    id = Column(String, primary_key=True, default=_uuid)
    # External identifier, e.g. MRN issued by a source system (HL7 PID-3)
    identifier = Column(String, unique=True, index=True, nullable=True)
    family_name = Column(String, nullable=False)
    given_name = Column(String, nullable=False)
    gender = Column(String, nullable=True)  # male | female | other | unknown
    birth_date = Column(Date, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    address_line = Column(String, nullable=True)
    address_city = Column(String, nullable=True)
    address_state = Column(String, nullable=True)
    address_postal_code = Column(String, nullable=True)
    source_system = Column(String, nullable=True)  # which system sent this record

    observations = relationship(
        "Observation", back_populates="patient", cascade="all, delete-orphan"
    )


class Observation(Base):
    __tablename__ = "observations"

    id = Column(String, primary_key=True, default=_uuid)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    code = Column(String, nullable=False)       # e.g. LOINC code, "8867-4"
    display = Column(String, nullable=False)    # e.g. "Heart rate"
    value = Column(String, nullable=False)
    unit = Column(String, nullable=True)
    status = Column(String, default="final")
    effective_datetime = Column(DateTime, nullable=True)

    patient = relationship("Patient", back_populates="observations")
