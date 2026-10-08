#!/usr/bin/env python3
"""Download an audio file (local path, direct URL, or Google Drive share link)
and transcribe it with faster-whisper (free, runs locally, MIT license).

Outputs, in --out-dir:
  <name>.raw.txt   plain transcript, one segment per line
  <name>.srt       timestamped subtitles
  <name>.json      segments with start/end/text and detected language
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

DRIVE_RE = re.compile(r"drive\.google\.com|docs\.google\.com")


def download(src: str, dest_dir: Path) -> Path:
    if os.path.exists(src):
        return Path(src)
    dest_dir.mkdir(parents=True, exist_ok=True)
    if DRIVE_RE.search(src):
        import gdown

        out = gdown.download(src, output=str(dest_dir) + os.sep, fuzzy=True, quiet=False)
        if not out:
            sys.exit("Google Drive download failed: is the file shared as 'Anyone with the link'?")
        return Path(out)
    if "dropbox.com" in src:
        src = re.sub(r"[?&]dl=0", "", src)
        src += ("&" if "?" in src else "?") + "dl=1"
    name = Path(urllib.parse.urlparse(src).path).name or "audio"
    out = dest_dir / name
    print(f"Downloading {src} -> {out}", file=sys.stderr)
    urllib.request.urlretrieve(src, out)
    return out


def to_wav(audio: Path) -> Path:
    """Decode with ffmpeg to 16 kHz mono WAV. PyAV silently returns 0 s of audio
    for some phone-recorded m4a files that ffmpeg decodes fine."""
    if not shutil.which("ffmpeg") or audio.suffix.lower() == ".wav":
        return audio
    wav = audio.with_suffix(".16k.wav")
    if not wav.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(audio), "-ac", "1", "-ar", "16000", str(wav)],
                       check=False)
    return wav if wav.exists() and wav.stat().st_size > 44 else audio


def ts(sec: float) -> str:
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("source", help="local audio path, direct URL, or Google Drive share link")
    p.add_argument("--model", default=os.environ.get("WHISPER_MODEL", "large-v3-turbo"),
                   help="tiny/base/small/medium/large-v3/large-v3-turbo (default: large-v3-turbo)")
    p.add_argument("--language", default=None, help="e.g. zh, en; omit to auto-detect")
    p.add_argument("--keep-simplified", action="store_true",
                   help="don't convert Chinese output to Traditional (Taiwan) characters")
    p.add_argument("--prompt", default=None,
                   help="initial prompt: names/jargon that help recognition")
    p.add_argument("--out-dir", default="output")
    p.add_argument("--download-dir", default="downloads")
    a = p.parse_args()

    audio = download(a.source, Path(a.download_dir))
    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = audio.stem

    from faster_whisper import WhisperModel

    print(f"Loading model {a.model} ...", file=sys.stderr)
    model = WhisperModel(a.model, device="auto", compute_type="int8")
    segments, info = model.transcribe(
        str(to_wav(audio)), language=a.language, initial_prompt=a.prompt,
        vad_filter=True, beam_size=5,
    )
    print(f"Detected language: {info.language} ({info.language_probability:.2f}), "
          f"duration {info.duration:.0f}s", file=sys.stderr)
    if info.duration == 0:
        sys.exit(f"Could not decode any audio from {audio}")

    convert = None
    if info.language == "zh" and not a.keep_simplified:
        import opencc

        convert = opencc.OpenCC("s2twp").convert

    segs = []
    for s in segments:
        text = s.text.strip()
        if convert:
            text = convert(text)
        segs.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": text})
        print(f"[{ts(s.start)}] {text}", file=sys.stderr)

    (out_dir / f"{stem}.raw.txt").write_text("\n".join(x["text"] for x in segs) + "\n", encoding="utf-8")
    (out_dir / f"{stem}.srt").write_text(
        "".join(f"{i}\n{ts(x['start'])} --> {ts(x['end'])}\n{x['text']}\n\n" for i, x in enumerate(segs, 1)),
        encoding="utf-8")
    (out_dir / f"{stem}.json").write_text(json.dumps(
        {"source": a.source, "language": info.language, "duration": info.duration, "segments": segs},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(out_dir / f"{stem}.raw.txt")


if __name__ == "__main__":
    main()
