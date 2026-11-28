import shutil
from pathlib import Path

import pytest

from studio.cli import main
from studio.project import Project
from studio.prompts import keyframe_prompt

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def proj(tmp_path):
    for d in ("series", "characters", "locations", "episodes"):
        shutil.copytree(ROOT / d, tmp_path / d)
    return tmp_path


def test_sample_episode_is_valid():
    assert Project(ROOT).validate("ep001") == []


def test_prompt_includes_character_location_and_style():
    p = Project(ROOT)
    shot = next(s for s in p.episode("ep001").shots if s.id == "s020")
    prompt = keyframe_prompt(p, shot)
    assert "copper repair-robot" in prompt
    assert "workshop" in prompt
    assert "watercolor" in prompt


def test_validate_catches_unknown_character(proj):
    f = proj / "episodes/ep001/shots.yaml"
    f.write_text(f.read_text().replace("characters: [pip]", "characters: [nobody]", 1))
    errors = Project(proj).validate("ep001")
    assert any("unknown character 'nobody'" in e for e in errors)


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_placeholder_render_end_to_end(proj):
    assert main(["--root", str(proj), "render", "ep001"]) == 0
    out = proj / "output/ep001"
    assert (out / "ep001.mp4").stat().st_size > 0
    assert "Mrs. Alder: It's been sulking all week." in (out / "ep001.srt").read_text()


def test_new_episode(proj):
    assert main(["--root", str(proj), "new-episode", "ep002", "Too Many Ramps"]) == 0
    assert Project(proj).validate("ep002") == []


def test_camera_moves_stay_inside_background():
    from studio.motion import camera_box
    for move in ("push_in", "pull_out", "pan_left", "pan_right", "tilt_up", "tilt_down"):
        for t in (0, 0.5, 1):
            x0, y0, x1, y1 = camera_box(t, move, 0.25, 0.5, (2600, 2600), (1080, 1920))
            assert 0 <= x0 < x1 <= 2600 and 0 <= y0 < y1 <= 2600, (move, t)


def test_map_card_renders_pins():
    from studio.motion import map_card
    card = map_card(3.0, {"label": "Test", "pins": [[0, 0]], "region": [-20, 20, -20, 20]},
                    (400, 300), 5)
    assert card.size == (400, 300)
    # the pin colour should appear somewhere on the card
    assert (235, 76, 96, 255) in set(card.getdata())
