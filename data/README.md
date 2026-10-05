# Dados do projeto

## Origem e licença

Usamos as classes `go` e `stop` do **Mini Speech Commands**, obtido pelo [tutorial oficial do TensorFlow](https://www.tensorflow.org/tutorials/audio/simple_audio). O tutorial informa que o dataset Speech Commands foi disponibilizado sob licença **CC BY**. A página e o dataset devem ser atribuídos na apresentação e no repositório final.

- Arquivo original: `https://storage.googleapis.com/download.tensorflow.org/data/mini_speech_commands.zip`
- Tamanho: **182.082.353 bytes**
SHA-256 do arquivo baixado: `49650f2341b26d886b46b3f4fb8fed59e30300b17550f1ee4a768b3106cf93a0`

O ZIP também contém arquivos de metadados do macOS chamados `._*.wav`. Eles não são gravações WAV e foram excluídos da preparação.

## Seleção e divisões

Foram selecionadas **2.000 gravações válidas**, sendo **1.000 `go` e 1.000 `stop`**, de **1.070 locutores**. A divisão foi feita por identificador de locutor, com semente 42. Uma pessoa aparece em apenas uma divisão.

| Divisão | `go` | `stop` | Total |
| --- | ---: | ---: | ---: |
| Treino | 788 | 792 | 1.580 |
| Validação | 103 | 112 | 215 |
| Teste | 109 | 96 | 205 |

Os caminhos, rótulos, locutores e divisões estão em [`manifest.csv`](manifest.csv). Os números e o hash do arquivo original estão em [`dataset_summary.json`](dataset_summary.json).

## Formato do áudio

A especificação única está em [`audio_spec.json`](audio_spec.json): **WAV PCM16, mono, 16 kHz, 1 segundo, 16.000 amostras**. O código em `training/audio.py` converte cada amostra inteira para `float32` dividindo por 32768; áudios curtos recebem zeros ao final. O aplicativo Android aplica a mesma preparação.

## Como reproduzir

Na raiz do projeto, executar:

```text
python training/prepare_dataset.py
```

O script baixa o ZIP oficial para `data/raw/`, extrai apenas `go` e `stop`, valida todos os cabeçalhos WAV e recria o manifesto e o resumo. A pasta `data/raw/` contém downloads e gravações extraídas; ela não deverá ser enviada ao futuro repositório público por padrão.

A coleta pelo microfone virtual do emulador e a inferência no Android foram realizadas na etapa 5. As medições estão em [`../results/emulator_microphone_test.md`](../results/emulator_microphone_test.md). Os arquivos PCM captados não são publicados; o APK debug guarda temporariamente a última captura no armazenamento privado do aplicativo para verificação.
