# Healthcare System Interoperability — Base Project

A minimal but functional demo of **healthcare data interoperability**: it lets a
legacy system that speaks **HL7 v2** (e.g. a hospital ADT feed) exchange
patient data with a modern service that exposes **FHIR-shaped** resources
over REST.

## Why this design

Real-world healthcare interoperability problems almost always come down to:
one system speaks an older messaging standard (HL7 v2), another expects the
newer resource-based standard (FHIR), and something in the middle has to
translate between them without losing data. This project models that
exact problem on a small scale:

```
Legacy HIS/ADT system            This service                Modern FHIR client
  (HL7 v2 messages)   ── POST ──►  /hl7/ingest  ──► stores as ──► GET /fhir/Patient/{id}
                       ◄── GET ──  /hl7/export/{id} ◄── FHIR-shaped Patient
```

## Features

- **FHIR-style REST API** for `Patient` and `Observation` resources
  (create, read, update, delete, search).
- **HL7 v2 → FHIR ingestion** (`POST /hl7/ingest`): parses a raw ADT^A01
  message (PID segment) and upserts it as a Patient resource.
- **FHIR → HL7 v2 export** (`GET /hl7/export/{id}`): converts a stored
  Patient back into an HL7 v2 message for legacy consumers.
- SQLite persistence via SQLAlchemy (swap the connection string for
  Postgres/MySQL in production).
- Interactive API docs at `/docs` (Swagger UI) courtesy of FastAPI.
- Test suite covering both the REST API and the HL7 parser/generator.

## Project structure

```
healthcare-interop/
├── app/
│   ├── main.py            # FastAPI app, router registration
│   ├── database.py        # SQLAlchemy engine/session setup
│   ├── models.py          # ORM models: Patient, Observation
│   ├── schemas.py         # Pydantic schemas shaped like FHIR resources
│   ├── hl7_parser.py       # HL7 v2 <-> FHIR mapping logic
│   └── routers/
│       ├── patients.py     # /fhir/Patient CRUD
│       ├── observations.py # /fhir/Observation CRUD
│       └── hl7.py          # /hl7/ingest, /hl7/export
├── tests/
├── requirements.txt
└── README.md
```

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for interactive API documentation.

## Try it

**1. Create a patient directly via FHIR API:**

```bash
curl -X POST http://127.0.0.1:8000/fhir/Patient \
  -H "Content-Type: application/json" \
  -d '{
        "identifier": "MRN001",
        "family_name": "Smith",
        "given_name": "Jane",
        "gender": "female",
        "birth_date": "1985-03-14",
        "phone": "555-1234"
      }'
```

**2. Ingest a legacy HL7 v2 ADT message (simulating a hospital feed):**

```bash
curl -X POST http://127.0.0.1:8000/hl7/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "message": "MSH|^~\\&|SENDING_APP|SENDING_FAC|RECEIVING_APP|RECEIVING_FAC|20240115103000||ADT^A01|MSG00001|P|2.5\rEVN|A01|20240115103000\rPID|1||77777^^^HOSPITAL^MR||Patel^Ravi||19780512|M|||9 Oak Ave^^Chicago^IL^60614||312-555-0100"
  }'
```

This returns the patient as a FHIR resource. Sending the same message again
(with the same identifier) **updates** the existing patient instead of
duplicating it — a basic patient-matching/upsert strategy.

**3. Export a patient back to HL7 v2** (e.g. for a legacy downstream system):

```bash
curl http://127.0.0.1:8000/hl7/export/{patient_id}
```

**4. Attach a clinical observation (e.g. a vital sign) to a patient:**

```bash
curl -X POST http://127.0.0.1:8000/fhir/Observation \
  -H "Content-Type: application/json" \
  -d '{
        "patient_id": "<patient-id-from-above>",
        "code": "8867-4",
        "display": "Heart rate",
        "value": "72",
        "unit": "bpm"
      }'
```

## Run tests

```bash
pytest -q
```

## Where to take this next

This is intentionally a **base project** — enough to demonstrate the core
interoperability pattern without the full complexity of production
healthcare systems. Natural extensions:

- Add more FHIR resource types (Encounter, Condition, MedicationRequest).
- Support more HL7 v2 message/segment types (ORU for lab results, ORM for
  orders) beyond ADT.
- Add proper patient matching/deduplication (fuzzy matching on name + DOB,
  not just exact identifier match).
- Add authentication/authorization (OAuth2 + SMART on FHIR scopes are the
  real-world standard).
- Validate against the full FHIR R4 resource schema (e.g. with the
  `fhir.resources` Python package) instead of a simplified subset.
- Add an audit log of all cross-system data exchanges (required for HIPAA
  compliance in a real deployment).
