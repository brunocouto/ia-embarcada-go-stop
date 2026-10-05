# Modelos do projeto

| Arquivo | Uso |
| --- | --- |
| `go_stop_model.keras` | Modelo original treinado na etapa 3. |
| `go_stop_float32.tflite` | Conversão sem quantização, usada como referência. |
| `go_stop_quantized.tflite` | Modelo comprimido escolhido para integrar ao aplicativo Android. |
| `labels.json` | Ordem das saídas: `go`, `stop`. |
| `deployment.json` | Contrato de entrada e saída do modelo escolhido. |

O aplicativo deverá carregar `go_stop_quantized.tflite`. Sua entrada é `float32[1,16000,1]`, normalizada conforme `data/audio_spec.json`; a saída é `float32[1,2]` com as pontuações de `go` e `stop`, nessa ordem.

A quantização pós-treinamento reduziu o arquivo de **126.768 para 39.824 bytes** em relação ao modelo `.tflite` sem compressão. Os pesos contêm tensores `int8`, mas a interface de entrada e saída continua `float32`. A avaliação completa está em `results/conversion_comparison.json`.
