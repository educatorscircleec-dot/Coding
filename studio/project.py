"""Load and validate the series project (style, characters, locations, episodes)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


def _load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _load_dir(directory: Path) -> dict[str, dict]:
    if not directory.is_dir():
        return {}
    return {
        p.stem: _load_yaml(p)
        for p in sorted(directory.glob("*.yaml"))
        if not p.stem.startswith("_")
    }


@dataclass
class Shot:
    id: str
    location: str | None
    characters: list[str]
    framing: str
    action: str
    motion: str
    duration: float
    dialogue: list[dict] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "Shot":
        return cls(
            id=str(d["id"]),
            location=d.get("location"),
            characters=list(d.get("characters") or []),
            framing=d.get("framing", ""),
            action=d.get("action", ""),
            motion=d.get("motion", ""),
            duration=float(d.get("duration", 4)),
            dialogue=list(d.get("dialogue") or []),
        )


@dataclass
class Episode:
    id: str
    title: str
    path: Path
    shots: list[Shot]


class Project:
    def __init__(self, root: Path | str = "."):
        self.root = Path(root).resolve()
        self.style = _load_yaml(self.root / "series" / "style.yaml")
        self.characters = _load_dir(self.root / "characters")
        self.locations = _load_dir(self.root / "locations")

    @property
    def output_dir(self) -> Path:
        return self.root / "output"

    def episode_ids(self) -> list[str]:
        ep_dir = self.root / "episodes"
        return sorted(p.name for p in ep_dir.iterdir() if (p / "shots.yaml").exists())

    def episode(self, ep_id: str) -> Episode:
        path = self.root / "episodes" / ep_id
        data = _load_yaml(path / "shots.yaml")
        shots = [Shot.from_dict(s) for s in data.get("shots") or []]
        return Episode(id=ep_id, title=data.get("title", ep_id), path=path, shots=shots)

    def validate(self, ep_id: str) -> list[str]:
        """Return a list of problems (empty list means the episode is valid)."""
        errors: list[str] = []
        try:
            ep = self.episode(ep_id)
        except (FileNotFoundError, KeyError, yaml.YAMLError) as e:
            return [f"{ep_id}: cannot load shots.yaml ({e})"]
        if not ep.shots:
            errors.append(f"{ep_id}: no shots defined")
        seen: set[str] = set()
        for s in ep.shots:
            where = f"{ep_id}/{s.id}"
            if s.id in seen:
                errors.append(f"{where}: duplicate shot id")
            seen.add(s.id)
            if s.location and s.location not in self.locations:
                errors.append(f"{where}: unknown location '{s.location}'")
            for c in s.characters:
                if c not in self.characters:
                    errors.append(f"{where}: unknown character '{c}'")
            for line in s.dialogue:
                speaker = line.get("character")
                if speaker not in self.characters:
                    errors.append(f"{where}: dialogue from unknown character '{speaker}'")
                elif speaker not in s.characters:
                    errors.append(f"{where}: '{speaker}' speaks but is not listed in characters")
            if not s.action:
                errors.append(f"{where}: missing 'action'")
            if not 1 <= s.duration <= 5:
                errors.append(f"{where}: duration {s.duration}s outside the 1-5 s clip range")
        return errors
