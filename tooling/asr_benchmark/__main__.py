# Usage: python -m asr_benchmark fetch-cv|fetch-openslr|synth|run|stream
import argparse
import asyncio
import json
import os
import sys
import wave
from pathlib import Path

from asr_benchmark.corpora import (
    extract_parquet_sample,
    fetch_common_voice,
    read_manifest,
    write_manifest,
)
from asr_benchmark.engines import (
    ALLOWANCE_MINUTES,
    MODELS,
    PRICED,
    available_engines,
)
from asr_benchmark.guard import UNKNOWN_CLIP_MINUTES, Guard
from asr_benchmark.planted import PLANTED_CLIPS
from asr_benchmark.runner import (
    choose_winner,
    evaluate,
    planted_as_clips,
    save,
    table,
)
from asr_benchmark.streaming import STREAMING, stream_clip, summarise

SEED = 15
# Every Cameroon clip in the mirror's test split, then seeded samples of the others.
OPENSLR_QUOTAS = {"cameroon": 47, "gabon": 20, "chad-congo": 16, "yaounde": 60}
_UNREADABLE = (wave.Error, EOFError)


def wav_seconds(path: Path) -> float | None:
    try:
        with wave.open(str(path)) as handle:
            return float(handle.getnframes() / handle.getframerate())
    except _UNREADABLE:
        return None


def synth(voice_path: Path, directory: Path) -> None:
    from piper import PiperVoice  # type: ignore[import-not-found]  # run-time extra, not a repo dependency

    directory.mkdir(parents=True, exist_ok=True)
    voice = PiperVoice.load(str(voice_path))
    for clip in PLANTED_CLIPS:
        with wave.open(str(directory / f"{clip.id}.wav"), "wb") as handle:
            voice.synthesize_wav(clip.spoken, handle)


def run(
    manifests: list[Path],
    planted_dir: Path,
    out: Path,
    whisper_dir: Path | None,
    limit: int | None = None,
) -> int:
    clips = [c for m in manifests for c in read_manifest(m)[:limit]]
    clips += planted_as_clips(planted_dir)[:limit]
    durations = {
        c.id: d for c in clips if (d := c.seconds or wav_seconds(Path(c.path)))
    }
    engines, skipped = available_engines(whisper_dir, os.environ)
    if only := os.environ.get("ASR_ONLY"):
        engines = [e for e in engines if e.name == only]
    minutes = {
        c.path: durations.get(c.id, UNKNOWN_CLIP_MINUTES * 60) / 60 for c in clips
    }
    guard = Guard(out / "cache", ALLOWANCE_MINUTES, minutes)
    engines = [
        guard.wrap(e, MODELS[e.name] + os.environ.get("ASR_VARIANT", ""))
        if e.key_env
        else e
        for e in engines
    ]
    for line in skipped:
        print(line)
    results = []
    hypotheses = {}
    for engine in engines:
        print(f"running {engine.name} on {len(clips)} clips")
        result, hyp = evaluate(engine, clips, durations)
        results.append(result)
        hypotheses[engine.name] = hyp
        if engine.key_env:
            print(guard.usage_line(engine.name))
        if result.stopped:
            print(f"STOPPED {result.stopped}", file=sys.stderr)
    if not results:
        print("no engine could run", file=sys.stderr)
        return 1
    save(results, hypotheses, out)
    print(table(results))
    winner = choose_winner(results) or "none of the engines that ran"
    print(f"winner by the selection rule: {winner}")
    for r in results:
        for clip_id, reason in r.missing.items():
            print(f"{r.name} missing {clip_id}: {reason}")
    return 0


def stream(manifests: list[Path], count: int, out: Path) -> int:
    clips = [c for m in manifests for c in read_manifest(m)][:count]
    report: dict[str, dict[str, float | None]] = {}
    for name in STREAMING:
        key = PRICED[name][0]
        if not key or not os.environ.get(key):
            print(f"skipped {name}: {key} is not set")
            continue
        timings = [asyncio.run(stream_clip(name, Path(c.path))) for c in clips]
        report[name] = summarise(timings)
        print(name, report[name])
    if not report:
        print("no streaming engine could run", file=sys.stderr)
        return 1
    out.write_text(json.dumps(report, indent=2))
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="asr_benchmark")
    sub = parser.add_subparsers(dest="command", required=True)
    cv = sub.add_parser("fetch-cv")
    cv.add_argument("dest", type=Path)
    cv.add_argument("--count", type=int, default=60)
    slr = sub.add_parser("fetch-openslr")
    slr.add_argument("parquet", type=Path)
    slr.add_argument("dest", type=Path)
    tts = sub.add_parser("synth")
    tts.add_argument("voice", type=Path)
    tts.add_argument("dest", type=Path)
    go = sub.add_parser("run")
    go.add_argument("--manifest", type=Path, action="append", default=[])
    go.add_argument("--planted-dir", type=Path, required=True)
    go.add_argument("--out", type=Path, required=True)
    go.add_argument("--whisper-dir", type=Path)
    go.add_argument("--limit", type=int, help="clips per manifest and planted")
    live = sub.add_parser("stream")
    live.add_argument("--manifest", type=Path, action="append", default=[])
    live.add_argument("--count", type=int, default=20)
    live.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "fetch-cv":
        write_manifest(
            fetch_common_voice(args.dest, args.count, SEED),
            args.dest / "manifest.jsonl",
        )
    elif args.command == "fetch-openslr":
        clips = extract_parquet_sample(args.parquet, args.dest, OPENSLR_QUOTAS, SEED)
        write_manifest(clips, args.dest / "manifest.jsonl")
    elif args.command == "synth":
        synth(args.voice, args.dest)
    elif args.command == "stream":
        return stream(args.manifest, args.count, args.out)
    else:
        return run(
            args.manifest, args.planted_dir, args.out, args.whisper_dir, args.limit
        )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
