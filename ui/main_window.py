"""Main application window — srsRAN Manager."""
from __future__ import annotations
import os
import subprocess
import sys
import tempfile
import shutil
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QTabWidget, QHeaderView, QAbstractItemView, QFileDialog,
    QMessageBox, QStatusBar, QFrame, QSizePolicy,
    QToolBar, QApplication, QGroupBox, QTextEdit, QProgressBar,
    QScrollArea
)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont, QAction

from core.tower_database import TowerDatabase, STATE_NAMES, CARRIER_COLORS, BAND_FREQ
from core.config_generator import (
    export_tower_configs, export_ue_conf, generate_ue_conf,
    generate_epc_conf, generate_user_db, export_full_bundle,
    generate_sim_for_tower
)
from core.grsp_exporter import export_grsp
from core.grsp_importer import import_grsp_files
from ui.tower_editor import TowerEditorDialog
from ui.sim_editor import SimEditorDialog
from ui.config_viewer import ConfigViewerDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = TowerDatabase()
        self._current_state: str | None = None
        self._state_buttons: dict[str, QPushButton] = {}
        self._selected_tower: dict | None = None
        self._selected_sim: dict | None = None
        self._active_tower_sim: dict | None = None   # auto-generated SIM for current tower
        self.setWindowTitle("srsRAN Manager — US LTE Base Station Profiles")
        self.setMinimumSize(1280, 760)
        self._build_ui()
        self._select_state(list(STATE_NAMES.keys())[0])

    # ══════════════════════════════════════════════════════════════════════
    # UI BUILD
    # ══════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        self._build_toolbar()

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("background:#2a2d36;")
        sep.setFixedWidth(1)
        root.addWidget(sep)

        self._tabs = QTabWidget()
        root.addWidget(self._tabs, 1)

        self._tower_tab  = self._build_tower_tab()
        self._sim_tab    = self._build_sim_tab()
        self._launch_tab = self._build_launch_tab()

        self._tabs.addTab(self._tower_tab,  "  Base Stations  ")
        self._tabs.addTab(self._sim_tab,    "  SIM Profiles  ")
        self._tabs.addTab(self._launch_tab, "  Launch srsRAN  ")

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready — select a tower to begin")

    def _build_toolbar(self):
        tb = QToolBar("Main")
        tb.setMovable(False)
        tb.setIconSize(QSize(18, 18))

        for label, tip, slot in [
            ("+ Tower",       "Add tower profile",              self._add_tower),
            ("+ SIM",         "Add SIM profile manually",       self._add_sim),
            ("Import .grsp…", "Import SIM from GRSIMWrite file",self._import_grsp),
        ]:
            a = QAction(label, self)
            a.setStatusTip(tip)
            a.triggered.connect(slot)
            tb.addAction(a)

        tb.addSeparator()

        act_bundle = QAction("Export bundle…", self)
        act_bundle.setStatusTip("Export all configs + .grsp for selected tower")
        act_bundle.triggered.connect(self._export_bundle)
        tb.addAction(act_bundle)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tb.addWidget(spacer)

        lbl = QLabel("  srsRAN Manager  ")
        lbl.setStyleSheet("color:#3a4a70; font-weight:bold; font-size:12px;")
        tb.addWidget(lbl)

        self.addToolBar(tb)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(195)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(3)

        lbl = QLabel("STATES")
        lbl.setStyleSheet("color:#3a4560; font-size:10px; font-weight:bold; "
                          "letter-spacing:1.5px; padding:4px 8px 6px 8px;")
        layout.addWidget(lbl)

        for code in sorted(STATE_NAMES.keys()):
            name  = STATE_NAMES[code]
            count = len(self.db.towers(code))
            btn   = QPushButton(f"{code}  {name}\n{count} towers")
            btn.setObjectName("stateBtn")
            btn.setProperty("active", "false")
            btn.clicked.connect(lambda _, c=code: self._select_state(c))
            self._state_buttons[code] = btn
            layout.addWidget(btn)

        layout.addStretch()
        total = sum(len(self.db.towers(s)) for s in self.db.states())
        lbl2 = QLabel(f"Total: {total} towers")
        lbl2.setStyleSheet("color:#2a3450; font-size:11px; padding:4px 8px;")
        layout.addWidget(lbl2)
        return sidebar

    # ── Tower tab ──────────────────────────────────────────────────────────

    def _build_tower_tab(self) -> QWidget:
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(16, 12, 16, 12)
        vbox.setSpacing(8)

        hdr = QHBoxLayout()
        self._state_label = QLabel("Select a state")
        self._state_label.setObjectName("heading")
        hdr.addWidget(self._state_label)
        hdr.addStretch()
        for label, obj, slot in [
            ("+ Add",          "btnSuccess", self._add_tower),
            ("Edit",           "",           self._edit_tower),
            ("Delete",         "btnDanger",  self._delete_tower),
            ("View Config",    "btnPrimary", self._view_tower_config),
        ]:
            b = QPushButton(label)
            if obj: b.setObjectName(obj)
            b.clicked.connect(slot)
            hdr.addWidget(b)
        vbox.addLayout(hdr)

        self._tower_table = QTableWidget(0, 9)
        self._tower_table.setHorizontalHeaderLabels(
            ["ID", "Name", "City", "Carrier", "Band", "EARFCN", "PCI", "TAC", "TX Power"])
        self._tower_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)
        self._tower_table.verticalHeader().setVisible(False)
        self._tower_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._tower_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tower_table.setAlternatingRowColors(True)
        self._tower_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tower_table.selectionModel().selectionChanged.connect(self._on_tower_selected)
        self._tower_table.doubleClicked.connect(lambda _: self._view_tower_config())
        vbox.addWidget(self._tower_table, 1)

        # Selected tower info bar
        self._tower_info = QLabel("No tower selected")
        self._tower_info.setStyleSheet(
            "background:#141820; color:#4a5880; padding:6px 12px; "
            "border-radius:5px; font-size:12px;")
        vbox.addWidget(self._tower_info)

        return w

    # ── SIM tab ────────────────────────────────────────────────────────────

    def _build_sim_tab(self) -> QWidget:
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(16, 12, 16, 12)
        vbox.setSpacing(8)

        hdr = QHBoxLayout()
        lbl = QLabel("SIM Card Profiles")
        lbl.setObjectName("heading")
        hdr.addWidget(lbl)
        hdr.addStretch()

        for label, obj, slot in [
            ("+ Add SIM",      "btnSuccess", self._add_sim),
            ("Import .grsp…",  "",           self._import_grsp),
            ("Edit",           "",           self._edit_sim),
            ("Delete",         "btnDanger",  self._delete_sim),
            ("Export .grsp",   "btnPrimary", self._export_sim_grsp),
            ("Export ue.conf", "",           self._export_ue_conf),
        ]:
            b = QPushButton(label)
            if obj: b.setObjectName(obj)
            b.clicked.connect(slot)
            hdr.addWidget(b)

        vbox.addLayout(hdr)

        self._sim_table = QTableWidget(0, 7)
        self._sim_table.setHorizontalHeaderLabels(
            ["ID", "Name", "Carrier", "Mode", "MCC", "MNC", "IMSI"])
        self._sim_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)
        self._sim_table.verticalHeader().setVisible(False)
        self._sim_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._sim_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._sim_table.setAlternatingRowColors(True)
        self._sim_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._sim_table.selectionModel().selectionChanged.connect(self._on_sim_selected)
        self._sim_table.doubleClicked.connect(lambda _: self._edit_sim())
        vbox.addWidget(self._sim_table, 1)

        self._refresh_sim_table()
        return w

    # ── Launch tab ─────────────────────────────────────────────────────────

    def _build_launch_tab(self) -> QWidget:
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(20, 16, 20, 16)
        vbox.setSpacing(14)

        # ── Selected tower/SIM info ──
        self._launch_info = QLabel("Select a tower in Base Stations tab")
        self._launch_info.setStyleSheet(
            "background:#141820; color:#60a0e0; padding:10px 14px; "
            "border-radius:7px; font-size:13px; font-weight:bold;")
        self._launch_info.setWordWrap(True)
        vbox.addWidget(self._launch_info)

        # ── Action buttons ──
        btn_row1 = QHBoxLayout()
        btn_row1.setSpacing(10)

        self._btn_gen_sim = QPushButton("1. Generate SIM for this tower")
        self._btn_gen_sim.setObjectName("btnSuccess")
        self._btn_gen_sim.setMinimumHeight(44)
        self._btn_gen_sim.setToolTip("Auto-generate IMSI/Ki/OPc matched to selected tower's MCC/MNC")
        self._btn_gen_sim.clicked.connect(self._gen_sim_for_tower)
        btn_row1.addWidget(self._btn_gen_sim)

        self._btn_export_grsp = QPushButton("2. Export .grsp (flash SIM)")
        self._btn_export_grsp.setObjectName("btnPrimary")
        self._btn_export_grsp.setMinimumHeight(44)
        self._btn_export_grsp.setToolTip("Save .grsp file to open in GRSIMWrite and flash blank SIM card")
        self._btn_export_grsp.clicked.connect(self._export_bundle_grsp)
        btn_row1.addWidget(self._btn_export_grsp)

        self._btn_export_all = QPushButton("3. Export all configs")
        self._btn_export_all.setMinimumHeight(44)
        self._btn_export_all.setToolTip("Save enb.conf / rr.conf / sib.conf / epc.conf / user_db.csv / ue.conf")
        self._btn_export_all.clicked.connect(self._export_bundle)
        btn_row1.addWidget(self._btn_export_all)

        vbox.addLayout(btn_row1)

        # ── WSL2 Launch ──
        grp_wsl = QGroupBox("Launch srsRAN in WSL2 (Windows)")
        wsl_layout = QVBoxLayout(grp_wsl)
        wsl_layout.setSpacing(10)

        info = QLabel(
            "Кнопки ниже деплоят конфиги в WSL2 и запускают srsepc / srsenb в отдельных окнах.\n"
            "LimeSDR должен быть подключён. В WSL2 должен быть установлен srsRAN_4G + SoapySDR."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#5a6888; font-size:12px;")
        wsl_layout.addWidget(info)

        btn_row2 = QHBoxLayout()
        btn_row2.setSpacing(10)

        self._btn_deploy = QPushButton("Deploy configs to WSL2")
        self._btn_deploy.setMinimumHeight(40)
        self._btn_deploy.clicked.connect(self._deploy_to_wsl)
        btn_row2.addWidget(self._btn_deploy)

        self._btn_epc = QPushButton("Start EPC  (srsepc)")
        self._btn_epc.setObjectName("btnSuccess")
        self._btn_epc.setMinimumHeight(40)
        self._btn_epc.clicked.connect(self._launch_epc)
        btn_row2.addWidget(self._btn_epc)

        self._btn_enb = QPushButton("Start eNB  (srsenb + LimeSDR)")
        self._btn_enb.setObjectName("btnPrimary")
        self._btn_enb.setMinimumHeight(40)
        self._btn_enb.clicked.connect(self._launch_enb)
        btn_row2.addWidget(self._btn_enb)

        self._btn_stop = QPushButton("Stop all")
        self._btn_stop.setObjectName("btnDanger")
        self._btn_stop.setMinimumHeight(40)
        self._btn_stop.clicked.connect(self._stop_all)
        btn_row2.addWidget(self._btn_stop)

        wsl_layout.addLayout(btn_row2)

        # Status
        self._wsl_status = QLabel("WSL2 status: not checked")
        self._wsl_status.setStyleSheet("color:#4a5870; font-size:12px; padding:2px;")
        wsl_layout.addWidget(self._wsl_status)

        vbox.addWidget(grp_wsl)

        # ── SIM card info box ──
        self._grp_sim_info = QGroupBox("Generated SIM — ready to flash")
        sim_info_layout = QVBoxLayout(self._grp_sim_info)
        self._sim_info_text = QTextEdit()
        self._sim_info_text.setReadOnly(True)
        self._sim_info_text.setMaximumHeight(140)
        self._sim_info_text.setFont(QFont("Consolas", 11))
        self._sim_info_text.setStyleSheet(
            "background:#0e1218; color:#80e8a0; border:none;")
        self._sim_info_text.setPlaceholderText(
            "Нажми «Generate SIM for this tower» — данные появятся здесь")
        sim_info_layout.addWidget(self._sim_info_text)
        self._grp_sim_info.setVisible(False)
        vbox.addWidget(self._grp_sim_info)

        # ── WSL2 install instructions ──
        grp_install = QGroupBox("Установка srsRAN в WSL2 (один раз)")
        inst_layout = QVBoxLayout(grp_install)
        inst_text = QTextEdit()
        inst_text.setReadOnly(True)
        inst_text.setMaximumHeight(130)
        inst_text.setFont(QFont("Consolas", 10))
        inst_text.setPlainText(
            "# 1. PowerShell (admin): wsl --install  →  перезагрузка\n"
            "# 2. В WSL2 Ubuntu:\n"
            "sudo apt update && sudo apt install -y build-essential cmake git \\\n"
            "  libfftw3-dev libmbedtls-dev libboost-all-dev \\\n"
            "  libconfig++-dev libsctp-dev libzmq3-dev \\\n"
            "  soapysdr-tools soapysdr-module-lms7\n"
            "git clone https://github.com/srsRAN/srsRAN_4G.git\n"
            "cd srsRAN_4G && mkdir build && cd build\n"
            "cmake .. -DCMAKE_BUILD_TYPE=Release && make -j$(nproc)\n"
            "sudo make install && srsran_install_configs.sh user"
        )
        inst_layout.addWidget(inst_text)
        vbox.addWidget(grp_install)

        vbox.addStretch()
        return w

    # ══════════════════════════════════════════════════════════════════════
    # STATE / TABLE LOGIC
    # ══════════════════════════════════════════════════════════════════════

    def _select_state(self, state: str):
        for code, btn in self._state_buttons.items():
            active = code == state
            btn.setProperty("active", "true" if active else "false")
            btn.style().unpolish(btn); btn.style().polish(btn)

        self._current_state = state
        towers = self.db.towers(state)
        self._state_label.setText(
            f"{STATE_NAMES.get(state, state)}  "
            f"<span style='color:#3a5080; font-size:14px;'>({len(towers)} towers)</span>")
        self._refresh_tower_table(towers)

    def _refresh_tower_table(self, towers: list[dict]):
        tbl = self._tower_table
        tbl.setRowCount(0)
        for t in towers:
            row = tbl.rowCount()
            tbl.insertRow(row)
            for col, val in enumerate([
                t['id'], t['name'], t['city'], t['carrier'],
                f"B{t['band']} ({BAND_FREQ.get(t['band'],'')})",
                str(t['dl_earfcn']), str(t['pci']), str(t['tac']),
                f"{t['tx_power']} dBm"
            ]):
                item = QTableWidgetItem(val)
                item.setData(Qt.ItemDataRole.UserRole, t['id'])
                if col == 3:
                    item.setForeground(QColor(CARRIER_COLORS.get(t['carrier'], "#607090")))
                    f = item.font(); f.setBold(True); item.setFont(f)
                tbl.setItem(row, col, item)
        tbl.resizeColumnsToContents()
        tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

    def _on_tower_selected(self):
        rows = self._tower_table.selectionModel().selectedRows()
        if rows:
            tid = self._tower_table.item(rows[0].row(), 0).text()
            self._selected_tower = self.db.tower_by_id(tid)
            if self._selected_tower:
                t = self._selected_tower
                self._tower_info.setText(
                    f"Selected:  {t['name']}  |  "
                    f"Band {t['band']}  EARFCN {t['dl_earfcn']}  "
                    f"PCI {t['pci']}  TAC {t['tac']}  "
                    f"MCC {t['mcc']} MNC {t['mnc']}")
                self._launch_info.setText(
                    f"Tower:  {t['name']}\n"
                    f"Band {t['band']}  ·  EARFCN {t['dl_earfcn']}  ·  "
                    f"PCI {t['pci']}  ·  {t['carrier']}  ·  "
                    f"MCC {t['mcc']} MNC {t['mnc']}")
                self._active_tower_sim = None
                self._grp_sim_info.setVisible(False)
                self._sim_info_text.clear()
                self.statusBar().showMessage(
                    f"{t['name']}  |  Band {t['band']}  EARFCN {t['dl_earfcn']}")
                # Auto-generate SIM immediately on tower select
                self._gen_sim_for_tower()
        else:
            self._selected_tower = None

    def _refresh_sim_table(self):
        tbl = self._sim_table
        tbl.setRowCount(0)
        for s in self.db.sims():
            row = tbl.rowCount()
            tbl.insertRow(row)
            for col, val in enumerate([
                s['id'], s['name'], s.get('carrier',''),
                s.get('mode',''), s.get('mcc',''),
                s.get('mnc',''), s.get('imsi','—')
            ]):
                item = QTableWidgetItem(val)
                item.setData(Qt.ItemDataRole.UserRole, s['id'])
                if col == 3:
                    item.setForeground(
                        QColor("#80e880") if val == "soft" else QColor("#e0a050"))
                tbl.setItem(row, col, item)
        tbl.resizeColumnsToContents()
        tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

    def _on_sim_selected(self):
        rows = self._sim_table.selectionModel().selectedRows()
        if rows:
            sid = self._sim_table.item(rows[0].row(), 0).text()
            self._selected_sim = self.db.sim_by_id(sid)
        else:
            self._selected_sim = None

    # ══════════════════════════════════════════════════════════════════════
    # CRUD
    # ══════════════════════════════════════════════════════════════════════

    def _add_tower(self):
        state = self._current_state or "CO"
        dlg = TowerEditorDialog(None, state=state, parent=self)
        if dlg.exec() == TowerEditorDialog.DialogCode.Accepted:
            self.db.add_tower(dlg.result_tower())
            self._select_state(state)
            self._update_sidebar_count(state)

    def _edit_tower(self):
        if not self._selected_tower:
            QMessageBox.information(self, "Info", "Выберите вышку.")
            return
        dlg = TowerEditorDialog(self._selected_tower, parent=self)
        if dlg.exec() == TowerEditorDialog.DialogCode.Accepted:
            self.db.save_tower(dlg.result_tower())
            self._select_state(self._current_state)

    def _delete_tower(self):
        if not self._selected_tower:
            return
        t = self._selected_tower
        if QMessageBox.question(self, "Удалить",
                f"Удалить вышку <b>{t['name']}</b>?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.db.delete_tower(t['id'])
            self._selected_tower = None
            self._select_state(self._current_state)
            self._update_sidebar_count(self._current_state)

    def _add_sim(self):
        dlg = SimEditorDialog(parent=self)
        if dlg.exec() == SimEditorDialog.DialogCode.Accepted:
            self.db.add_sim(dlg.result_sim())
            self._refresh_sim_table()

    def _edit_sim(self):
        if not self._selected_sim:
            QMessageBox.information(self, "Info", "Выберите SIM профиль.")
            return
        dlg = SimEditorDialog(self._selected_sim, parent=self)
        if dlg.exec() == SimEditorDialog.DialogCode.Accepted:
            self.db.save_sim(dlg.result_sim())
            self._refresh_sim_table()

    def _delete_sim(self):
        if not self._selected_sim:
            return
        s = self._selected_sim
        if QMessageBox.question(self, "Удалить",
                f"Удалить профиль <b>{s['name']}</b>?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.db.delete_sim(s['id'])
            self._selected_sim = None
            self._refresh_sim_table()

    # ══════════════════════════════════════════════════════════════════════
    # CONFIG / GRSP ACTIONS
    # ══════════════════════════════════════════════════════════════════════

    def _view_tower_config(self):
        if not self._selected_tower:
            QMessageBox.information(self, "Info", "Выберите вышку.")
            return
        sim = self._active_tower_sim or self._selected_sim
        dlg = ConfigViewerDialog(self._selected_tower, sim=sim, parent=self)
        dlg.exec()

    def _gen_sim_for_tower(self):
        if not self._selected_tower:
            QMessageBox.information(self, "Info", "Сначала выберите вышку.")
            return
        t = self._selected_tower
        sim = generate_sim_for_tower(t)
        self._active_tower_sim = sim

        # Show in info box
        self._grp_sim_info.setVisible(True)
        self._sim_info_text.setPlainText(
            f"Tower  : {t['name']}\n"
            f"IMSI   : {sim['imsi']}\n"
            f"Ki     : {sim['ki']}\n"
            f"OPc    : {sim['opc']}\n"
            f"MCC    : {sim['mcc']}   MNC: {sim['mnc']}\n"
            f"APN    : {sim['apn']}\n"
            f"Mode   : Milenage\n\n"
            f"→ Нажми «Export .grsp» чтобы прошить SIM\n"
            f"→ Нажми «Export all configs» чтобы получить конфиги srsRAN"
        )
        self.statusBar().showMessage(
            f"SIM создан: IMSI {sim['imsi']}  Ki {sim['ki'][:8]}…")

    def _export_bundle_grsp(self):
        """Export .grsp for active or selected SIM."""
        sim = self._active_tower_sim or self._selected_sim
        if not sim:
            if not self._selected_tower:
                QMessageBox.information(self, "Info",
                    "Сначала выберите вышку.")
                return
            sim = generate_sim_for_tower(self._selected_tower)
            self._active_tower_sim = sim

        # Validate
        if not sim.get("imsi") or not sim.get("ki") or not sim.get("opc"):
            QMessageBox.critical(self, "Ошибка",
                f"SIM профиль неполный!\n"
                f"IMSI: {sim.get('imsi','(пусто)')}\n"
                f"Ki:   {sim.get('ki','(пусто)')}\n"
                f"OPc:  {sim.get('opc','(пусто)')}\n\n"
                "Нажми «Generate SIM for this tower» заново.")
            return

        folder = QFileDialog.getExistingDirectory(self, "Папка для .grsp файла")
        if not folder:
            return
        path = export_grsp(sim, folder)
        QMessageBox.information(self, "Готово",
            f"Файл сохранён:\n{path}\n\n"
            f"IMSI: {sim['imsi']}\n"
            f"Ki:   {sim['ki']}\n"
            f"OPc:  {sim['opc']}\n\n"
            "Открой в GRSIMWrite → Write Card → вставь blank SIM.")

    def _export_sim_grsp(self):
        if not self._selected_sim:
            QMessageBox.information(self, "Info", "Выберите SIM профиль.")
            return
        folder = QFileDialog.getExistingDirectory(self, "Папка для .grsp файла")
        if not folder:
            return
        path = export_grsp(self._selected_sim, folder)
        QMessageBox.information(self, "Экспорт .grsp", f"Сохранено:\n{path}")

    def _export_bundle(self):
        if not self._selected_tower:
            QMessageBox.information(self, "Info", "Выберите вышку.")
            return
        sim = self._active_tower_sim or self._selected_sim
        if not sim:
            sim = generate_sim_for_tower(self._selected_tower)
            self._active_tower_sim = sim

        folder = QFileDialog.getExistingDirectory(self, "Папка для конфигов")
        if not folder:
            return

        subfolder = os.path.join(folder, self._selected_tower['id'])
        paths = export_full_bundle(self._selected_tower, sim, subfolder)
        grsp_path = export_grsp(sim, subfolder)
        paths.append(grsp_path)

        QMessageBox.information(self, "Экспорт завершён",
            f"Сохранено {len(paths)} файлов в:\n{subfolder}\n\n"
            + "\n".join(os.path.basename(p) for p in paths))

    def _export_ue_conf(self):
        if not self._selected_sim:
            QMessageBox.information(self, "Info", "Выберите SIM профиль.")
            return
        folder = QFileDialog.getExistingDirectory(self, "Папка для ue.conf")
        if not folder:
            return
        path = export_ue_conf(self._selected_sim, self._selected_tower, folder)
        QMessageBox.information(self, "Экспорт", f"Сохранено:\n{path}")

    def _import_grsp(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Выбери .grsp файлы",
            os.path.expanduser("~/Downloads"),
            "GRSIMWrite (*.grsp *.grps);;Все файлы (*)"
        )
        if not paths:
            return
        profiles, errors = import_grsp_files(paths)
        if errors:
            QMessageBox.warning(self, "Предупреждения", "\n".join(errors))
        if not profiles:
            return
        for p in profiles:
            self.db.add_sim(p)
        self._refresh_sim_table()
        self._tabs.setCurrentWidget(self._sim_tab)
        lines = [f"✓  {p['name']}  IMSI: {p['imsi']}" for p in profiles]
        QMessageBox.information(self, f"Импортировано {len(profiles)} профилей",
                                "\n".join(lines))

    # ══════════════════════════════════════════════════════════════════════
    # WSL2 LAUNCH
    # ══════════════════════════════════════════════════════════════════════

    def _check_wsl(self) -> bool:
        if sys.platform != "win32":
            self._wsl_status.setText("WSL2: не требуется (Linux/macOS)")
            return False
        try:
            r = subprocess.run(["wsl", "--status"],
                               capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                self._wsl_status.setText("WSL2: ✓ доступен")
                return True
        except Exception:
            pass
        self._wsl_status.setText("WSL2: не найден — установи через PowerShell: wsl --install")
        return False

    def _deploy_to_wsl(self):
        if not self._selected_tower:
            QMessageBox.information(self, "Info", "Выберите вышку.")
            return

        sim = self._active_tower_sim or self._selected_sim
        if not sim:
            sim = generate_sim_for_tower(self._selected_tower)
            self._active_tower_sim = sim

        # On non-Windows — just export to a folder the user picks
        if sys.platform != "win32":
            folder = QFileDialog.getExistingDirectory(self, "Папка для конфигов")
            if not folder:
                return
            subfolder = os.path.join(folder, self._selected_tower['id'])
            export_full_bundle(self._selected_tower, sim, subfolder)
            QMessageBox.information(self, "Экспорт",
                f"Конфиги сохранены:\n{subfolder}")
            return

        # Check WSL is available
        try:
            r = subprocess.run(["wsl", "--status"],
                               capture_output=True, text=True, timeout=8)
            if r.returncode != 0:
                raise FileNotFoundError
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            QMessageBox.warning(self, "WSL2 не найден",
                "WSL2 не установлен или не запущен.\n\n"
                "Установи: PowerShell (admin) → wsl --install\n\n"
                "Пока используй «Export all configs» для ручного копирования.")
            return

        tmp = tempfile.mkdtemp(prefix="srsran_")
        try:
            export_full_bundle(self._selected_tower, sim, tmp)

            # Convert Windows temp path to WSL path
            win_path = tmp.replace("\\", "/")
            r2 = subprocess.run(["wsl", "wslpath", win_path],
                                capture_output=True, text=True, timeout=8)
            wsl_tmp = r2.stdout.strip()
            if not wsl_tmp:
                raise RuntimeError("wslpath вернул пустой путь")

            wsl_dest = "~/.config/srsran"
            cmd = (f"mkdir -p {wsl_dest} && "
                   f"cp {wsl_tmp}/*.conf {wsl_dest}/ && "
                   f"cp {wsl_tmp}/user_db.csv /tmp/srsran_user_db.csv && "
                   f"sed -i 's/\\r//' {wsl_dest}/*.conf && "
                   f"sed -i 's/\\r//' /tmp/srsran_user_db.csv && "
                   f"echo DONE")
            r3 = subprocess.run(["wsl", "bash", "-c", cmd],
                                capture_output=True, text=True, timeout=20)
            if "DONE" in r3.stdout:
                self._wsl_status.setText("WSL2: ✓ конфиги скопированы")
                QMessageBox.information(self, "Deploy OK",
                    f"Конфиги скопированы в WSL2:\n{wsl_dest}\n\n"
                    "Теперь нажми  Start EPC  →  Start eNB")
            else:
                err = r3.stderr.strip() or r3.stdout.strip() or "Неизвестная ошибка"
                QMessageBox.warning(self, "Deploy ошибка", err)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка Deploy", str(e))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def _wsl_open_terminal(self, title: str, bash_cmd: str):
        """Open a new Windows Terminal / cmd window running a WSL2 command."""
        # Try Windows Terminal first, fall back to cmd
        wt = shutil.which("wt")
        if wt:
            subprocess.Popen([
                "wt", "--title", title, "--",
                "wsl", "bash", "-c",
                f"{bash_cmd}; echo '--- Press Enter to close ---'; read"
            ])
        else:
            subprocess.Popen(
                f'start "{title}" wsl bash -c "{bash_cmd}; read"',
                shell=True
            )

    def _launch_epc(self):
        if not self._check_wsl():
            if sys.platform != "win32":
                QMessageBox.information(self, "Linux/macOS",
                    "Запусти в терминале:\n"
                    "sudo srsepc ~/.config/srsran/epc.conf")
            return
        self._wsl_open_terminal(
            "srsEPC",
            "sudo srsepc ~/.config/srsran/epc.conf"
        )
        self._wsl_status.setText("WSL2: ▶ srsepc запускается…")

    def _launch_enb(self):
        if not self._check_wsl():
            if sys.platform != "win32":
                QMessageBox.information(self, "Linux/macOS",
                    "Запусти в терминале:\n"
                    "sudo srsenb ~/.config/srsran/enb.conf "
                    "--rf.device_name=soapy --rf.device_args=\"driver=lime\"")
            return
        self._wsl_open_terminal(
            "srsENB-LimeSDR",
            "sudo srsenb ~/.config/srsran/enb.conf "
            "--rf.device_name=soapy --rf.device_args=\"driver=lime\""
        )
        self._wsl_status.setText("WSL2: ▶ srsenb (LimeSDR) запускается…")

    def _stop_all(self):
        if sys.platform == "win32":
            subprocess.run(["wsl", "bash", "-c",
                            "sudo pkill -f srsenb; sudo pkill -f srsepc"],
                           capture_output=True)
        else:
            subprocess.run(["bash", "-c",
                            "sudo pkill -f srsenb; sudo pkill -f srsepc"],
                           capture_output=True)
        self._wsl_status.setText("WSL2: ■ процессы остановлены")

    # ══════════════════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════════════════

    def _update_sidebar_count(self, state: str):
        if state in self._state_buttons:
            count = len(self.db.towers(state))
            self._state_buttons[state].setText(
                f"{state}  {STATE_NAMES.get(state, state)}\n{count} towers")
