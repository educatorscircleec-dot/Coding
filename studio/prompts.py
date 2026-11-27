"""Turn a shot into prompts for the keyframe (image) and animate (video) steps."""

from __future__ import annotations

from .project import Project, Shot


def _clean(text: str | None) -> str:
    return " ".join((text or "").split()).strip().rstrip(".")


def keyframe_prompt(project: Project, shot: Shot) -> str:
    """Prompt for the still image that starts the shot."""
    parts = [_clean(shot.framing), _clean(shot.action)]
    for cid in shot.characters:
        parts.append(_clean(project.characters[cid].get("visual")))
    if shot.location:
        parts.append("setting: " + _clean(project.locations[shot.location].get("visual")))
    parts.append(_clean(project.style.get("style_prompt")))
    return ", ".join(p for p in parts if p)


def motion_prompt(project: Project, shot: Shot) -> str:
    """Prompt for the image-to-video model: what moves, plus the series style."""
    motion = _clean(shot.motion) or _clean(project.style.get("default_motion"))
    return ", ".join(p for p in [motion, _clean(project.style.get("style_prompt"))] if p)


def negative_prompt(project: Project) -> str:
    return _clean(project.style.get("negative_prompt"))


def build_all(project: Project, ep_id: str) -> list[dict]:
    ep = project.episode(ep_id)
    return [
        {
            "id": s.id,
            "duration": s.duration,
            "keyframe_prompt": keyframe_prompt(project, s),
            "motion_prompt": motion_prompt(project, s),
            "negative_prompt": negative_prompt(project),
            "dialogue": s.dialogue,
        }
        for s in ep.shots
    ]
