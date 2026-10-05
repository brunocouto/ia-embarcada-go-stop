"""Prepara duas amostras reservadas para verificar o APK debug no emulador."""

from hashlib import sha256
from pathlib import Path
import wave


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "android/app/src/debug/assets"
SOURCES = {
    "go": "data/raw/mini_speech_commands/go/0eb48e10_nohash_0.wav",
    "stop": "data/raw/mini_speech_commands/stop/023a61ad_nohash_0.wav",
}


def main() -> None:
    DESTINATION.mkdir(parents=True, exist_ok=True)
    for label, relative_path in SOURCES.items():
        source = ROOT / relative_path
        with wave.open(str(source), "rb") as audio:
            if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) != (1, 2, 16000):
                raise ValueError(f"Formato inesperado: {source}")
            samples = audio.readframes(16000)
        samples = samples.ljust(32000, b"\0")
        if len(samples) != 32000:
            raise ValueError(f"Amostra longa demais: {source}")
        destination = DESTINATION / f"sample_{label}.pcm"
        destination.write_bytes(samples)
        print(f"{label}: {relative_path} -> {destination.relative_to(ROOT)}; SHA-256 {sha256(samples).hexdigest()}")


if __name__ == "__main__":
    main()
