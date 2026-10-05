"""Copia o modelo escolhido e os rótulos para os assets do aplicativo."""

from hashlib import sha256
from pathlib import Path
from shutil import copyfile


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "android" / "app" / "src" / "main" / "assets"


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    for filename in ("go_stop_quantized.tflite", "labels.json"):
        source = ROOT / "models" / filename
        destination = ASSETS / filename
        if not source.is_file():
            raise FileNotFoundError(source)
        copyfile(source, destination)
        if digest(source) != digest(destination):
            raise RuntimeError(f"Cópia diferente do original: {filename}")
        print(f"Copiado {filename}: {destination.stat().st_size} bytes; SHA-256 {digest(destination)}")


if __name__ == "__main__":
    main()
