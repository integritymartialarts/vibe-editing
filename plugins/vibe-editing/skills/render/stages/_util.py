"""Shared helpers for render stages."""
from __future__ import annotations

import json, subprocess
from pathlib import Path


def _has_videotoolbox() -> bool:
    global _VT
    try:
        return _VT
    except NameError:
        pass
    try:
        out = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"],
                             capture_output=True, text=True, timeout=15).stdout
        _VT = "h264_videotoolbox" in out
    except Exception:
        _VT = False
    return _VT


def _portable_encoder(cmd):
    """Stages hard-code Apple's h264_videotoolbox. Where it doesn't exist (Windows/Linux), swap in
    libx264 at the same bitrate (`-preset fast`), so the same commands run unchanged on any machine."""
    if "h264_videotoolbox" not in cmd or _has_videotoolbox():
        return cmd
    out = []
    for c in cmd:
        if c == "h264_videotoolbox":
            out += ["libx264", "-preset", "fast"]
        else:
            out.append(c)
    return out


def run(cmd, **kw):
    cmd = _portable_encoder([str(c) for c in cmd])
    print("  $", " ".join(cmd[:8]) + (" ..." if len(cmd) > 8 else ""), flush=True)
    return subprocess.run(cmd, check=True, **kw)


def resolve_path(p: str | Path, project: Path) -> Path:
    """Resolve a config path. Absolute -> as-is. Relative -> under project root."""
    p = Path(p)
    return p if p.is_absolute() else (project / p)


def ffprobe_duration(p: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(p)], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def ffprobe_fps(p: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                          "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", str(p)],
                         capture_output=True, text=True, check=True)
    num, den = out.stdout.strip().split("/")
    return float(num) / float(den)
