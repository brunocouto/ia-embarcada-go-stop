"""Treina e avalia o classificador go/stop com o manifesto da etapa 2.

Uso, na raiz do projeto: python training/train.py
"""

import argparse
from collections import Counter
import csv
import json
import os
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np
import tensorflow as tf

from audio import LABELS, SAMPLES_PER_CLIP, load_audio


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "manifest.csv"
MODELS = ROOT / "models"
RESULTS = ROOT / "results"
SEED = 42


def read_manifest() -> list[dict[str, str]]:
    with MANIFEST.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        raise RuntimeError("Manifesto vazio. Execute training/prepare_dataset.py.")
    if {row["label"] for row in rows} != set(LABELS):
        raise RuntimeError("Os rótulos do manifesto diferem de go/stop.")
    return rows


def load_split(rows: list[dict[str, str]], split: str) -> tuple[np.ndarray, np.ndarray, list[str]]:
    selected = [row for row in rows if row["split"] == split]
    if not selected:
        raise RuntimeError(f"Divisão vazia: {split}")
    audio = np.stack([load_audio(ROOT / row["path"]) for row in selected])
    labels = np.asarray([LABELS.index(row["label"]) for row in selected], dtype=np.int64)
    paths = [row["path"] for row in selected]
    return audio[..., np.newaxis], labels, paths


def build_model() -> tf.keras.Model:
    inputs = tf.keras.Input(shape=(SAMPLES_PER_CLIP, 1), name="audio")
    x = tf.keras.layers.Conv1D(24, 80, strides=16, padding="same", use_bias=False)(inputs)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.ReLU()(x)
    x = tf.keras.layers.MaxPooling1D(2)(x)
    x = tf.keras.layers.Conv1D(48, 9, strides=2, padding="same", use_bias=False)(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.ReLU()(x)
    x = tf.keras.layers.MaxPooling1D(2)(x)
    x = tf.keras.layers.Conv1D(64, 5, strides=2, padding="same", use_bias=False)(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.ReLU()(x)
    x = tf.keras.layers.GlobalAveragePooling1D()(x)
    x = tf.keras.layers.Dense(32, activation="relu")(x)
    outputs = tf.keras.layers.Dense(len(LABELS), activation="softmax", name="scores")(x)
    model = tf.keras.Model(inputs, outputs, name="go_stop_raw_audio")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def save_history(history: tf.keras.callbacks.History) -> None:
    columns = ["epoch", *history.history.keys()]
    with (RESULTS / "training_history.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        for index in range(len(history.history["loss"])):
            writer.writerow([index + 1, *(history.history[key][index] for key in history.history)])


def save_evaluation(model: tf.keras.Model, x_test: np.ndarray, y_test: np.ndarray,
                    test_paths: list[str], history: tf.keras.callbacks.History,
                    epochs_requested: int, batch_size: int) -> None:
    probabilities = model.predict(x_test, batch_size=batch_size, verbose=0)
    predictions = probabilities.argmax(axis=1)
    confusion = np.zeros((len(LABELS), len(LABELS)), dtype=np.int64)
    for true_label, predicted_label in zip(y_test, predictions):
        confusion[true_label, predicted_label] += 1

    errors = []
    for path, true_label, predicted_label, scores in zip(test_paths, y_test, predictions, probabilities):
        if true_label != predicted_label:
            errors.append({
                "path": path,
                "true_label": LABELS[true_label],
                "predicted_label": LABELS[predicted_label],
                "predicted_confidence": round(float(scores[predicted_label]), 6),
            })
    with (RESULTS / "test_errors.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=("path", "true_label", "predicted_label", "predicted_confidence"))
        writer.writeheader()
        writer.writerows(errors)

    accuracy = float(np.mean(predictions == y_test))
    per_class = {}
    for index, label in enumerate(LABELS):
        true_total = int(confusion[index].sum())
        predicted_total = int(confusion[:, index].sum())
        correct = int(confusion[index, index])
        per_class[label] = {
            "test_examples": true_total,
            "correct": correct,
            "recall": correct / true_total if true_total else None,
            "precision": correct / predicted_total if predicted_total else None,
        }
    report = {
        "model_file": "models/go_stop_model.keras",
        "model_bytes": (MODELS / "go_stop_model.keras").stat().st_size,
        "model_parameters": model.count_params(),
        "input_shape": [1, SAMPLES_PER_CLIP, 1],
        "labels_in_order": list(LABELS),
        "test_examples": len(y_test),
        "accuracy": accuracy,
        "error_count": len(errors),
        "confusion_matrix_rows_true_columns_predicted": confusion.tolist(),
        "per_class": per_class,
        "seed": SEED,
        "epochs_requested": epochs_requested,
        "epochs_ran": len(history.history["loss"]),
        "selected_epoch_by_validation_loss": int(np.argmin(history.history["val_loss"])) + 1,
        "validation_accuracy_at_selected_epoch": float(history.history["val_accuracy"][int(np.argmin(history.history["val_loss"]))]),
        "best_validation_accuracy": max(history.history["val_accuracy"]),
        "batch_size": batch_size,
        "tensorflow_version": tf.__version__,
        "numpy_version": np.__version__,
    }
    (RESULTS / "evaluation.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Teste: acurácia={accuracy:.4f}; erros={len(errors)}/{len(y_test)}")
    print("Matriz de confusão (linhas reais, colunas previstas; go, stop):")
    print(confusion)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=25)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()
    if args.epochs < 1 or args.batch_size < 1:
        parser.error("epochs e batch-size devem ser positivos")

    tf.keras.utils.set_random_seed(SEED)
    rows = read_manifest()
    counts = Counter((row["split"], row["label"]) for row in rows)
    print(f"Manifesto: {len(rows)} arquivos; divisões: {dict(counts)}")
    x_train, y_train, _ = load_split(rows, "train")
    x_val, y_val, _ = load_split(rows, "validation")
    x_test, y_test, test_paths = load_split(rows, "test")
    print(f"Entradas: treino={x_train.shape}, validação={x_val.shape}, teste={x_test.shape}")

    model = build_model()
    model.summary()
    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=5, restore_best_weights=True
        )
    ]
    history = model.fit(
        x_train, y_train,
        validation_data=(x_val, y_val),
        epochs=args.epochs,
        batch_size=args.batch_size,
        callbacks=callbacks,
        verbose=2,
    )

    MODELS.mkdir(exist_ok=True)
    RESULTS.mkdir(exist_ok=True)
    model.save(MODELS / "go_stop_model.keras")
    (MODELS / "labels.json").write_text(
        json.dumps({"labels_in_order": list(LABELS)}, indent=2) + "\n", encoding="utf-8"
    )
    (RESULTS / "training_config.json").write_text(
        json.dumps({
            "manifest": "data/manifest.csv",
            "audio_spec": "data/audio_spec.json",
            "seed": SEED,
            "epochs_requested": args.epochs,
            "batch_size": args.batch_size,
            "model": "1D CNN sobre áudio PCM normalizado",
            "optimizer": "Adam, learning_rate=0.001",
            "early_stopping": "val_loss, patience=5, restore_best_weights=True",
            "split_policy": "por locutor, fixada na etapa 2",
        }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    save_history(history)
    save_evaluation(model, x_test, y_test, test_paths, history, args.epochs, args.batch_size)


if __name__ == "__main__":
    main()
