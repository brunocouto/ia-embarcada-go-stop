"""Baixa e prepara as classes go/stop do Mini Speech Commands oficial.

Uso: python training/prepare_dataset.py
Produz: data/manifest.csv e data/dataset_summary.json.
"""

from collections import Counter
import csv
from hashlib import sha256
import json
from pathlib import Path
import random
import re
from urllib.request import urlopen
import wave
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ARCHIVE = DATA / "raw" / "mini_speech_commands.zip"
EXTRACTED = DATA / "raw" / "mini_speech_commands"
MANIFEST = DATA / "manifest.csv"
SUMMARY = DATA / "dataset_summary.json"
URL = "https://storage.googleapis.com/download.tensorflow.org/data/mini_speech_commands.zip"
EXPECTED_ARCHIVE_BYTES = 182_082_353
LABELS = ("go", "stop")
SEED = 42
FILENAME = re.compile(r"^(?P<speaker>.+)_nohash_\d+\.wav$", re.IGNORECASE)


def file_hash(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download() -> None:
    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    if ARCHIVE.exists() and ARCHIVE.stat().st_size == EXPECTED_ARCHIVE_BYTES:
        return
    part = ARCHIVE.with_suffix(".zip.part")
    if part.exists():
        part.unlink()
    with urlopen(URL, timeout=60) as response, part.open("wb") as output:
        for chunk in iter(lambda: response.read(1024 * 1024), b""):
            output.write(chunk)
    if part.stat().st_size != EXPECTED_ARCHIVE_BYTES:
        raise RuntimeError(f"Tamanho inesperado do download: {part.stat().st_size} bytes")
    part.replace(ARCHIVE)


def extract_selected() -> None:
    with ZipFile(ARCHIVE) as archive:
        members = []
        for item in archive.infolist():
            parts = Path(item.filename).parts
            if item.is_dir() or len(parts) < 2:
                continue
            label, filename = parts[-2:]
            if label in LABELS and filename.lower().endswith(".wav") and not filename.startswith("._"):
                members.append((item, label, filename))
        if not members:
            raise RuntimeError("As classes go/stop não foram encontradas no arquivo oficial.")
        for item, label, filename in members:
            if not FILENAME.fullmatch(filename):
                raise ValueError(f"Nome de arquivo inesperado: {filename}")
            destination = EXTRACTED / label / filename
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists() and destination.stat().st_size == item.file_size:
                continue
            with archive.open(item) as source, destination.open("wb") as output:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    output.write(chunk)
    # Uma execução anterior pode ter extraído os metadados AppleDouble.
    # Remover apenas esses arquivos gerados, dentro das duas classes selecionadas.
    for label in LABELS:
        for sidecar in (EXTRACTED / label).glob("._*.wav"):
            if sidecar.is_file():
                sidecar.unlink()


def inspect_audio(path: Path) -> tuple[int, int]:
    with wave.open(str(path), "rb") as wav:
        if wav.getnchannels() != 1 or wav.getframerate() != 16_000:
            raise ValueError(f"Canais ou frequência inesperados: {path}")
        if wav.getsampwidth() != 2 or wav.getcomptype() != "NONE":
            raise ValueError(f"Formato inesperado: {path}")
        return wav.getnframes(), wav.getframerate()


def build_manifest() -> list[dict[str, str | int]]:
    samples = []
    for label in LABELS:
        for path in sorted((EXTRACTED / label).glob("*.wav")):
            # O ZIP oficial também contém arquivos AppleDouble ._*.wav;
            # eles são metadados do macOS, não gravações de áudio.
            if path.name.startswith("._"):
                continue
            match = FILENAME.fullmatch(path.name)
            if not match:
                raise ValueError(f"Nome de arquivo inesperado: {path.name}")
            frames, sample_rate = inspect_audio(path)
            if not 0 < frames <= 16_000:
                raise ValueError(f"Duração inesperada: {path} ({frames} amostras)")
            samples.append({
                "path": path.relative_to(ROOT).as_posix(),
                "label": label,
                "speaker_id": match.group("speaker"),
                "frames": frames,
                "sample_rate_hz": sample_rate,
            })
    if not samples or {row["label"] for row in samples} != set(LABELS):
        raise RuntimeError("O dataset precisa conter ambas as classes.")

    speakers = sorted({str(row["speaker_id"]) for row in samples})
    random.Random(SEED).shuffle(speakers)
    train_end = int(len(speakers) * 0.8)
    val_end = train_end + int(len(speakers) * 0.1)
    split_by_speaker = {
        speaker: ("train" if index < train_end else "validation" if index < val_end else "test")
        for index, speaker in enumerate(speakers)
    }
    for row in samples:
        row["split"] = split_by_speaker[str(row["speaker_id"])]
    counts = Counter((str(row["split"]), str(row["label"])) for row in samples)
    if any(counts[(split, label)] == 0 for split in ("train", "validation", "test") for label in LABELS):
        raise RuntimeError("Alguma divisão ficou sem exemplos de uma classe.")
    return samples


def save_outputs(samples: list[dict[str, str | int]]) -> None:
    with MANIFEST.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=("path", "label", "speaker_id", "frames", "sample_rate_hz", "split"),
        )
        writer.writeheader()
        writer.writerows(samples)

    counts = Counter((str(row["split"]), str(row["label"])) for row in samples)
    speakers = {str(row["speaker_id"]) for row in samples}
    summary = {
        "source_url": URL,
        "source_description": "Mini Speech Commands, conforme tutorial oficial do TensorFlow",
        "license": "CC BY, conforme tutorial oficial do TensorFlow; verificar atribuição antes da publicação dos áudios",
        "archive_bytes": ARCHIVE.stat().st_size,
        "archive_sha256": file_hash(ARCHIVE),
        "selected_labels": list(LABELS),
        "split_seed": SEED,
        "split_method": "80/10/10 por speaker_id; mesmo locutor só em uma divisão",
        "speaker_count": len(speakers),
        "sample_count": len(samples),
        "counts": {
            split: {label: counts[(split, label)] for label in LABELS}
            for split in ("train", "validation", "test")
        },
        "audio_spec_file": "data/audio_spec.json",
    }
    SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    download()
    extract_selected()
    samples = build_manifest()
    save_outputs(samples)
    counts = Counter((str(row["split"]), str(row["label"])) for row in samples)
    print(f"Preparados {len(samples)} arquivos de {len({row['speaker_id'] for row in samples})} locutores.")
    for split in ("train", "validation", "test"):
        print(f"{split}: go={counts[(split, 'go')]}, stop={counts[(split, 'stop')]}")
    print(f"Manifesto: {MANIFEST}")
    print(f"Resumo: {SUMMARY}")


if __name__ == "__main__":
    main()
