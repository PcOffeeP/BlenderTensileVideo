#!/usr/bin/env python3
"""Encode the fixed, author-defined independent fracture examples with FFmpeg."""
import argparse
import subprocess
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--kind", choices=("brittle", "ductile"), required=True)
    p.add_argument("--frames", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    if a.output.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {a.output}")
    if a.kind == "brittle":
        required = [a.frames / "brittle_0000.png", a.frames / "brittle_0360.png"]
        inputs = ["-loop", "1", "-framerate", "30", "-t", "12", "-i", str(required[0]),
                  "-loop", "1", "-framerate", "30", "-t", "8", "-i", str(required[1])]
        filters = "[0:v][1:v]concat=n=2:v=1:a=0,format=yuv420p[v]"
    else:
        required = [a.frames / f"ductile_{i:04d}.png" for i in range(391)]
        inputs = ["-framerate", "30", "-start_number", "0", "-i", str(a.frames / "ductile_%04d.png"),
                  "-loop", "1", "-framerate", "30", "-i", str(required[-1])]
        filters = ("[0:v]trim=end_frame=391,setpts=PTS-STARTPTS[a];"
                   "[1:v]trim=end_frame=209,setpts=PTS-STARTPTS[b];"
                   "[a][b]concat=n=2:v=1:a=0,format=yuv420p[v]")
    missing = [str(x) for x in required if not x.is_file()]
    if missing:
        raise SystemExit(f"Missing {len(missing)} input frames; first: {missing[0]}")
    a.output.parent.mkdir(parents=True, exist_ok=True)
    cmd = (["ffmpeg", "-hide_banner", "-loglevel", "warning", "-n"] + inputs
           + ["-filter_complex", filters, "-map", "[v]", "-frames:v", "600", "-r", "30",
              "-c:v", "libx264", "-preset", "fast", "-crf", "0", "-g", "600", "-bf", "0",
              "-sc_threshold", "0", "-movflags", "+faststart", str(a.output)])
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
