"""GRSIMWrite .grsp file exporter.

Generates a .grsp file from a SIM profile that can be opened
directly in GRSIMWrite to flash a blank SIM card.
"""
from __future__ import annotations
import os
from typing import Any


def generate_grsp(sim: dict[str, Any]) -> str:
    """Generate GRSIMWrite .grsp file content from a SIM profile dict."""
    imsi15 = sim.get("imsi", "310410000000001")
    # Pad IMSI18 = "80" + 9 + imsi15 padded
    imsi18 = "80" + imsi15[:1] + imsi15

    ki   = sim.get("ki",  "00" * 16).upper()
    opc  = sim.get("opc", "00" * 16).upper()
    mcc  = sim.get("mcc", "310")
    mnc  = sim.get("mnc", "410")
    plmn = mcc + mnc            # e.g. 310410
    spn  = sim.get("carrier", "Custom")
    apn  = sim.get("apn", "internet")
    msisdn = sim.get("_msisdn", "")
    iccid  = sim.get("_iccid", "8901" + mcc + mnc + "000000000")
    atr    = sim.get("_atr", "3B9F95801FC78031A073B6A10067CF3215CA9CD70920")
    pin1   = sim.get("_pin1", "1234")
    puk1   = sim.get("_puk1", "88888888")
    adm    = sim.get("_adm",  "3838383838383838")

    # ECC by carrier
    ecc_gsm = "112; 911"
    ecc_lte = "112:112:00; 911:911:00"

    # OPLMN / HPLMN lines
    oplmn = f"{plmn}:4000; {plmn}:8000; {plmn}:0080"

    return f"""GRSIMWrite Data file
V 1.0

Control0
Name=Image1

Control1
Name=GrpComm
State=-1

Control14
Name=EditICCID
State=-1
Value={iccid}

Control15
Name=EditPIN1
State=-1
Value={pin1}

Control16
Name=EditPUK1
State=-1
Value={puk1}

Control17
Name=EditPIN2
State=-1
Value={pin1}

Control18
Name=EditPUK2
State=-1
Value={puk1}

Control19
Name=EditADM
State=-1
Value={adm}

Control20
Name=EditATR
State=-1
Value={atr}

Control21
Name=ChkICCID_Inc
State=-1
Value=0

Control22
Name=EditType
State=-1
Value=LTE(LY14):LTE+GSM

Control23
Name=EditLang
State=-1
Value=English

Control25
Name=EditApp
State=-1
Value=11100

Control77
Name=PanGSM_IMSI

Control78
Name=RadGSM_IMSI18
State=-1
Value=0

Control79
Name=RadGSM_IMSI15
State=-1
Value=-1

Control80
Name=EditGSM_IMSI18
State=-1
Value={imsi18}

Control81
Name=EditGSM_IMSI15
State=-1
Value={imsi15}

Control82
Name=EditGSM_KI
State=-1
Value={ki}

Control83
Name=EditGSM_ACC
State=-1
Value=FFFF

Control84
Name=ChkGSM_ACC_Input
State=-1
Value=0

Control85
Name=ChkGSM_IMSI_Inc
State=-1
Value=0

Control86
Name=ChkGSM_KI_Inc
State=-1
Value=0

Control87
Name=EditGSM_SMSP
State=-1
Value=+

Control88
Name=EditGSM_FPLMN
State=-1
Value=

Control89
Name=EditGSM_SPN
State=-1
Value={spn}

Control90
Name=EditGSM_PLMN
State=-1
Value={plmn}

Control91
Name=EditGSM_HPLMN
State=-1
Value=01

Control92
Name=EditGSM_GID1
State=-1
Value=

Control93
Name=EditGSM_GID2
State=-1
Value=

Control94
Name=EditGSM_MSISDN
State=-1
Value={msisdn}

Control95
Name=ChkGSM_MSISDN_Inc
State=-1
Value=0

Control97
Name=PanGSM_Alg

Control98
Name=RadGSM_Comp128_1
State=0
Value=-1

Control101
Name=RadGSM_MLG
State=-1
Value=0

Control102
Name=EditGSM_ECC
State=-1
Value={ecc_gsm}

Control106
Name=EditGSM_EHPLMN
State=-1
Value={plmn}

Control108
Name=EditGSM_AD
State=-1
Value=00000003

Control143
Name=PanLTE_IMSI

Control144
Name=RadLTE_IMSI18
State=-1
Value=0

Control145
Name=RadLTE_IMSI15
State=-1
Value=-1

Control146
Name=EditLTE_IMSI18
State=-1
Value={imsi18}

Control147
Name=EditLTE_IMSI15
State=-1
Value={imsi15}

Control148
Name=EditLTE_KI
State=-1
Value={ki}

Control149
Name=EditLTE_ACC
State=-1
Value=FFFF

Control150
Name=ChkLTE_ACC_Input
State=-1
Value=0

Control151
Name=ChkLTE_IMSI_Inc
State=-1
Value=0

Control152
Name=ChkLTE_KI_Inc
State=-1
Value=0

Control153
Name=EditLTE_SMSP
State=-1
Value=+

Control154
Name=EditLTE_FPLMN
State=-1
Value=

Control155
Name=EditLTE_SPN
State=-1
Value={spn}

Control156
Name=EditLTE_PLMN
State=-1
Value={plmn}:4000

Control157
Name=EditLTE_HPPLMN
State=-1
Value=01

Control158
Name=EditLTE_GID1
State=-1
Value=

Control159
Name=EditLTE_GID2
State=-1
Value=

Control160
Name=EditLTE_OPC
State=-1
Value={opc}

Control161
Name=EditLTE_OP
State=0
Value=

Control162
Name=EditLTE_OPLMN
State=-1
Value={oplmn}

Control163
Name=EditLTE_HPLMN
State=-1
Value={oplmn}

Control164
Name=EditLTE_MSISDN
State=-1
Value={msisdn}

Control165
Name=ChkLTE_MSISDN_Inc
State=-1
Value=0

Control140
Name=PanLTE_OPC

Control141
Name=RadLTE_OPC
State=-1
Value=-1

Control142
Name=RadLTE_OP
State=-1
Value=0

Control166
Name=PanLTE_Alg

Control167
Name=RadLTE_MLG
State=-1
Value=-1

Control168
Name=RadLTE_XOR
State=0
Value=0

Control171
Name=EditLTE_ECC
State=-1
Value={ecc_lte}

Control177
Name=EditLTE_EHPLMN
State=-1
Value={plmn}

Control181
Name=EditLTE_AD
State=-1
Value=00000003

CardInfo.Code=LY14
CardInfo.Name=LTE
CardInfo.Func=LTE+GSM
CardInfo.Desc=LTE(LY14):LTE+GSM
CardInfo.ATR={atr}
CardInfo.AID_USIM=A0000000871002FF86FF0389FFFFFFFF
CardInfo.AID_CSIM=
CardInfo.GSM=-1
CardInfo.WCDMA=-1
CardInfo.LTE=-1
CardInfo.CDMA1X=0
CardInfo.EVDO=0
CardInfo.CSIM=0
CardInfo.Alg_Comp128_1=0
CardInfo.Alg_Comp128_2=0
CardInfo.Alg_Comp128_3=0
CardInfo.Alg_MLG=-1
CardInfo.Alg_XOR=0
CardInfo.ChangeADM=-1
"""


def export_grsp(sim: dict[str, Any], output_dir: str) -> str:
    """Write .grsp file for GRSIMWrite. Returns path."""
    os.makedirs(output_dir, exist_ok=True)
    safe_name = sim.get("id", "sim").replace("/", "_")
    path = os.path.join(output_dir, f"{safe_name}.grsp")
    with open(path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(generate_grsp(sim))
    return path
