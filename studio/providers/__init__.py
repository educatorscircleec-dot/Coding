"""Generation back-ends. Each is chosen by name in series/style.yaml or on the command line.

Keyframe providers: make a still image from text.
Animate providers:  make a short clip from that image + a motion prompt.
"""

from __future__ import annotations

from .base import AnimateProvider, KeyframeProvider


def get_keyframe_provider(name: str, **opts) -> KeyframeProvider:
    if name == "placeholder":
        from .placeholder import PlaceholderKeyframes
        return PlaceholderKeyframes(**opts)
    if name == "huggingface":
        from .huggingface import HFKeyframes
        return HFKeyframes(**opts)
    raise ValueError(f"unknown keyframe provider '{name}'")


def get_animate_provider(name: str, **opts) -> AnimateProvider:
    if name == "placeholder":
        from .placeholder import PlaceholderAnimate
        return PlaceholderAnimate(**opts)
    if name == "wan":
        from .wan import WanAnimate
        return WanAnimate(**opts)
    raise ValueError(f"unknown animate provider '{name}'")
