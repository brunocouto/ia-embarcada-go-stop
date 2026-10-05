# Coleta e inferência pelo microfone virtual

- **Data:** 05/10/2026
- **Dispositivo:** Android Emulator API 35 x86_64, AVD `go_stop_api35`
- **Aplicativo:** APK debug, modelo quantizado `go_stop_quantized.tflite`

## Procedimento

O emulador foi iniciado com áudio do computador habilitado (`-allow-host-audio` e `adb emu avd hostmicon`). O botão normal **Gravar e classificar** acionou `AudioRecord` no Android virtual. Para ter uma palavra de referência, um WAV da divisão de **teste** foi reproduzido nos alto-falantes do computador; o microfone do computador alimentou o microfone virtual. O aplicativo gravou 16.000 amostras PCM16, normalizou o áudio e executou o modelo no próprio emulador.

No APK debug, a última captura foi temporariamente guardada no armazenamento privado do aplicativo como `last_capture.pcm`. Ela foi analisada para confirmar que o som conhecido chegou ao sensor virtual. O APK release não guarda a captura. Os arquivos PCM captados não foram adicionados ao projeto.

## Resultados observados

| Palavra reproduzida | WAV da divisão de teste | Resultado na tela | Amostras não nulas / 16.000 | Pico PCM16 | Tempo de `Interpreter.run` | Evidência |
| --- | --- | --- | ---: | ---: | ---: | --- |
| `go` | `go/129c7d8d_nohash_0.wav` | **GO**, 55,6% | 13.611 | 1.750 | 41,7 ms | [tela GO](emulator_microphone_go.png) |
| `stop` | `stop/023a61ad_nohash_0.wav` | **STOP**, 76,6% | 13.095 | 2.046 | 6,9 ms | [tela STOP](emulator_microphone_stop.png) |

Para verificar a origem do sinal, foi calculada a maior correlação cruzada absoluta normalizada entre a captura e cada WAV de referência, permitindo deslocamento temporal. A captura de `go` teve correlação **0,7129** com o WAV `go` e **0,0686** com `stop`; a de `stop`, **0,3807** com `stop` e **0,0137** com `go`. Isso dá evidência de que as gravações reproduzidas chegaram ao microfone virtual; a reprodução acústica e o microfone mudam volume e forma de onda.

**Limite:** são apenas duas tentativas, ambas corretas. Não representam acurácia geral nem latência em celular físico. O tempo informado mede somente a chamada de inferência. O professor permite deploy em dispositivo real ou simulado; o teste acima demonstra a coleta do sensor virtual até a inferência no emulador.
