from app.hl7_parser import HL7ParseError, parse_adt_to_patient_dict, patient_to_hl7_adt


SAMPLE_ADT = (
    "MSH|^~\\&|SENDING_APP|SENDING_FAC|RECEIVING_APP|RECEIVING_FAC|20240115103000||ADT^A01|MSG00001|P|2.5\r"
    "EVN|A01|20240115103000\r"
    "PID|1||55555^^^HOSPITAL^MR||Nguyen^Anh||19900722|F|||123 Main St^^Springfield^IL^62701||555-9876"
)


def test_parse_adt_message_directly():
    data = parse_adt_to_patient_dict(SAMPLE_ADT)
    assert data["identifier"] == "55555"
    assert data["family_name"] == "Nguyen"
    assert data["given_name"] == "Anh"
    assert data["gender"] == "female"
    assert str(data["birth_date"]) == "1990-07-22"
    assert data["address_city"] == "Springfield"
    assert data["phone"] == "555-9876"


def test_parse_missing_pid_raises():
    try:
        parse_adt_to_patient_dict("MSH|^~\\&|A|B|C|D|20240115||ADT^A01|1|P|2.5")
        assert False, "expected HL7ParseError"
    except HL7ParseError:
        pass


def test_ingest_hl7_creates_patient(client):
    resp = client.post("/hl7/ingest", json={"message": SAMPLE_ADT})
    assert resp.status_code == 201
    body = resp.json()
    assert body["identifier"] == "55555"
    assert body["name"]["family"] == "Nguyen"
    assert body["sourceSystem"] == "HL7-ADT"


def test_ingest_hl7_upserts_on_same_identifier(client):
    client.post("/hl7/ingest", json={"message": SAMPLE_ADT})

    updated_message = SAMPLE_ADT.replace("Nguyen^Anh", "Nguyen^Annie")
    resp = client.post("/hl7/ingest", json={"message": updated_message})
    assert resp.status_code == 201
    assert resp.json()["name"]["given"] == ["Annie"]

    # still only one patient stored (upsert, not duplicate)
    all_patients = client.get("/fhir/Patient", params={"identifier": "55555"}).json()
    assert len(all_patients) == 1


def test_export_round_trip(client):
    ingest_resp = client.post("/hl7/ingest", json={"message": SAMPLE_ADT})
    patient_id = ingest_resp.json()["id"]

    export_resp = client.get(f"/hl7/export/{patient_id}")
    assert export_resp.status_code == 200
    hl7_text = export_resp.text
    assert "PID|1||55555" in hl7_text
    assert "Nguyen^Anh" in hl7_text

    # re-parsing the exported message should recover the same core data
    reparsed = parse_adt_to_patient_dict(hl7_text)
    assert reparsed["identifier"] == "55555"
    assert reparsed["family_name"] == "Nguyen"
