# Resultado da etapa 4: conversão e compressão

O script `training/convert_model.py` converteu o modelo treinado para LiteRT (`.tflite`) em duas versões: uma `float32` sem quantização e outra com **quantização pós-treinamento de faixa dinâmica**. A segunda usa `tf.lite.Optimize.DEFAULT` e contém tensores `int8`. O método segue a [documentação oficial de quantização do LiteRT](https://developers.google.com/edge/litert/conversion/tensorflow/quantization/post_training_quantization).

As três versões foram avaliadas nos **mesmos 205 exemplos de teste**:

| Modelo | Arquivo | Tamanho | Acertos | Acurácia |
| --- | --- | ---: | ---: | ---: |
| Treinado em Keras | `go_stop_model.keras` | 430.922 bytes | 180/205 | 87,80% |
| LiteRT sem compressão | `go_stop_float32.tflite` | 126.768 bytes | 180/205 | 87,80% |
| LiteRT quantizado | `go_stop_quantized.tflite` | 39.824 bytes | 179/205 | 87,32% |

O arquivo quantizado ficou **68,59% menor que o `.tflite` sem compressão**. Houve uma mudança de previsão no teste, equivalente a **0,49 ponto percentual** a menos de acurácia. O `.keras` inclui estrutura de treinamento e não é a base usada para calcular essa redução.

**Modelo escolhido para o aplicativo:** `models/go_stop_quantized.tflite`. Ele recebe `float32[1,16000,1]` e devolve `float32[1,2]`, com rótulos na ordem `go`, `stop`. A escolha aplica o critério registrado no script: arquivo menor e perda de até 2 pontos percentuais no teste. Essa tolerância é uma decisão do projeto, não uma exigência do professor.

O relatório completo está em [`conversion_comparison.json`](conversion_comparison.json). O resultado ainda **não foi medido no celular**; tempo de inferência e áudio captado pelo microfone pertencem à etapa 5.

Para reproduzir a conversão a partir do modelo treinado, executar na raiz do projeto:

```text
python training/convert_model.py
```
