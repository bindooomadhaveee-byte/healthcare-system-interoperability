from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/fhir/Patient", tags=["Patient"])


@router.post("", response_model=schemas.PatientOut, status_code=201)
def create_patient(payload: schemas.PatientCreate, db: Session = Depends(get_db)):
    if payload.identifier:
        existing = (
            db.query(models.Patient)
            .filter(models.Patient.identifier == payload.identifier)
            .first()
        )
        if existing:
            raise HTTPException(409, "Patient with this identifier already exists")

    patient = models.Patient(**payload.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return schemas.PatientOut.from_orm_model(patient)


@router.get("", response_model=list[schemas.PatientOut])
def search_patients(
    family: Optional[str] = Query(None, description="Search by family name"),
    identifier: Optional[str] = Query(None, description="Search by external identifier"),
    db: Session = Depends(get_db),
):
    q = db.query(models.Patient)
    if family:
        q = q.filter(models.Patient.family_name.ilike(f"%{family}%"))
    if identifier:
        q = q.filter(models.Patient.identifier == identifier)
    return [schemas.PatientOut.from_orm_model(p) for p in q.all()]


@router.get("/{patient_id}", response_model=schemas.PatientOut)
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = db.get(models.Patient, patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")
    return schemas.PatientOut.from_orm_model(patient)


@router.put("/{patient_id}", response_model=schemas.PatientOut)
def update_patient(patient_id: str, payload: schemas.PatientUpdate, db: Session = Depends(get_db)):
    patient = db.get(models.Patient, patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(patient, field, value)
    db.commit()
    db.refresh(patient)
    return schemas.PatientOut.from_orm_model(patient)


@router.delete("/{patient_id}", status_code=204)
def delete_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = db.get(models.Patient, patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")
    db.delete(patient)
    db.commit()
