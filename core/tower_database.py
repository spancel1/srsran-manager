"""Tower and SIM profile database manager."""
from __future__ import annotations
import json
import os
from typing import Any

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

STATE_NAMES = {
    "CO": "Colorado",
    "VA": "Virginia",
    "WV": "West Virginia",
    "OH": "Ohio",
    "PA": "Pennsylvania",
    "IL": "Illinois",
    "KS": "Kansas",
}

CARRIER_COLORS = {
    "AT&T":    "#00A8E0",
    "Verizon": "#CD040B",
    "T-Mobile":"#E20074",
}

BAND_FREQ = {
    2:  "1900 MHz",
    4:  "1700/2100 MHz (AWS)",
    5:  "850 MHz",
    12: "700 MHz (lower A)",
    13: "700 MHz (upper C)",
    17: "700 MHz (lower B)",
}


class TowerDatabase:
    def __init__(self) -> None:
        self._towers: dict[str, list[dict[str, Any]]] = {}
        self._sims: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        towers_path = os.path.join(_DATA_DIR, "towers.json")
        sims_path   = os.path.join(_DATA_DIR, "sim_profiles.json")

        with open(towers_path, encoding="utf-8") as f:
            data = json.load(f)
        # Inject state key into each tower for convenience
        for state, towers in data.items():
            for t in towers:
                t["state"] = state
            self._towers[state] = towers

        with open(sims_path, encoding="utf-8") as f:
            self._sims = json.load(f)["profiles"]

    def states(self) -> list[str]:
        return sorted(self._towers.keys())

    def towers(self, state: str) -> list[dict[str, Any]]:
        return self._towers.get(state, [])

    def tower_by_id(self, tower_id: str) -> dict[str, Any] | None:
        for towers in self._towers.values():
            for t in towers:
                if t["id"] == tower_id:
                    return t
        return None

    def sims(self) -> list[dict[str, Any]]:
        return self._sims

    def sim_by_id(self, sim_id: str) -> dict[str, Any] | None:
        for s in self._sims:
            if s["id"] == sim_id:
                return s
        return None

    def save_tower(self, tower: dict[str, Any]) -> None:
        state = tower["state"]
        towers = self._towers.setdefault(state, [])
        for i, t in enumerate(towers):
            if t["id"] == tower["id"]:
                towers[i] = tower
                break
        else:
            towers.append(tower)
        self._persist_towers()

    def add_tower(self, tower: dict[str, Any]) -> None:
        state = tower["state"]
        self._towers.setdefault(state, []).append(tower)
        self._persist_towers()

    def delete_tower(self, tower_id: str) -> None:
        for state, towers in self._towers.items():
            self._towers[state] = [t for t in towers if t["id"] != tower_id]
        self._persist_towers()

    def save_sim(self, sim: dict[str, Any]) -> None:
        for i, s in enumerate(self._sims):
            if s["id"] == sim["id"]:
                self._sims[i] = sim
                break
        else:
            self._sims.append(sim)
        self._persist_sims()

    def add_sim(self, sim: dict[str, Any]) -> None:
        self._sims.append(sim)
        self._persist_sims()

    def delete_sim(self, sim_id: str) -> None:
        self._sims = [s for s in self._sims if s["id"] != sim_id]
        self._persist_sims()

    def _persist_towers(self) -> None:
        path = os.path.join(_DATA_DIR, "towers.json")
        data = {state: [{k: v for k, v in t.items() if k != "state"}
                        for t in towers]
                for state, towers in self._towers.items()}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _persist_sims(self) -> None:
        path = os.path.join(_DATA_DIR, "sim_profiles.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"profiles": self._sims}, f, indent=2, ensure_ascii=False)
