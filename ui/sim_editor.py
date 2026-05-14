"""SIM profile editor dialog."""
from __future__ import annotations
import uuid
import re
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QGroupBox, QHBoxLayout,
    QLineEdit, QComboBox, QPushButton, QLabel,
    QDialogButtonBox, QMessageBox, QCheckBox
)
from PyQt6.QtCore import Qt


MODES = ["soft", "pcsc"]
CARRIERS = ["AT&T", "Verizon", "T-Mobile", "US Cellular", "Dish", "Custom"]
MNC_MAP = {"AT&T": "410", "Verizon": "480", "T-Mobile": "260",
           "US Cellular": "220", "Dish": "530", "Custom": "000"}
APN_MAP = {"AT&T": "broadband", "Verizon": "vzwinternet",
           "T-Mobile": "fast.t-mobile.com", "US Cellular": "usinternet",
           "Dish": "internet", "Custom": "internet"}


def _rand_hex(n: int) -> str:
    import secrets
    return secrets.token_hex(n // 2).upper()


class SimEditorDialog(QDialog):
    def __init__(self, sim: dict | None = None, parent=None):
        super().__init__(parent)
        self._is_new = sim is None
        self._sim = dict(sim) if sim else self._default_sim()
        self.setWindowTitle("Add SIM Profile" if self._is_new else f"Edit — {self._sim['name']}")
        self.setMinimumWidth(520)
        self._build_ui()
        self._populate()

    @staticmethod
    def _default_sim() -> dict:
        return {
            "id":      f"SIM-{str(uuid.uuid4())[:8].upper()}",
            "name":    "",
            "carrier": "AT&T",
            "imsi":    "310410000000001",
            "imei":    "353490069873456",
            "ki":      "",
            "opc":     "",
            "amf":     "8000",
            "sqn":     "000000000001",
            "mcc":     "310",
            "mnc":     "410",
            "apn":     "broadband",
            "mode":    "soft",
        }

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 16)

        # ── Mode & Carrier ──
        grp_basic = QGroupBox("Profile")
        form = QFormLayout(grp_basic)
        form.setSpacing(8)

        self._profile_name = QLineEdit()
        self._profile_name.setPlaceholderText("e.g. AT&T Test SIM #1")

        self._mode = QComboBox()
        self._mode.addItems(MODES)
        self._mode.currentTextChanged.connect(self._on_mode_changed)

        self._carrier = QComboBox()
        self._carrier.addItems(CARRIERS)
        self._carrier.currentTextChanged.connect(self._on_carrier_changed)

        form.addRow("Profile name:", self._profile_name)
        form.addRow("Mode:", self._mode)
        form.addRow("Carrier:", self._carrier)
        layout.addWidget(grp_basic)

        # ── USIM credentials ──
        self._grp_creds = QGroupBox("USIM Credentials (soft mode)")
        form2 = QFormLayout(self._grp_creds)
        form2.setSpacing(8)

        self._mcc  = QLineEdit(); self._mcc.setMaxLength(3);  self._mcc.setFixedWidth(55)
        self._mnc  = QLineEdit(); self._mnc.setMaxLength(3);  self._mnc.setFixedWidth(55)
        mcc_row = QHBoxLayout()
        mcc_row.addWidget(QLabel("MCC:")); mcc_row.addWidget(self._mcc)
        mcc_row.addWidget(QLabel("MNC:")); mcc_row.addWidget(self._mnc)
        mcc_row.addStretch()
        form2.addRow("MCC / MNC:", mcc_row)

        self._imsi = QLineEdit(); self._imsi.setMaxLength(15)
        self._imei = QLineEdit(); self._imei.setMaxLength(15)
        self._ki   = QLineEdit(); self._ki.setMaxLength(32)
        self._opc  = QLineEdit(); self._opc.setMaxLength(32)
        self._amf  = QLineEdit(); self._amf.setMaxLength(4)
        self._sqn  = QLineEdit(); self._sqn.setMaxLength(12)
        self._apn  = QLineEdit()

        # Generate random Ki/OPC buttons
        ki_row  = QHBoxLayout()
        ki_row.addWidget(self._ki)
        btn_gen_ki = QPushButton("Gen")
        btn_gen_ki.setFixedWidth(46)
        btn_gen_ki.setToolTip("Generate random Ki")
        btn_gen_ki.clicked.connect(lambda: self._ki.setText(_rand_hex(32)))
        ki_row.addWidget(btn_gen_ki)

        opc_row = QHBoxLayout()
        opc_row.addWidget(self._opc)
        btn_gen_opc = QPushButton("Gen")
        btn_gen_opc.setFixedWidth(46)
        btn_gen_opc.setToolTip("Generate random OPc")
        btn_gen_opc.clicked.connect(lambda: self._opc.setText(_rand_hex(32)))
        opc_row.addWidget(btn_gen_opc)

        form2.addRow("IMSI:", self._imsi)
        form2.addRow("IMEI:", self._imei)
        form2.addRow("Ki (128-bit hex):", ki_row)
        form2.addRow("OPc (128-bit hex):", opc_row)
        form2.addRow("AMF:", self._amf)
        form2.addRow("SQN:", self._sqn)
        form2.addRow("APN:", self._apn)

        layout.addWidget(self._grp_creds)

        # ── PCSC note ──
        self._lbl_pcsc = QLabel(
            "<b>Physical SIM (PCSC mode)</b><br>"
            "Credentials will be read from the physical SIM card via a card reader.<br>"
            "Requires <code>pcscd</code> running and PIN disabled on the card."
        )
        self._lbl_pcsc.setWordWrap(True)
        self._lbl_pcsc.setStyleSheet("color:#80c080; padding:10px; "
                                      "background:#1a2e1a; border-radius:6px;")
        self._lbl_pcsc.setVisible(False)
        layout.addWidget(self._lbl_pcsc)

        # ── Extra info from .grsp (read-only) ──
        self._grp_grsp = QGroupBox("Card Info (from .grsp import)")
        form_grsp = QFormLayout(self._grp_grsp)
        form_grsp.setSpacing(6)

        self._lbl_iccid    = QLabel()
        self._lbl_msisdn   = QLabel()
        self._lbl_atr      = QLabel()
        self._lbl_card_type = QLabel()
        self._lbl_source   = QLabel()

        for lbl in (self._lbl_iccid, self._lbl_msisdn, self._lbl_atr,
                    self._lbl_card_type, self._lbl_source):
            lbl.setStyleSheet("color:#8090b0; font-family:Consolas; font-size:12px;")
            lbl.setWordWrap(True)

        form_grsp.addRow("ICCID:",     self._lbl_iccid)
        form_grsp.addRow("MSISDN:",    self._lbl_msisdn)
        form_grsp.addRow("ATR:",       self._lbl_atr)
        form_grsp.addRow("Card type:", self._lbl_card_type)
        form_grsp.addRow("Source:",    self._lbl_source)
        self._grp_grsp.setVisible(False)
        layout.addWidget(self._grp_grsp)

        # ── Buttons ──
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        btn_box.button(QDialogButtonBox.StandardButton.Ok).setObjectName("btnPrimary")
        layout.addWidget(btn_box)

    def _populate(self):
        s = self._sim
        self._profile_name.setText(s.get("name", ""))

        mode_idx = self._mode.findText(s.get("mode", "soft"))
        if mode_idx >= 0: self._mode.setCurrentIndex(mode_idx)

        c_idx = self._carrier.findText(s.get("carrier", "AT&T"))
        if c_idx >= 0: self._carrier.setCurrentIndex(c_idx)

        self._mcc.setText(s.get("mcc", "310"))
        self._mnc.setText(s.get("mnc", "410"))
        self._imsi.setText(s.get("imsi", ""))
        self._imei.setText(s.get("imei", ""))
        self._ki.setText(s.get("ki", ""))
        self._opc.setText(s.get("opc", ""))
        self._amf.setText(s.get("amf", "8000"))
        self._sqn.setText(s.get("sqn", "000000000001"))
        self._apn.setText(s.get("apn", "internet"))
        self._on_mode_changed(s.get("mode", "soft"))

        # Show .grsp extra fields if present
        has_grsp = any(k.startswith("_") for k in s)
        self._grp_grsp.setVisible(has_grsp)
        if has_grsp:
            self._lbl_iccid.setText(s.get("_iccid", ""))
            self._lbl_msisdn.setText(s.get("_msisdn", ""))
            self._lbl_atr.setText(s.get("_atr", ""))
            self._lbl_card_type.setText(s.get("_card_type", ""))
            self._lbl_source.setText(s.get("_source_file", ""))

    def _on_mode_changed(self, mode: str):
        is_soft = mode == "soft"
        self._grp_creds.setVisible(is_soft)
        self._lbl_pcsc.setVisible(not is_soft)

    def _on_carrier_changed(self, text: str):
        self._mnc.setText(MNC_MAP.get(text, "000"))
        self._apn.setText(APN_MAP.get(text, "internet"))

    def _on_accept(self):
        if not self._profile_name.text().strip():
            QMessageBox.warning(self, "Validation", "Profile name is required.")
            return
        mode = self._mode.currentText()
        if mode == "soft":
            imsi = self._imsi.text().strip()
            if not re.fullmatch(r"\d{10,15}", imsi):
                QMessageBox.warning(self, "Validation", "IMSI must be 10-15 digits.")
                return
            ki = self._ki.text().strip()
            if ki and not re.fullmatch(r"[0-9a-fA-F]{32}", ki):
                QMessageBox.warning(self, "Validation", "Ki must be 32 hex characters.")
                return

        self._sim.update({
            "name":    self._profile_name.text().strip(),
            "carrier": self._carrier.currentText(),
            "mode":    mode,
            "mcc":     self._mcc.text().strip(),
            "mnc":     self._mnc.text().strip(),
            "imsi":    self._imsi.text().strip(),
            "imei":    self._imei.text().strip(),
            "ki":      self._ki.text().strip().upper(),
            "opc":     self._opc.text().strip().upper(),
            "amf":     self._amf.text().strip(),
            "sqn":     self._sqn.text().strip(),
            "apn":     self._apn.text().strip(),
        })
        self.accept()

    def result_sim(self) -> dict:
        return self._sim
