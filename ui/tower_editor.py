"""Tower editor dialog — create / edit a tower profile."""
from __future__ import annotations
import uuid
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QSpinBox, QComboBox, QDoubleSpinBox,
    QPushButton, QLabel, QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt
from core.tower_database import STATE_NAMES, BAND_FREQ


CARRIERS = ["AT&T", "Verizon", "T-Mobile", "US Cellular", "Dish", "Custom"]
BANDS = sorted(BAND_FREQ.keys())
N_PRB_OPTIONS = [6, 15, 25, 50, 75, 100]
MNC_DEFAULTS = {
    "AT&T": "410",
    "Verizon": "012",
    "T-Mobile": "260",
    "US Cellular": "220",
    "Dish": "530",
    "Custom": "000",
}


class TowerEditorDialog(QDialog):
    def __init__(self, tower: dict | None = None, state: str = "CO", parent=None):
        super().__init__(parent)
        self._is_new = tower is None
        self._tower = dict(tower) if tower else self._default_tower(state)
        self.setWindowTitle("Add Tower" if self._is_new else f"Edit — {self._tower['name']}")
        self.setMinimumWidth(500)
        self._build_ui()
        self._populate()

    # ── helpers ────────────────────────────────────────────────────────────
    @staticmethod
    def _default_tower(state: str) -> dict:
        return {
            "id": f"{state}-{str(uuid.uuid4())[:6].upper()}",
            "name": "",
            "city": "",
            "state": state,
            "lat": 0.0,
            "lon": 0.0,
            "carrier": "AT&T",
            "mcc": "310",
            "mnc": "410",
            "band": 12,
            "dl_earfcn": 5110,
            "pci": 1,
            "enb_id": 300000,
            "cell_id": 1,
            "tac": 1001,
            "tx_power": 43,
            "n_prb": 50,
        }

    # ── UI ─────────────────────────────────────────────────────────────────
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 16)

        # ── Basic info ──
        grp_basic = QGroupBox("Tower Information")
        form_basic = QFormLayout(grp_basic)
        form_basic.setSpacing(8)

        self._name = QLineEdit()
        self._name.setPlaceholderText("e.g. Denver Downtown - AT&T B12")
        self._city = QLineEdit()
        self._city.setPlaceholderText("City name")

        self._state_combo = QComboBox()
        for code, name in sorted(STATE_NAMES.items()):
            self._state_combo.addItem(f"{code} — {name}", code)

        self._lat = QDoubleSpinBox()
        self._lat.setRange(-90, 90); self._lat.setDecimals(6); self._lat.setSingleStep(0.001)
        self._lon = QDoubleSpinBox()
        self._lon.setRange(-180, 180); self._lon.setDecimals(6); self._lon.setSingleStep(0.001)

        form_basic.addRow("Name:", self._name)
        form_basic.addRow("City:", self._city)
        form_basic.addRow("State:", self._state_combo)
        coord_row = QHBoxLayout()
        coord_row.addWidget(QLabel("Lat:")); coord_row.addWidget(self._lat)
        coord_row.addWidget(QLabel("Lon:")); coord_row.addWidget(self._lon)
        form_basic.addRow("Coordinates:", coord_row)
        layout.addWidget(grp_basic)

        # ── Carrier ──
        grp_carrier = QGroupBox("Carrier / Network Identity")
        form_carrier = QFormLayout(grp_carrier)
        form_carrier.setSpacing(8)

        self._carrier = QComboBox()
        self._carrier.addItems(CARRIERS)
        self._carrier.currentTextChanged.connect(self._on_carrier_changed)

        self._mcc = QLineEdit(); self._mcc.setMaxLength(3); self._mcc.setFixedWidth(60)
        self._mnc = QLineEdit(); self._mnc.setMaxLength(3); self._mnc.setFixedWidth(60)

        mccmnc_row = QHBoxLayout()
        mccmnc_row.addWidget(QLabel("MCC:")); mccmnc_row.addWidget(self._mcc)
        mccmnc_row.addWidget(QLabel("MNC:")); mccmnc_row.addWidget(self._mnc)
        mccmnc_row.addStretch()

        form_carrier.addRow("Carrier:", self._carrier)
        form_carrier.addRow("MCC / MNC:", mccmnc_row)
        layout.addWidget(grp_carrier)

        # ── RF params ──
        grp_rf = QGroupBox("RF Parameters")
        form_rf = QFormLayout(grp_rf)
        form_rf.setSpacing(8)

        self._band = QComboBox()
        for b in BANDS:
            self._band.addItem(f"Band {b}  ({BAND_FREQ[b]})", b)
        self._band.currentIndexChanged.connect(self._on_band_changed)

        self._dl_earfcn = QSpinBox()
        self._dl_earfcn.setRange(0, 65535)

        self._n_prb = QComboBox()
        for n in N_PRB_OPTIONS:
            bw_map = {6: "1.4 MHz", 15: "3 MHz", 25: "5 MHz",
                      50: "10 MHz", 75: "15 MHz", 100: "20 MHz"}
            self._n_prb.addItem(f"{n} PRB ({bw_map[n]})", n)

        self._tx_power = QSpinBox()
        self._tx_power.setRange(0, 80); self._tx_power.setSuffix(" dBm")

        self._pci = QSpinBox()
        self._pci.setRange(0, 503)

        form_rf.addRow("Band:", self._band)
        form_rf.addRow("DL EARFCN:", self._dl_earfcn)
        form_rf.addRow("Bandwidth:", self._n_prb)
        form_rf.addRow("TX Power:", self._tx_power)
        form_rf.addRow("PCI:", self._pci)
        layout.addWidget(grp_rf)

        # ── Cell IDs ──
        grp_cell = QGroupBox("Cell Identifiers")
        form_cell = QFormLayout(grp_cell)
        form_cell.setSpacing(8)

        self._enb_id = QSpinBox()
        self._enb_id.setRange(0, 0xFFFFF); self._enb_id.setDisplayIntegerBase(10)

        self._cell_id = QSpinBox()
        self._cell_id.setRange(0, 255)

        self._tac = QSpinBox()
        self._tac.setRange(1, 65535)

        form_cell.addRow("eNB ID:", self._enb_id)
        form_cell.addRow("Cell ID:", self._cell_id)
        form_cell.addRow("TAC:", self._tac)
        layout.addWidget(grp_cell)

        # ── Buttons ──
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        btn_box.button(QDialogButtonBox.StandardButton.Ok).setObjectName("btnPrimary")
        layout.addWidget(btn_box)

    def _populate(self):
        t = self._tower
        self._name.setText(t.get("name", ""))
        self._city.setText(t.get("city", ""))

        idx = self._state_combo.findData(t.get("state", "CO"))
        if idx >= 0: self._state_combo.setCurrentIndex(idx)

        self._lat.setValue(t.get("lat", 0.0))
        self._lon.setValue(t.get("lon", 0.0))

        carrier_idx = self._carrier.findText(t.get("carrier", "AT&T"))
        if carrier_idx >= 0: self._carrier.setCurrentIndex(carrier_idx)

        self._mcc.setText(t.get("mcc", "310"))
        self._mnc.setText(t.get("mnc", "410"))

        band_idx = self._band.findData(t.get("band", 12))
        if band_idx >= 0: self._band.setCurrentIndex(band_idx)

        self._dl_earfcn.setValue(t.get("dl_earfcn", 5110))
        self._tx_power.setValue(t.get("tx_power", 43))
        self._pci.setValue(t.get("pci", 1))

        nprb_idx = self._n_prb.findData(t.get("n_prb", 50))
        if nprb_idx >= 0: self._n_prb.setCurrentIndex(nprb_idx)

        self._enb_id.setValue(t.get("enb_id", 300000))
        self._cell_id.setValue(t.get("cell_id", 1))
        self._tac.setValue(t.get("tac", 1001))

    def _on_carrier_changed(self, text: str):
        self._mnc.setText(MNC_DEFAULTS.get(text, "000"))

    def _on_band_changed(self, _):
        band = self._band.currentData()
        earfcn_defaults = {2: 900, 4: 1850, 5: 200, 12: 5110, 13: 5230, 17: 5780}
        self._dl_earfcn.setValue(earfcn_defaults.get(band, 5110))

    def _on_accept(self):
        if not self._name.text().strip():
            QMessageBox.warning(self, "Validation", "Tower name is required.")
            return
        if not self._city.text().strip():
            QMessageBox.warning(self, "Validation", "City is required.")
            return
        self._tower.update({
            "name":      self._name.text().strip(),
            "city":      self._city.text().strip(),
            "state":     self._state_combo.currentData(),
            "lat":       self._lat.value(),
            "lon":       self._lon.value(),
            "carrier":   self._carrier.currentText(),
            "mcc":       self._mcc.text().strip(),
            "mnc":       self._mnc.text().strip(),
            "band":      self._band.currentData(),
            "dl_earfcn": self._dl_earfcn.value(),
            "n_prb":     self._n_prb.currentData(),
            "tx_power":  self._tx_power.value(),
            "pci":       self._pci.value(),
            "enb_id":    self._enb_id.value(),
            "cell_id":   self._cell_id.value(),
            "tac":       self._tac.value(),
        })
        self.accept()

    def result_tower(self) -> dict:
        return self._tower
