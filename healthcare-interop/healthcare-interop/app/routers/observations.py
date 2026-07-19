from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/fhir/Observation", tags=["Observation"])


@router.post("", response_model=schemas.ObservationOut, status_code=201)
def create_observation(payload: schemas.ObservationCreate, db: Session = Depends(get_db)):
    patient = db.get(models.Patient, payload.patient_id)
    if not patient:
        raise HTTPException(404, "Referenced patient not found")

    obs = models.Observation(**payload.model_dump())
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return schemas.ObservationOut.from_orm_model(obs)


@router.get("", response_model=list[schemas.ObservationOut])
def search_observations(
    patient_id: Optional[str] = Query(None, description="Filter by subject Patient/{id}"),
    db: Session = Depends(get_db),
):
    q = db.query(models.Observation)
    if patient_id:
        q = q.filter(models.Observation.patient_id == patient_id)
    return [schemas.ObservationOut.from_orm_model(o) for o in q.all()]


@router.get("/{observation_id}", response_model=schemas.ObservationOut)
def get_observation(observation_id: str, db: Session = Depends(get_db)):
    obs = db.get(models.Observation, observation_id)
    if not obs:
        raise HTTPException(404, "Observation not found")
    return schemas.ObservationOut.from_orm_model(obs)
