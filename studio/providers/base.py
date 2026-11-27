from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class KeyframeProvider(ABC):
    def __init__(self, width: int = 832, height: int = 480, **_):
        self.width, self.height = width, height

    @abstractmethod
    def generate(self, prompt: str, negative: str, out_path: Path, label: str = "") -> Path:
        """Write a PNG to out_path and return it."""


class AnimateProvider(ABC):
    def __init__(self, fps: int = 16, **_):
        self.fps = fps

    @abstractmethod
    def animate(self, image: Path, prompt: str, negative: str, duration: float,
                out_path: Path, label: str = "") -> Path:
        """Write an MP4 to out_path and return it."""
