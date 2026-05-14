"""GRSIMWrite .grsp / .grps file importer.

Parses GRSIMWrite data files and extracts SIM profile fields
for use in srsRAN ue.conf generation.
"""
from __future__ import annotations
import os
import re
import uuid


def _parse_grsp(text: str) -> dict[str, str]:
    """Parse key=value pairs from GRSIMWrite file. Returns flat dict."""
    result: dict[str, str] = {}
    current_control: str | None = None

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Control block header: "Control42"
        m_ctrl = re.match(r"^Control\d+$", line)
        if m_ctrl:
            current_control = None
            continue

        # Name= inside a control block
        if line.startswith("Name=") and current_control is None:
            current_control = line[5:]
            continue

        # Value= inside a control block
        if line.startswith("Value=") and current_control:
            result[current_control] = line[6:]
            current_control = None
            continue

        # Top-level CardInfo.xxx= lines
        m_card = re.match(r"^(CardInfo\.\w+)=(.*)$", line)
        if m_card:
            result[m_card.group(1)] = m_card.group(2)

    return result


def import_grsp_file(path: str) -> dict:
    """Read a .grsp file and return a SIM profile dict compatible with sim_profiles.json."""
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()

    # Verify it's a GRSIMWrite file
    if "GRSIMWrite Data file" not in text and "GRSIMWrite" not in text[:100]:
        raise ValueError("Not a valid GRSIMWrite (.grsp) file")

    fields = _parse_grsp(text)

    # ── Extract fields ────────────────────────────────────────────────────

    # IMSI: prefer 15-digit, fall back to 18-digit
    imsi15 = fields.get("EditLTE_IMSI15") or fields.get("EditGSM_IMSI15", "")
    imsi18 = fields.get("EditLTE_IMSI18") or fields.get("EditGSM_IMSI18", "")
    # Use 15-digit if it looks valid (starts with digits)
    imsi = imsi15 if re.match(r"^\d{10,15}$", imsi15) else imsi18

    # MCC/MNC — try to read from PLMN field first, fall back to IMSI
    plmn_raw = (fields.get("EditLTE_PLMN") or fields.get("EditGSM_PLMN", "")).split(":")[0].strip()
    if re.match(r"^\d{5,6}$", plmn_raw):
        mcc = plmn_raw[:3]
        mnc = plmn_raw[3:]          # 2 or 3 digits as stored in card
    else:
        mcc = imsi[:3] if len(imsi) >= 3 else ""
        mnc = imsi[3:6] if len(imsi) >= 6 else ""

    # Ki — prefer LTE, fall back to GSM
    ki = fields.get("EditLTE_KI") or fields.get("EditGSM_KI", "")

    # OPc — LTE section
    opc = fields.get("EditLTE_OPC", "")

    # SPN (carrier name)
    spn = fields.get("EditLTE_SPN") or fields.get("EditGSM_SPN", "")

    # MSISDN (phone number)
    msisdn = fields.get("EditLTE_MSISDN") or fields.get("EditGSM_MSISDN", "")

    # ICCID
    iccid = fields.get("EditICCID", "")

    # IMEI (not always present in grsp, generate placeholder)
    imei = fields.get("EditIMEI", "353490069873456")

    # PIN/PUK
    pin1 = fields.get("EditPIN1", "1234")
    puk1 = fields.get("EditPUK1", "88888888")
    adm  = fields.get("EditADM", "")

    # ATR
    atr = fields.get("EditATR") or fields.get("CardInfo.ATR", "")

    # Card type
    card_type = fields.get("EditType") or fields.get("CardInfo.Desc", "")
    card_code  = fields.get("CardInfo.Code", "")

    # AMF — default for Milenage
    amf = "8000"

    # SQN — default
    sqn = "000000000001"

    # APN defaults by carrier/MNC
    apn_map = {"410": "broadband", "480": "vzwinternet", "260": "fast.t-mobile.com"}
    apn = apn_map.get(mnc, "internet")

    # Carrier name
    carrier_map = {
        "AT&T": "AT&T", "Verizon": "Verizon", "T-Mobile": "T-Mobile",
        "ATT": "AT&T",
    }
    carrier = "Custom"
    for key, val in carrier_map.items():
        if key.lower() in spn.lower():
            carrier = val
            break

    # Algorithm
    alg_mlg = fields.get("RadLTE_MLG", "0")
    alg_xor = fields.get("RadLTE_XOR", "0")
    algo = "milenage" if alg_mlg not in ("0", "") else ("xor" if alg_xor not in ("0", "") else "milenage")

    # Build profile name from filename + SPN
    base_name = os.path.splitext(os.path.basename(path))[0]
    name = f"{spn or 'Custom'} — imported from {base_name}"

    profile = {
        "id":       f"SIM-{str(uuid.uuid4())[:8].upper()}",
        "name":     name,
        "carrier":  carrier,
        "imsi":     imsi,
        "imei":     imei,
        "ki":       ki.upper(),
        "opc":      opc.upper(),
        "amf":      amf,
        "sqn":      sqn,
        "mcc":      mcc,
        "mnc":      mnc,
        "apn":      apn,
        "mode":     "soft",
        # Extended fields stored for reference
        "_iccid":   iccid,
        "_msisdn":  msisdn,
        "_pin1":    pin1,
        "_puk1":    puk1,
        "_adm":     adm,
        "_atr":     atr,
        "_card_type": card_type,
        "_card_code": card_code,
        "_algo":    algo,
        "_source_file": os.path.basename(path),
    }

    return profile


def import_grsp_files(paths: list[str]) -> list[dict]:
    """Import multiple .grsp files. Returns list of profiles (skips errors)."""
    profiles = []
    errors = []
    for p in paths:
        try:
            profiles.append(import_grsp_file(p))
        except Exception as e:
            errors.append(f"{os.path.basename(p)}: {e}")
    return profiles, errors
