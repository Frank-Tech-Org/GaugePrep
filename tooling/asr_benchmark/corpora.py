import csv
import hashlib
import json
import tarfile
import urllib.request
from collections.abc import Iterator
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

COMMON_VOICE_BASE = (
    "https://huggingface.co/datasets/fsicoli/common_voice_22_0/resolve/main"
)
# Bytes of an MP3 clip worth testing: roughly 2 to 8 seconds of speech.
CLIP_BYTES = (20_000, 90_000)


@dataclass(frozen=True)
class Clip:
    id: str
    corpus: str
    group: str
    path: str
    reference: str
    seconds: float | None = None


def write_manifest(clips: list[Clip], target: Path) -> None:
    target.write_text(
        "".join(json.dumps(asdict(c), ensure_ascii=False) + "\n" for c in clips),
        encoding="utf-8",
    )


def read_manifest(source: Path) -> list[Clip]:
    return [
        Clip(**json.loads(line))
        for line in source.read_text(encoding="utf-8").splitlines()
        if line
    ]


def keep_clip(name: str, seed: int, share: float) -> bool:
    """Seeded pick that depends only on the clip name, not on stream order."""
    digest = hashlib.sha256(f"{seed}:{name}".encode()).digest()
    return digest[0] / 256 < share


def _open(url: str) -> Iterator[bytes]:
    with urllib.request.urlopen(url, timeout=60) as response:  # noqa: S310  # fixed https dataset URL
        yield from iter(lambda: response.read(1 << 16), b"")


def fetch_common_voice(dest: Path, count: int, seed: int) -> list[Clip]:
    """Stream the French test split and keep a seeded sample of `count` clips."""
    dest.mkdir(parents=True, exist_ok=True)
    tsv = dest / "test.tsv"
    if not tsv.exists():
        tsv.write_bytes(b"".join(_open(f"{COMMON_VOICE_BASE}/transcript/fr/test.tsv")))
    with tsv.open(encoding="utf-8", newline="") as handle:
        sentences = {
            row["path"]: row["sentence"]
            for row in csv.DictReader(handle, delimiter="\t", quoting=csv.QUOTE_NONE)
        }
    clips: list[Clip] = []
    request = urllib.request.Request(f"{COMMON_VOICE_BASE}/audio/fr/test/fr_test_0.tar")
    with urllib.request.urlopen(request, timeout=300) as response:  # noqa: S310  # fixed https dataset URL
        with tarfile.open(fileobj=response, mode="r|") as archive:
            for member in archive:
                name = Path(member.name).name
                if name not in sentences or not (
                    CLIP_BYTES[0] <= member.size <= CLIP_BYTES[1]
                ):
                    continue
                if not keep_clip(name, seed, 0.2):
                    continue
                audio = archive.extractfile(member)
                if audio is None:
                    continue
                target = dest / name
                target.write_bytes(audio.read())
                clips.append(
                    Clip(
                        f"cv-{target.stem[-8:]}",
                        "common-voice-fr",
                        "scripted",
                        str(target),
                        sentences[name],
                    )
                )
                if len(clips) == count:
                    break
    return clips


def speaker_country(filename: str) -> str:
    """Group from an OpenSLR 57 file name such as `cameroon_m_099_019.wav`.

    Files named `ctell` are the 2003 Yaounde recordings, not CA16.
    """
    stem = filename.removeprefix("afc-")
    if stem.startswith("ctell"):
        return "yaounde"
    for country in ("cameroon", "gabon", "niger"):
        if stem.startswith(country):
            return country
    return "chad-congo" if stem.startswith(("chad", "congo")) else "other"


def _name(row: dict[str, Any]) -> str:
    return Path(row.get("path") or row["audio"]["path"]).name


def extract_parquet_sample(
    parquet: Path, dest: Path, quotas: dict[str, int], seed: int
) -> list[Clip]:
    """Seeded sample per country group from a parquet mirror of OpenSLR 57."""
    import pyarrow.parquet as pq  # type: ignore[import-not-found]  # run-time extra, not a repo dependency

    dest.mkdir(parents=True, exist_ok=True)
    rows = [
        r
        for r in pq.read_table(parquet).to_pylist()
        if r["sentence"].strip() and r["audio"]["bytes"]
    ]
    rows.sort(key=lambda r: hashlib.sha256(f"{seed}:{_name(r)}".encode()).digest())
    taken: dict[str, int] = {}
    clips: list[Clip] = []
    for row in rows:
        name = _name(row)
        group = speaker_country(name)
        if taken.get(group, 0) >= quotas.get(group, 0):
            continue
        taken[group] = taken.get(group, 0) + 1
        target = dest / name
        target.write_bytes(row["audio"]["bytes"])
        clips.append(
            Clip(
                f"slr57-{target.stem}",
                "openslr57",
                group,
                str(target),
                row["sentence"].strip(),
            )
        )
    return clips
