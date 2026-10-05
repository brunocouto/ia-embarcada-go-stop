"""Preparação de áudio compartilhada pelo treino e pela avaliação em Python."""

from pathlib import Path
import wave

import numpy as np


SAMPLE_RATE = 16_000
SAMPLES_PER_CLIP = 16_000
LABELS = ("go", "stop")


def load_audio(path: str | Path) -> np.ndarray:
    """Lê WAV mono PCM16 e devolve exatamente 16000 amostras float32.

    A implementação Android deverá reproduzir esta sequência: PCM16 mono a
    16 kHz, normalização por 32768, corte no início ou zeros ao final.
    """
    with wave.open(str(path), "rb") as wav:
        if wav.getnchannels() != 1:
            raise ValueError(f"Áudio não é mono: {path}")
        if wav.getframerate() != SAMPLE_RATE:
            raise ValueError(f"Taxa diferente de {SAMPLE_RATE} Hz: {path}")
        if wav.getsampwidth() != 2 or wav.getcomptype() != "NONE":
            raise ValueError(f"Áudio não é PCM16 sem compressão: {path}")
        raw = wav.readframes(SAMPLES_PER_CLIP)

    samples = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    if samples.size < SAMPLES_PER_CLIP:
        samples = np.pad(samples, (0, SAMPLES_PER_CLIP - samples.size))
    return samples
