"""Main application window."""
from __future__ import annotations
import os
import subprocess
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QTabWidget, QHeaderView, QAbstractItemView, QFileDialog,
    QMessageBox, QStatusBar, QFrame, QScrollArea, QSizePolicy,
    QToolBar, QApplication
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont, QColor, QAction

from core.tower_database import TowerDatabase, STATE_NAMES, CARRIER_COLORS, BAND_FREQ
from core.config_generator import export_tower_configs, export_ue_conf, generate_ue_conf
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
        self.setWindowTitle("srsRAN Manager — US LTE Base Station Profiles")
        self.setMinimumSize(1200, 740)
        self._build_ui()
        self._select_state(list(STATE_NAMES.keys())[0])

    # ── UI construction ─────────────────────────────────────────────────

    def _build_ui(self):
        # Toolbar
        self._build_toolbar()

        # Central area: sidebar + main content
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        sidebar = self._build_sidebar()
        root.addWidget(sidebar)

        # Vertical separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("background:#2a2d36;")
        sep.setFixedWidth(1)
        root.addWidget(sep)

        # Tab area
        self._tabs = QTabWidget()
        self._tabs.setObjectName("mainTabs")
        root.addWidget(self._tabs, 1)

        # Tab 1: Towers
        self._tower_tab = self._build_tower_tab()
        self._tabs.addTab(self._tower_tab, "  Base Stations  ")

        # Tab 2: SIM Profiles
        self._sim_tab = self._build_sim_tab()
        self._tabs.addTab(self._sim_tab, "  SIM Profiles  ")

        # Tab 3: Config Preview
        self._preview_tab = self._build_preview_tab()
        self._tabs.addTab(self._preview_tab, "  Quick Preview  ")

        # Status bar
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready — srsRAN Manager v1.0")

    def _build_toolbar(self):
        tb = QToolBar("Main")
        tb.setMovable(False)
        tb.setIconSize(QSize(20, 20))
        tb.setObjectName("mainToolbar")

        act_add_tower = QAction("+ Add Tower", self)
        act_add_tower.setStatusTip("Add a new tower profile")
        act_add_tower.triggered.connect(self._add_tower)
        tb.addAction(act_add_tower)

        act_add_sim = QAction("+ Add SIM", self)
        act_add_sim.setStatusTip("Add a new SIM profile")
        act_add_sim.triggered.connect(self._add_sim)
        tb.addAction(act_add_sim)

        act_import_grsp = QAction("Import .grsp…", self)
        act_import_grsp.setStatusTip("Import SIM profiles from GRSIMWrite .grsp files")
        act_import_grsp.triggered.connect(self._import_grsp)
        tb.addAction(act_import_grsp)

        tb.addSeparator()

        act_export = QAction("Export configs…", self)
        act_export.setStatusTip("Export srsRAN config files to a folder")
        act_export.triggered.connect(self._export_selected)
        tb.addAction(act_export)

        act_wsl = QAction("Deploy to WSL2", self)
        act_wsl.setStatusTip("Copy configs to WSL2 srsRAN config directory")
        act_wsl.triggered.connect(self._deploy_to_wsl)
        tb.addAction(act_wsl)

        tb.addSeparator()

        # right-align info label
        spacer = QWidget(); spacer.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tb.addWidget(spacer)

        lbl = QLabel("  srsRAN 4G Manager  ")
        lbl.setStyleSheet("color:#4a5880; font-weight:bold; font-size:12px;")
        tb.addWidget(lbl)

        self.addToolBar(tb)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(190)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(4)

        lbl = QLabel("STATES")
        lbl.setStyleSheet("color:#3a4560; font-size:10px; font-weight:bold; "
                          "letter-spacing:1.5px; padding: 4px 8px 6px 8px;")
        layout.addWidget(lbl)

        for code in sorted(STATE_NAMES.keys()):
            name = STATE_NAMES[code]
            count = len(self.db.towers(code))
            btn = QPushButton(f"{code}  {name}\n{count} towers")
            btn.setObjectName("stateBtn")
            btn.setCheckable(False)
            btn.setProperty("active", "false")
            btn.clicked.connect(lambda checked, c=code: self._select_state(c))
            self._state_buttons[code] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # Stats
        total = sum(len(self.db.towers(s)) for s in self.db.states())
        lbl_total = QLabel(f"Total towers: {total}")
        lbl_total.setStyleSheet("color:#3a4560; font-size:11px; padding:4px 8px;")
        layout.addWidget(lbl_total)

        return sidebar

    def _build_tower_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Header row
        hdr = QHBoxLayout()
        self._state_label = QLabel("Select a state")
        self._state_label.setObjectName("heading")
        hdr.addWidget(self._state_label)
        hdr.addStretch()

        btn_add = QPushButton("+ Add Tower")
        btn_add.setObjectName("btnSuccess")
        btn_add.clicked.connect(self._add_tower)
        hdr.addWidget(btn_add)

        btn_edit = QPushButton("Edit")
        btn_edit.clicked.connect(self._edit_tower)
        hdr.addWidget(btn_edit)

        btn_del = QPushButton("Delete")
        btn_del.setObjectName("btnDanger")
        btn_del.clicked.connect(self._delete_tower)
        hdr.addWidget(btn_del)

        btn_cfg = QPushButton("View / Export Config")
        btn_cfg.setObjectName("btnPrimary")
        btn_cfg.clicked.connect(self._view_tower_config)
        hdr.addWidget(btn_cfg)

        layout.addLayout(hdr)

        # Tower table
        self._tower_table = QTableWidget(0, 9)
        self._tower_table.setHorizontalHeaderLabels([
            "ID", "Name", "City", "Carrier", "Band", "EARFCN", "PCI", "TAC", "TX Power"
        ])
        self._tower_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)
        self._tower_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents)
        self._tower_table.verticalHeader().setVisible(False)
        self._tower_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._tower_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tower_table.setAlternatingRowColors(True)
        self._tower_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tower_table.selectionModel().selectionChanged.connect(self._on_tower_selected)
        self._tower_table.doubleClicked.connect(lambda _: self._edit_tower())
        layout.addWidget(self._tower_table, 1)

        return w

    def _build_sim_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        hdr = QHBoxLayout()
        lbl = QLabel("SIM Card Profiles")
        lbl.setObjectName("heading")
        hdr.addWidget(lbl)
        hdr.addStretch()

        btn_add = QPushButton("+ Add SIM")
        btn_add.setObjectName("btnSuccess")
        btn_add.clicked.connect(self._add_sim)
        hdr.addWidget(btn_add)

        btn_import = QPushButton("Import .grsp…")
        btn_import.setToolTip("Import SIM profiles from GRSIMWrite .grsp / .grps files")
        btn_import.clicked.connect(self._import_grsp)
        hdr.addWidget(btn_import)

        btn_edit = QPushButton("Edit")
        btn_edit.clicked.connect(self._edit_sim)
        hdr.addWidget(btn_edit)

        btn_del = QPushButton("Delete")
        btn_del.setObjectName("btnDanger")
        btn_del.clicked.connect(self._delete_sim)
        hdr.addWidget(btn_del)

        btn_exp = QPushButton("Export ue.conf")
        btn_exp.setObjectName("btnPrimary")
        btn_exp.clicked.connect(self._export_ue_conf)
        hdr.addWidget(btn_exp)

        layout.addLayout(hdr)

        self._sim_table = QTableWidget(0, 7)
        self._sim_table.setHorizontalHeaderLabels([
            "ID", "Name", "Carrier", "Mode", "MCC", "MNC", "IMSI"
        ])
        self._sim_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)
        self._sim_table.verticalHeader().setVisible(False)
        self._sim_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._sim_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._sim_table.setAlternatingRowColors(True)
        self._sim_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._sim_table.selectionModel().selectionChanged.connect(self._on_sim_selected)
        self._sim_table.doubleClicked.connect(lambda _: self._edit_sim())
        layout.addWidget(self._sim_table, 1)

        self._refresh_sim_table()
        return w

    def _build_preview_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        lbl = QLabel("Quick Preview — select a tower and open config")
        lbl.setObjectName("subheading")
        layout.addWidget(lbl)

        info = QLabel(
            "Select a tower in the <b>Base Stations</b> tab, then click "
            "<b>View / Export Config</b> to preview and export:\n"
            "  • <b>enb.conf</b> — main eNodeB config\n"
            "  • <b>rr.conf</b>  — radio resources (EARFCN, PCI, TAC)\n"
            "  • <b>sib.conf</b> — system information blocks\n"
            "  • <b>ue.conf</b>  — UE / SIM card config\n\n"
            "Or use the <b>Export configs…</b> toolbar button to batch-export to a folder."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#6070a0; font-size:13px; line-height:160%; "
                           "background:#1a1d28; padding:16px; border-radius:8px;")
        layout.addWidget(info)

        # WSL2 deploy instructions
        wsl_box = QFrame()
        wsl_box.setStyleSheet("background:#161e28; border:1px solid #2a3050; "
                              "border-radius:8px; padding:4px;")
        wsl_layout = QVBoxLayout(wsl_box)
        wsl_lbl = QLabel("<b style='color:#60a0e0'>WSL2 Quick Deploy</b>")
        wsl_layout.addWidget(wsl_lbl)
        wsl_steps = QLabel(
            "1. Install WSL2 on Windows: <code>wsl --install</code>\n"
            "2. Inside WSL2 (Ubuntu), install srsRAN:\n"
            "   <code>sudo apt install cmake libfftw3-dev libmbedtls-dev \\\n"
            "         libboost-all-dev libconfig++-dev libsctp-dev</code>\n"
            "   <code>git clone https://github.com/srsRAN/srsRAN_4G.git</code>\n"
            "   <code>cd srsRAN_4G && mkdir build && cd build</code>\n"
            "   <code>cmake .. && make -j$(nproc)</code>\n"
            "3. Use <b>Deploy to WSL2</b> button above to copy configs to WSL2\n"
            "4. Run: <code>sudo srsenb ~/.config/srsran/enb.conf</code>"
        )
        wsl_steps.setWordWrap(True)
        wsl_steps.setStyleSheet("font-size:12px; font-family:Consolas; "
                                "color:#8090b0; line-height:160%;")
        wsl_layout.addWidget(wsl_steps)
        layout.addWidget(wsl_box)

        layout.addStretch()
        return w

    # ── State selection ──────────────────────────────────────────────────

    def _select_state(self, state: str):
        # Update buttons
        for code, btn in self._state_buttons.items():
            active = code == state
            btn.setProperty("active", "true" if active else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        self._current_state = state
        full_name = STATE_NAMES.get(state, state)
        towers = self.db.towers(state)
        self._state_label.setText(
            f"{full_name}  <span style='color:#4a6088; font-size:14px;'>"
            f"({len(towers)} towers)</span>"
        )
        self._refresh_tower_table(towers)

    # ── Tower table ──────────────────────────────────────────────────────

    def _refresh_tower_table(self, towers: list[dict]):
        tbl = self._tower_table
        tbl.setRowCount(0)
        for t in towers:
            row = tbl.rowCount()
            tbl.insertRow(row)
            cells = [
                t['id'],
                t['name'],
                t['city'],
                t['carrier'],
                f"B{t['band']} ({BAND_FREQ.get(t['band'], '')})",
                str(t['dl_earfcn']),
                str(t['pci']),
                str(t['tac']),
                f"{t['tx_power']} dBm",
            ]
            for col, val in enumerate(cells):
                item = QTableWidgetItem(val)
                item.setData(Qt.ItemDataRole.UserRole, t['id'])
                if col == 3:  # carrier column - color code
                    color = CARRIER_COLORS.get(t['carrier'], "#607090")
                    item.setForeground(QColor(color))
                    font = item.font(); font.setBold(True); item.setFont(font)
                tbl.setItem(row, col, item)
        tbl.resizeColumnsToContents()
        tbl.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)

    def _on_tower_selected(self):
        rows = self._tower_table.selectionModel().selectedRows()
        if rows:
            tower_id = self._tower_table.item(rows[0].row(), 0).text()
            self._selected_tower = self.db.tower_by_id(tower_id)
            if self._selected_tower:
                t = self._selected_tower
                self.statusBar().showMessage(
                    f"Selected: {t['name']}  |  "
                    f"Band {t['band']}  EARFCN {t['dl_earfcn']}  "
                    f"PCI {t['pci']}  TAC {t['tac']}"
                )
        else:
            self._selected_tower = None

    # ── SIM table ────────────────────────────────────────────────────────

    def _refresh_sim_table(self):
        tbl = self._sim_table
        tbl.setRowCount(0)
        for s in self.db.sims():
            row = tbl.rowCount()
            tbl.insertRow(row)
            cells = [
                s['id'], s['name'], s.get('carrier', ''),
                s.get('mode', ''), s.get('mcc', ''),
                s.get('mnc', ''), s.get('imsi', '—')
            ]
            for col, val in enumerate(cells):
                item = QTableWidgetItem(val)
                item.setData(Qt.ItemDataRole.UserRole, s['id'])
                if col == 3:  # mode
                    item.setForeground(
                        QColor("#80e880") if val == "soft" else QColor("#e0a050"))
                tbl.setItem(row, col, item)
        tbl.resizeColumnsToContents()
        tbl.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)

    def _on_sim_selected(self):
        rows = self._sim_table.selectionModel().selectedRows()
        if rows:
            sim_id = self._sim_table.item(rows[0].row(), 0).text()
            self._selected_sim = self.db.sim_by_id(sim_id)
        else:
            self._selected_sim = None

    # ── CRUD actions ─────────────────────────────────────────────────────

    def _add_tower(self):
        state = self._current_state or "CO"
        dlg = TowerEditorDialog(None, state=state, parent=self)
        if dlg.exec() == TowerEditorDialog.DialogCode.Accepted:
            self.db.add_tower(dlg.result_tower())
            self._select_state(state)
            self._update_sidebar_count(state)

    def _edit_tower(self):
        if not self._selected_tower:
            QMessageBox.information(self, "Info", "Select a tower first.")
            return
        dlg = TowerEditorDialog(self._selected_tower, parent=self)
        if dlg.exec() == TowerEditorDialog.DialogCode.Accepted:
            updated = dlg.result_tower()
            self.db.save_tower(updated)
            # If state changed, refresh old state and new state
            self._select_state(self._current_state)

    def _delete_tower(self):
        if not self._selected_tower:
            QMessageBox.information(self, "Info", "Select a tower first.")
            return
        t = self._selected_tower
        ret = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete tower <b>{t['name']}</b>?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ret == QMessageBox.StandardButton.Yes:
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
            QMessageBox.information(self, "Info", "Select a SIM profile first.")
            return
        dlg = SimEditorDialog(self._selected_sim, parent=self)
        if dlg.exec() == SimEditorDialog.DialogCode.Accepted:
            self.db.save_sim(dlg.result_sim())
            self._refresh_sim_table()

    def _delete_sim(self):
        if not self._selected_sim:
            QMessageBox.information(self, "Info", "Select a SIM profile first.")
            return
        s = self._selected_sim
        ret = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete SIM profile <b>{s['name']}</b>?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ret == QMessageBox.StandardButton.Yes:
            self.db.delete_sim(s['id'])
            self._selected_sim = None
            self._refresh_sim_table()

    # ── Config actions ───────────────────────────────────────────────────

    def _view_tower_config(self):
        if not self._selected_tower:
            QMessageBox.information(self, "Info", "Select a tower first.")
            return
        sim = self._selected_sim
        dlg = ConfigViewerDialog(self._selected_tower, sim=sim, parent=self)
        dlg.exec()

    def _export_selected(self):
        if not self._selected_tower:
            QMessageBox.information(self, "Info", "Select a tower first.")
            return
        folder = QFileDialog.getExistingDirectory(self, "Select export folder")
        if not folder:
            return
        subfolder = os.path.join(folder, self._selected_tower['id'])
        paths = export_tower_configs(self._selected_tower, subfolder)
        if self._selected_sim:
            paths.append(export_ue_conf(self._selected_sim, self._selected_tower, subfolder))
        QMessageBox.information(
            self, "Exported",
            f"Saved {len(paths)} config file(s) to:\n{subfolder}"
        )

    def _export_ue_conf(self):
        if not self._selected_sim:
            QMessageBox.information(self, "Info", "Select a SIM profile first.")
            return
        folder = QFileDialog.getExistingDirectory(self, "Select export folder")
        if not folder:
            return
        path = export_ue_conf(self._selected_sim, self._selected_tower, folder)
        QMessageBox.information(self, "Exported", f"Saved ue.conf to:\n{path}")

    def _deploy_to_wsl(self):
        if not self._selected_tower:
            QMessageBox.information(self, "Info", "Select a tower to deploy.")
            return

        # Check if WSL is available (Windows only)
        if sys.platform != "win32":
            QMessageBox.information(
                self, "WSL2 Deploy",
                "WSL2 deploy is only available on Windows.\n\n"
                "On Linux/Mac, use Export configs to export files directly."
            )
            return

        try:
            result = subprocess.run(
                ["wsl", "--status"], capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("WSL not found")
        except (FileNotFoundError, RuntimeError, subprocess.TimeoutExpired):
            QMessageBox.warning(
                self, "WSL2 Not Found",
                "WSL2 does not appear to be installed or running.\n\n"
                "Install WSL2: open PowerShell as admin and run:\n"
                "  wsl --install"
            )
            return

        # Export to temp dir, then copy via wsl cp
        import tempfile, shutil
        tmp = tempfile.mkdtemp(prefix="srsran_")
        try:
            paths = export_tower_configs(self._selected_tower, tmp)
            if self._selected_sim:
                paths.append(export_ue_conf(self._selected_sim, self._selected_tower, tmp))

            wsl_dest = "/home/$USER/.config/srsran"
            # Convert Windows path to WSL path
            wsl_tmp = subprocess.run(
                ["wsl", "wslpath", tmp.replace("\\", "/")],
                capture_output=True, text=True
            ).stdout.strip()

            cmd = f"mkdir -p {wsl_dest} && cp {wsl_tmp}/* {wsl_dest}/"
            proc = subprocess.run(
                ["wsl", "bash", "-c", cmd],
                capture_output=True, text=True, timeout=15
            )
            if proc.returncode == 0:
                QMessageBox.information(
                    self, "Deployed",
                    f"Configs deployed to WSL2:\n{wsl_dest}\n\n"
                    "To start srsENB in WSL2:\n"
                    "  sudo srsenb ~/.config/srsran/enb.conf"
                )
            else:
                QMessageBox.warning(self, "Deploy Failed",
                                    f"WSL2 copy failed:\n{proc.stderr}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def _import_grsp(self):
        """Import one or more GRSIMWrite .grsp files as SIM profiles."""
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select GRSIMWrite files",
            os.path.expanduser("~/Downloads"),
            "GRSIMWrite files (*.grsp *.grps);;All files (*)"
        )
        if not paths:
            return

        profiles, errors = import_grsp_files(paths)

        if errors:
            QMessageBox.warning(
                self, "Import Warnings",
                "Some files could not be imported:\n" + "\n".join(errors)
            )

        if not profiles:
            return

        for p in profiles:
            self.db.add_sim(p)

        self._refresh_sim_table()

        # Switch to SIM tab
        self._tabs.setCurrentWidget(self._sim_tab)

        # Show summary
        lines = []
        for p in profiles:
            lines.append(
                f"✓  {p['name']}\n"
                f"   IMSI: {p['imsi']}  |  Ki: {p['ki'][:8]}…  |  OPc: {p['opc'][:8]}…"
            )
        QMessageBox.information(
            self, f"Imported {len(profiles)} SIM profile(s)",
            "\n\n".join(lines)
        )

    # ── Helpers ──────────────────────────────────────────────────────────

    def _update_sidebar_count(self, state: str):
        if state in self._state_buttons:
            count = len(self.db.towers(state))
            name = STATE_NAMES.get(state, state)
            self._state_buttons[state].setText(f"{state}  {name}\n{count} towers")
