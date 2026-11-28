"""Command line for the series pipeline.

    python -m studio validate ep001
    python -m studio prompts ep001
    python -m studio keyframes ep001 [--provider huggingface] [--only s020] [--force]
    python -m studio animate ep001   [--provider wan]         [--only s020] [--force]
    python -m studio compose ep001   # AI backgrounds + your stickers + logo -> scenes
    python -m studio motion ep001    # camera moves + living stickers + map (no AI video)
    python -m studio voice ep001     # dialogue -> speech (Kokoro, offline)
    python -m studio assemble ep001
    python -m studio render ep001       # keyframes + animate + assemble
    python -m studio new-episode ep002 "Too Many Ramps"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import assemble, prompts
from .project import Project
from .providers import get_animate_provider, get_keyframe_provider


def _ep_out(project: Project, ep: str) -> Path:
    return project.output_dir / ep


def _selected(project: Project, args) -> list[dict]:
    items = prompts.build_all(project, args.episode)
    if getattr(args, "only", None):
        wanted = set(args.only)
        items = [i for i in items if i["id"] in wanted]
    return items


def _require_valid(project: Project, ep: str) -> None:
    errors = project.validate(ep)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        sys.exit(1)


def cmd_validate(project: Project, args) -> int:
    eps = [args.episode] if args.episode else project.episode_ids()
    bad = 0
    for ep in eps:
        errors = project.validate(ep)
        print(f"{ep}: {'OK' if not errors else f'{len(errors)} problem(s)'}")
        for e in errors:
            print(f"  - {e}")
        bad += bool(errors)
    return 1 if bad else 0


def cmd_prompts(project: Project, args) -> int:
    _require_valid(project, args.episode)
    items = _selected(project, args)
    out = _ep_out(project, args.episode) / "prompts.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    for i in items:
        print(f"[{i['id']}] {i['keyframe_prompt']}\n      motion: {i['motion_prompt']}\n")
    print(f"wrote {out.relative_to(project.root)}")
    return 0


def cmd_keyframes(project: Project, args) -> int:
    _require_valid(project, args.episode)
    style = project.style
    cfg = style.get("keyframe", {})
    name = args.provider or cfg.get("provider", "placeholder")
    w, h = project.resolution(args.episode)
    opts = {k: v for k, v in cfg.items() if k != "provider"} if name == cfg.get("provider") else {}
    prov = get_keyframe_provider(name, width=w, height=h, **opts)
    for i in _selected(project, args):
        out = _ep_out(project, args.episode) / "keyframes" / f"{i['id']}.png"
        if out.exists() and not args.force:
            print(f"[{i['id']}] keyframe exists, skipping (use --force to redo)")
            continue
        print(f"[{i['id']}] keyframe via {name} ...", flush=True)
        prov.generate(i["keyframe_prompt"], i["negative_prompt"], out, label=i["id"])
    return 0


def cmd_animate(project: Project, args) -> int:
    _require_valid(project, args.episode)
    style = project.style
    cfg = style.get("animate", {})
    name = args.provider or cfg.get("provider", "placeholder")
    opts = {k: v for k, v in cfg.items() if k != "provider"} if name == cfg.get("provider") else {}
    prov = get_animate_provider(name, fps=style.get("fps", 16), **opts)
    base = _ep_out(project, args.episode)
    for i in _selected(project, args):
        img = base / "keyframes" / f"{i['id']}.png"
        out = base / "clips" / f"{i['id']}.mp4"
        if not img.exists():
            print(f"[{i['id']}] no keyframe yet; run `keyframes` first", file=sys.stderr)
            return 1
        if out.exists() and not args.force:
            print(f"[{i['id']}] clip exists, skipping (use --force to redo)")
            continue
        print(f"[{i['id']}] animating via {name} ...", flush=True)
        prov.animate(img, i["motion_prompt"], i["negative_prompt"], i["duration"], out,
                     label=i["id"])
    return 0


def cmd_assemble(project: Project, args) -> int:
    _require_valid(project, args.episode)
    ep = project.episode(args.episode)
    base = _ep_out(project, args.episode)
    clips, subs, starts, t = [], [], [], 0.0
    for s in ep.shots:
        clip = base / "clips" / f"{s.id}.mp4"
        if not clip.exists():
            print(f"missing clip {clip.relative_to(project.root)}; run `animate` first",
                  file=sys.stderr)
            return 1
        d = assemble.clip_duration(clip)
        lines = s.dialogue
        for n, line in enumerate(lines):
            seg = d / len(lines)
            name = project.characters[line["character"]].get("name", line["character"])
            subs.append((t + n * seg, t + (n + 1) * seg, name, line["line"]))
        clips.append(clip)
        starts.append((s.id, t))
        t += d
    w, h = project.resolution(args.episode)
    video = assemble.concat(clips, base / f"{ep.id}.mp4", project.fps(args.episode), (w, h))
    dialogue_wavs = [(base / "audio" / f"{sid}.wav", start) for sid, start in starts]
    dialogue_wavs = [(p, start) for p, start in dialogue_wavs if p.exists()]
    if dialogue_wavs:
        track = assemble.mix_dialogue(dialogue_wavs, t, base / "audio" / "_episode_mix.wav")
        assemble.add_audio(video, track)
        print(f"mixed dialogue from {len(dialogue_wavs)} shot(s) into the episode")
    srt = assemble.write_srt(subs, base / f"{ep.id}.srt")
    print(f"wrote {video.relative_to(project.root)} ({t:.1f}s, {len(clips)} shots)")
    print(f"wrote {srt.relative_to(project.root)} ({len(subs)} subtitle lines)")
    return 0


def cmd_voice(project: Project, args) -> int:
    """Speak each shot's dialogue into output/<ep>/audio/<shot>.wav, plus a full read-through."""
    from . import voice

    _require_valid(project, args.episode)
    ep = project.episode(args.episode)
    base = _ep_out(project, args.episode)
    model_dir = project.root / project.style.get("voice", {}).get("model_dir", "models/kokoro")
    tts = voice.KokoroVoice(model_dir)
    wanted = set(args.only or [s.id for s in ep.shots])
    readthrough = []
    for s in ep.shots:
        if s.id not in wanted or not s.dialogue:
            continue
        parts = []
        for line in s.dialogue:
            ch = project.characters[line["character"]]
            parts.append(tts.speak(line["line"], ch.get("tts_voice", "af_heart"),
                                   float(ch.get("tts_speed", 1.0))))
            parts.append(voice.silence(voice.GAP_BETWEEN_LINES))
        audio = voice.np.concatenate(parts[:-1])
        out = voice.write_wav(audio, base / "audio" / f"{s.id}.wav")
        secs = len(audio) / voice.SAMPLE_RATE
        flag = "  <-- longer than the shot; trim the line or lengthen the shot" \
            if secs > s.duration else ""
        print(f"[{s.id}] {secs:4.1f}s of {s.duration:g}s  {out.relative_to(project.root)}{flag}")
        readthrough += [audio, voice.silence(0.5)]
    if readthrough:
        rt = voice.write_wav(voice.np.concatenate(readthrough), base / "voiceover.wav")
        print(f"wrote {rt.relative_to(project.root)} (full read-through)")
    return 0


def cmd_compose(project: Project, args) -> int:
    """Background + brand sticker + logo -> scenes/<shot>.png (full size) and keyframes/."""
    from . import compose

    _require_valid(project, args.episode)
    ep = project.episode(args.episode)
    base = _ep_out(project, args.episode)
    brand = project.style.get("brand", {})
    logo = project.root / brand["logo"] if brand.get("logo") else None
    w, h = project.resolution(args.episode)
    full = tuple(brand.get("scene_size", [1080, 1920] if h > w else [1920, 1080]))
    wanted = set(args.only or [s.id for s in ep.shots])
    for s in ep.shots:
        if s.id not in wanted:
            continue
        bg = next((p for p in (base / "backgrounds" / f"{s.id}{e}" for e in (".png", ".jpg"))
                   if p.exists()), None)
        if bg is None:
            print(f"[{s.id}] no background in {(base / 'backgrounds').relative_to(project.root)}/",
                  file=sys.stderr)
            return 1
        x = s.extra
        sticker = project.root / "brand" / "stickers" / f"{x['sticker']}.png" \
            if x.get("sticker") else None
        out = compose.compose_scene(
            bg, base / "scenes" / f"{s.id}.png", full, sticker=sticker,
            side=x.get("sticker_side", "left"), scale=float(x.get("sticker_scale", 0.62)),
            crop=x.get("sticker_crop"), focus_x=float(x.get("focus_x", 0.5)),
            logo=logo, logo_scale=float(x.get("logo_scale", brand.get("logo_scale", 0.2))),
            title=x.get("title"))
        from PIL import Image
        Image.open(out).resize((w, h), Image.LANCZOS).save(base / "keyframes" / f"{s.id}.png")
        print(f"[{s.id}] {out.relative_to(project.root)}")
    return 0


def _motion_job(job: dict) -> str:
    from . import motion
    motion.render_shot(**job)
    return job["out_path"].name


def cmd_motion(project: Project, args) -> int:
    """Animate composed scenes: camera move + living sticker + map card -> clips/<shot>.mp4."""
    from multiprocessing import Pool

    _require_valid(project, args.episode)
    ep = project.episode(args.episode)
    base = _ep_out(project, args.episode)
    brand = project.style.get("brand", {})
    logo = project.root / brand["logo"] if brand.get("logo") else None
    size, fps = project.resolution(args.episode), project.fps(args.episode)
    wanted = set(args.only or [s.id for s in ep.shots])
    jobs = []
    for s in ep.shots:
        if s.id not in wanted:
            continue
        bg = next((p for p in (base / "backgrounds" / f"{s.id}{e}" for e in (".png", ".jpg"))
                   if p.exists()), None)
        if bg is None:
            print(f"[{s.id}] no background image", file=sys.stderr)
            return 1
        x = s.extra
        jobs.append(dict(
            bg_path=bg, out_path=base / "clips" / f"{s.id}.mp4", size=size, fps=fps,
            duration=s.duration,
            sticker=project.root / "brand" / "stickers" / f"{x['sticker']}.png"
            if x.get("sticker") else None,
            side=x.get("sticker_side", "left"), scale=float(x.get("sticker_scale", 0.62)),
            crop=x.get("sticker_crop"), logo=logo,
            logo_scale=float(x.get("logo_scale", brand.get("logo_scale", 0.2))),
            title=x.get("title"),
            camera={"focus_x": x.get("focus_x", 0.5), **(x.get("camera") or {})},
            map_spec=x.get("map")))
    with Pool(min(4, len(jobs)) or 1) as pool:
        for name in pool.imap_unordered(_motion_job, jobs):
            print(f"animated {name}", flush=True)
    return 0


def cmd_render(project: Project, args) -> int:
    args.provider = None
    for step in (cmd_keyframes, cmd_animate, cmd_assemble):
        if step(project, args):
            return 1
    return 0


def cmd_new_episode(project: Project, args) -> int:
    path = project.root / "episodes" / args.episode
    if path.exists():
        print(f"{path.relative_to(project.root)} already exists", file=sys.stderr)
        return 1
    path.mkdir(parents=True)
    (path / "script.md").write_text(f"# {args.episode.upper()} — {args.title}\n\n", "utf-8")
    (path / "shots.yaml").write_text(
        f"episode: {args.episode}\ntitle: {args.title}\n\nshots:\n"
        "  - id: s010\n    location: lane\n    characters: []\n"
        "    framing: wide establishing shot\n    action: describe what we see\n"
        "    motion: describe what moves\n    duration: 4\n",
        "utf-8",
    )
    print(f"created {path.relative_to(project.root)}/ (script.md, shots.yaml)")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="studio", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", default=".", help="project root (default: current dir)")
    sub = p.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="check shots against characters/locations")
    v.add_argument("episode", nargs="?")
    v.set_defaults(fn=cmd_validate)

    for name, fn, has_provider in [
        ("prompts", cmd_prompts, False),
        ("keyframes", cmd_keyframes, True),
        ("animate", cmd_animate, True),
        ("render", cmd_render, False),
        ("voice", cmd_voice, False),
        ("compose", cmd_compose, False),
        ("motion", cmd_motion, False),
    ]:
        sp = sub.add_parser(name)
        sp.add_argument("episode")
        sp.add_argument("--only", nargs="+", metavar="SHOT", help="limit to these shot ids")
        if name != "prompts":
            sp.add_argument("--force", action="store_true", help="regenerate existing files")
        if has_provider:
            sp.add_argument("--provider", help="override provider from style.yaml")
        sp.set_defaults(fn=fn)

    a = sub.add_parser("assemble", help="join clips into the episode + subtitles")
    a.add_argument("episode")
    a.set_defaults(fn=cmd_assemble)

    n = sub.add_parser("new-episode", help="scaffold a new episode folder")
    n.add_argument("episode")
    n.add_argument("title")
    n.set_defaults(fn=cmd_new_episode)

    args = p.parse_args(argv)
    return args.fn(Project(args.root), args)


if __name__ == "__main__":
    sys.exit(main())
