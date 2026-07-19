def test_create_and_get_patient(client):
    payload = {
        "identifier": "MRN001",
        "family_name": "Smith",
        "given_name": "Jane",
        "gender": "female",
        "birth_date": "1985-03-14",
        "phone": "555-1234",
    }
    resp = client.post("/fhir/Patient", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["resourceType"] == "Patient"
    assert body["name"]["family"] == "Smith"
    patient_id = body["id"]

    resp = client.get(f"/fhir/Patient/{patient_id}")
    assert resp.status_code == 200
    assert resp.json()["identifier"] == "MRN001"


def test_duplicate_identifier_rejected(client):
    payload = {"identifier": "MRN002", "family_name": "Doe", "given_name": "John"}
    assert client.post("/fhir/Patient", json=payload).status_code == 201
    assert client.post("/fhir/Patient", json=payload).status_code == 409


def test_search_by_family_name(client):
    client.post("/fhir/Patient", json={"family_name": "Garcia", "given_name": "Maria"})
    client.post("/fhir/Patient", json={"family_name": "Lopez", "given_name": "Carlos"})

    resp = client.get("/fhir/Patient", params={"family": "garcia"})
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["name"]["family"] == "Garcia"


def test_create_observation_linked_to_patient(client):
    patient_resp = client.post(
        "/fhir/Patient", json={"family_name": "Lee", "given_name": "Sam"}
    )
    patient_id = patient_resp.json()["id"]

    obs_resp = client.post(
        "/fhir/Observation",
        json={
            "patient_id": patient_id,
            "code": "8867-4",
            "display": "Heart rate",
            "value": "72",
            "unit": "bpm",
        },
    )
    assert obs_resp.status_code == 201
    obs_body = obs_resp.json()
    assert obs_body["subject"]["reference"] == f"Patient/{patient_id}"
    assert obs_body["valueString"] == "72"


def test_observation_rejects_unknown_patient(client):
    resp = client.post(
        "/fhir/Observation",
        json={
            "patient_id": "does-not-exist",
            "code": "8867-4",
            "display": "Heart rate",
            "value": "72",
        },
    )
    assert resp.status_code == 404
