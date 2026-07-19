"""
HL7 v2.x <-> internal (FHIR-shaped) data mapping.

This module is the heart of the "interoperability" demo: it lets a legacy
system that only speaks HL7 v2 (pipe-and-hat delimited messages, e.g. an
ADT^A01 "admit patient" message from a hospital's ADT feed) exchange data
with this service, which stores and exposes patients as FHIR-like
resources. It also converts stored patients back into HL7 v2 so the
interoperability works in both directions.

HL7 v2 basics used here:
- Segments are separated by carriage return (\\r) or newline.
- Fields within a segment are separated by "|".
- Components within a field are separated by "^".
- The PID (Patient Identification) segment carries demographics:
    PID-3  = Patient Identifier List (component 1 = the ID)
    PID-5  = Patient Name (Family^Given)
    PID-7  = Date of Birth (YYYYMMDD)
    PID-8  = Administrative Sex (M/F/O/U)
    PID-11 = Patient Address (Line^^City^State^PostalCode)
    PID-13 = Phone Number - Home
"""
from __future__ import annotations

from datetime import datetime, date, timezone
from typing import Optional


GENDER_MAP = {"M": "male", "F": "female", "O": "other", "U": "unknown"}
GENDER_MAP_REVERSE = {v: k for k, v in GENDER_MAP.items()}


class HL7ParseError(ValueError):
    pass


def _segments(message: str) -> list[list[str]]:
    raw_segments = [s for s in message.replace("\r", "\n").split("\n") if s.strip()]
    return [seg.split("|") for seg in raw_segments]


def parse_adt_to_patient_dict(message: str) -> dict:
    """
    Parse an HL7 v2 ADT message and return a dict compatible with
    schemas.PatientCreate fields.
    """
    segments = _segments(message)
    pid = next((s for s in segments if s[0] == "PID"), None)
    if pid is None:
        raise HL7ParseError("No PID segment found in HL7 message")

    def field(index: int) -> str:
        return pid[index] if index < len(pid) else ""

    # PID-3: Patient Identifier List, e.g. "12345^^^HOSPITAL^MR"
    identifier = field(3).split("^")[0] or None

    # PID-5: Family^Given
    name_parts = field(5).split("^")
    family_name = name_parts[0] if len(name_parts) > 0 else ""
    given_name = name_parts[1] if len(name_parts) > 1 else ""
    if not family_name or not given_name:
        raise HL7ParseError("PID-5 (patient name) must contain Family^Given")

    # PID-7: YYYYMMDD
    birth_date: Optional[date] = None
    dob_raw = field(7)
    if dob_raw:
        try:
            birth_date = datetime.strptime(dob_raw[:8], "%Y%m%d").date()
        except ValueError:
            raise HL7ParseError(f"Invalid PID-7 date of birth: {dob_raw!r}")

    # PID-8: M/F/O/U
    gender_raw = field(8).upper()
    gender = GENDER_MAP.get(gender_raw)

    # PID-11: Line^^City^State^PostalCode
    addr_parts = field(11).split("^")
    address_line = addr_parts[0] if len(addr_parts) > 0 else None
    address_city = addr_parts[2] if len(addr_parts) > 2 else None
    address_state = addr_parts[3] if len(addr_parts) > 3 else None
    address_postal_code = addr_parts[4] if len(addr_parts) > 4 else None

    # PID-13: Phone
    phone = field(13).split("^")[0] or None

    return {
        "identifier": identifier,
        "family_name": family_name,
        "given_name": given_name,
        "gender": gender,
        "birth_date": birth_date,
        "phone": phone,
        "address_line": address_line or None,
        "address_city": address_city or None,
        "address_state": address_state or None,
        "address_postal_code": address_postal_code or None,
        "source_system": "HL7-ADT",
    }


def patient_to_hl7_adt(p) -> str:
    """
    Convert a stored Patient ORM object back into a minimal HL7 v2 ADT^A01
    message, demonstrating outbound interoperability toward legacy
    consumers.
    """
    now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    gender_code = GENDER_MAP_REVERSE.get(p.gender or "", "U")
    dob = p.birth_date.strftime("%Y%m%d") if p.birth_date else ""

    msh = f"MSH|^~\\&|INTEROP-SVC|HOSPITAL|RECEIVER|RECEIVER-FACILITY|{now}||ADT^A01|{p.id}|P|2.5"
    pid = (
        "PID|1||"
        f"{p.identifier or ''}^^^HOSPITAL^MR||"
        f"{p.family_name}^{p.given_name}||"
        f"{dob}|{gender_code}|||"
        f"{p.address_line or ''}^^{p.address_city or ''}^{p.address_state or ''}^{p.address_postal_code or ''}|||"
        f"{p.phone or ''}"
    )
    evn = f"EVN|A01|{now}"
    return "\r".join([msh, evn, pid])
