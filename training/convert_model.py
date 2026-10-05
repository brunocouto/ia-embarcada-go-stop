"""Converte, quantiza e compara o modelo no mesmo teste da etapa 3.

Uso, na raiz do projeto: python training/convert_model.py
"""

import csv
import json
import os
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np
import tensorflow as tf

from audio import LABELS, SAMPLES_PER_CLIP, load_audio


ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"
RESULTS = ROOT / "results"
KERAS_MODEL = MODELS / "go_stop_model.keras"
FLOAT_MODEL = MODELS / "go_stop_float32.tflite"
QUANT_MODEL = MODELS / "go_stop_quantized.tflite"


def load_test() -> tuple[np.ndarray, np.ndarray]:
    with (ROOT / "data" / "manifest.csv").open("r", encoding="utf-8", newline="") as file:
        rows = [row for row in csv.DictReader(file) if row["split"] == "test"]
    if len(rows) != 205:
        raise RuntimeError(f"Esperados 205 arquivos de teste, encontrados {len(rows)}.")
    audio = np.stack([load_audio(ROOT / row["path"]) for row in rows])[..., np.newaxis]
    labels = np.asarray([LABELS.index(row["label"]) for row in rows], dtype=np.int64)
    return audio, labels


def convert(model: tf.keras.Model) -> None:
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    FLOAT_MODEL.write_bytes(converter.convert())

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    QUANT_MODEL.write_bytes(converter.convert())


def run_litert(path: Path, audio: np.ndarray) -> tuple[np.ndarray, dict]:
    interpreter = tf.lite.Interpreter(model_path=str(path), num_threads=1)
    interpreter.allocate_tensors()
    inputs = interpreter.get_input_details()
    outputs = interpreter.get_output_details()
    if len(inputs) != 1 or len(outputs) != 1:
        raise RuntimeError(f"Esperada uma entrada e uma saída em {path.name}.")
    input_info, output_info = inputs[0], outputs[0]
    if tuple(input_info["shape"]) != (1, SAMPLES_PER_CLIP, 1):
        raise RuntimeError(f"Forma de entrada inesperada em {path.name}: {input_info['shape']}")
    if input_info["dtype"] != np.float32 or output_info["dtype"] != np.float32:
        raise RuntimeError(f"Entrada/saída não são float32 em {path.name}.")
    if tuple(output_info["shape"]) != (1, len(LABELS)):
        raise RuntimeError(f"Forma de saída inesperada em {path.name}: {output_info['shape']}")

    scores = np.empty((len(audio), len(LABELS)), dtype=np.float32)
    for index, clip in enumerate(audio):
        interpreter.set_tensor(input_info["index"], clip[np.newaxis, ...])
        interpreter.invoke()
        scores[index] = interpreter.get_tensor(output_info["index"])[0]
    tensor_dtypes = {str(detail["dtype"].__name__) for detail in interpreter.get_tensor_details()}
    interface = {
        "input_shape": input_info["shape"].tolist(),
        "input_dtype": input_info["dtype"].__name__,
        "output_shape": output_info["shape"].tolist(),
        "output_dtype": output_info["dtype"].__name__,
        "tensor_dtypes_present": sorted(tensor_dtypes),
    }
    return scores, interface


def metrics(scores: np.ndarray, true_labels: np.ndarray) -> dict:
    predicted = scores.argmax(axis=1)
    matrix = np.zeros((len(LABELS), len(LABELS)), dtype=np.int64)
    for truth, prediction in zip(true_labels, predicted):
        matrix[truth, prediction] += 1
    return {
        "accuracy": float(np.mean(predicted == true_labels)),
        "correct": int(np.sum(predicted == true_labels)),
        "errors": int(np.sum(predicted != true_labels)),
        "confusion_matrix_rows_true_columns_predicted": matrix.tolist(),
    }


def main() -> None:
    if not KERAS_MODEL.is_file():
        raise FileNotFoundError("Modelo treinado não encontrado. Execute training/train.py.")
    model = tf.keras.models.load_model(KERAS_MODEL)
    audio, true_labels = load_test()
    keras_scores = model.predict(audio, batch_size=32, verbose=0)
    convert(model)
    float_scores, float_interface = run_litert(FLOAT_MODEL, audio)
    quant_scores, quant_interface = run_litert(QUANT_MODEL, audio)

    keras_metrics = metrics(keras_scores, true_labels)
    float_metrics = metrics(float_scores, true_labels)
    quant_metrics = metrics(quant_scores, true_labels)
    original_report = json.loads((RESULTS / "evaluation.json").read_text(encoding="utf-8"))
    if abs(keras_metrics["accuracy"] - original_report["accuracy"]) > 1e-9:
        raise RuntimeError("A avaliação Keras não reproduziu a etapa 3.")

    float_bytes = FLOAT_MODEL.stat().st_size
    quant_bytes = QUANT_MODEL.stat().st_size
    accuracy_drop = float_metrics["accuracy"] - quant_metrics["accuracy"]
    quantized_tensors = "int8" in quant_interface["tensor_dtypes_present"]
    if not quantized_tensors:
        raise RuntimeError("O modelo otimizado não contém tensores int8.")
    if quant_bytes >= float_bytes:
        raise RuntimeError("O arquivo quantizado não ficou menor que o modelo float32.")
    if accuracy_drop > 0.02:
        raise RuntimeError(f"Perda de acurácia acima do limite escolhido de 2 p.p.: {accuracy_drop:.4f}")

    report = {
        "test_examples": len(true_labels),
        "labels_in_order": list(LABELS),
        "keras_model": {"file": "models/go_stop_model.keras", "bytes": KERAS_MODEL.stat().st_size, **keras_metrics},
        "float32_tflite": {"file": "models/go_stop_float32.tflite", "bytes": float_bytes, "interface": float_interface, **float_metrics},
        "quantized_tflite": {"file": "models/go_stop_quantized.tflite", "bytes": quant_bytes, "interface": quant_interface, **quant_metrics},
        "quantization_method": "post-training dynamic-range; tf.lite.Optimize.DEFAULT sem dataset representativo",
        "size_reduction_vs_float32_percent": 100.0 * (float_bytes - quant_bytes) / float_bytes,
        "quantized_accuracy_delta_percentage_points": 100.0 * (quant_metrics["accuracy"] - float_metrics["accuracy"]),
        "float_vs_keras_prediction_disagreements": int(np.sum(float_scores.argmax(axis=1) != keras_scores.argmax(axis=1))),
        "quantized_vs_float_prediction_disagreements": int(np.sum(quant_scores.argmax(axis=1) != float_scores.argmax(axis=1))),
        "max_absolute_score_difference_float_vs_keras": float(np.max(np.abs(float_scores - keras_scores))),
        "max_absolute_score_difference_quantized_vs_float": float(np.max(np.abs(quant_scores - float_scores))),
        "selected_for_android": "models/go_stop_quantized.tflite",
        "selection_rule": "menor que float32 e perda de acurácia no teste <= 2 pontos percentuais",
        "tensorflow_version": tf.__version__,
    }
    (RESULTS / "conversion_comparison.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (MODELS / "deployment.json").write_text(
        json.dumps({
            "model_file": "go_stop_quantized.tflite",
            "labels_file": "labels.json",
            "audio_spec_file": "../data/audio_spec.json",
            "input_shape": [1, SAMPLES_PER_CLIP, 1],
            "input_dtype": "float32",
            "output_shape": [1, len(LABELS)],
            "output_dtype": "float32",
            "labels_in_order": list(LABELS),
            "quantization": "dynamic-range, weights int8; float32 interface",
        }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Keras: {KERAS_MODEL.stat().st_size} bytes; {keras_metrics['correct']}/{len(true_labels)} acertos")
    print(f"TFLite float32: {float_bytes} bytes; {float_metrics['correct']}/{len(true_labels)} acertos")
    print(f"TFLite quantizado: {quant_bytes} bytes; {quant_metrics['correct']}/{len(true_labels)} acertos")
    print(f"Redução: {report['size_reduction_vs_float32_percent']:.2f}% em relação ao .tflite float32")
    print("Escolhido para Android: models/go_stop_quantized.tflite")


if __name__ == "__main__":
    main()
