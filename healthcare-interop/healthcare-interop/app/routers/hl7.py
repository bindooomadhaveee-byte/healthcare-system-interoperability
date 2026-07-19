from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.hl7_parser import HL7ParseError, parse_adt_to_patient_dict, patient_to_hl7_adt

router = APIRouter(prefix="/hl7", tags=["HL7 Interoperability"])


@router.post("/ingest", response_model=schemas.PatientOut, status_code=201)
def ingest_hl7_message(payload: schemas.HL7Message, db: Session = Depends(get_db)):
    """
    Accepts a raw HL7 v2 ADT message from a legacy source system, converts
    it into the internal FHIR-shaped Patient model, and upserts it.

    This simulates a hospital ADT feed (e.g. from an older HIS) pushing
    patient admit/update events into this modern, FHIR-capable service.
    """
    try:
        data = parse_adt_to_patient_dict(payload.message)
    except HL7ParseError as e:
        raise HTTPException(400, f"HL7 parse error: {e}")

    patient = None
    if data["identifier"]:
        patient = (
            db.query(models.Patient)
            .filter(models.Patient.identifier == data["identifier"])
            .first()
        )

    if patient:
        for field, value in data.items():
            setattr(patient, field, value)
    else:
        patient = models.Patient(**data)
        db.add(patient)

    db.commit()
    db.refresh(patient)
    return schemas.PatientOut.from_orm_model(patient)


@router.get("/export/{patient_id}")
def export_hl7_message(patient_id: str, db: Session = Depends(get_db)):
    """
    Converts a stored (FHIR-shaped) Patient back into an HL7 v2 ADT^A01
    message, demonstrating outbound interoperability toward legacy
    systems that only consume HL7.
    """
    patient = db.get(models.Patient, patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")

    hl7_message = patient_to_hl7_adt(patient)
    return Response(content=hl7_message, media_type="text/plain")
