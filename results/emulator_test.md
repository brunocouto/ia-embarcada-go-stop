# Teste do aplicativo no emulador Android

- **Data:** 05/10/2026
- **Ambiente:** Android Emulator, imagem Android API 35 x86_64, AVD `go_stop_api35`.

## O que foi executado

1. O APK de depuração foi instalado com `adb install` e o aplicativo abriu no emulador.
2. A permissão `RECORD_AUDIO` foi concedida e o botão **Gravar e classificar** foi acionado.
3. O aplicativo percorreu `AudioRecord` → leitura de 16.000 amostras PCM16 → normalização → `Interpreter.run` → resultado na tela, sem erro.
4. Na compilação final, o botão normal mostrou `STOP`, pontuação de 62,6%, e 92,5 ms para `Interpreter.run`. A [captura da tela](emulator_capture.png) registra essa execução.

**Interpretação:** isso verifica que o pipeline do aplicativo roda no Android virtual. Não se sabe qual sinal de áudio foi efetivamente recebido pelo microfone virtual nessa execução. O resultado `STOP` não conta como acerto de reconhecimento, e 92,5 ms não representa desempenho do celular físico.

## Duas gravações conhecidas no Android virtual

O APK de **depuração** inclui duas amostras de áudio do conjunto de teste, convertidas para PCM16 por `android/prepare_debug_samples.py`. Um parâmetro de inicialização disponível apenas no aplicativo depurável passa essas amostras pela **mesma preparação e pelo mesmo modelo** usados após a captura do microfone. Esse caminho pula a leitura do sensor e é identificado na tela como teste sem microfone.

| Palavra real | Arquivo do conjunto de teste | Resultado no emulador | Tempo de `Interpreter.run` | Evidência |
| --- | --- | --- | ---: | --- |
| `go` | `go/0eb48e10_nohash_0.wav` | **GO**, 99,6% | 110,8 ms | [tela GO](emulator_sample_go.png) |
| `stop` | `stop/023a61ad_nohash_0.wav` | **STOP**, 93,0% | 119,4 ms | [tela STOP](emulator_sample_stop.png) |

Comandos usados após instalar o APK no emulador:

```powershell
adb shell am start -S -n br.senai.gostop/.MainActivity --es debug_sample go
adb shell am start -S -n br.senai.gostop/.MainActivity --es debug_sample stop
```

Esses dois acertos demonstram que o modelo embarcado executa os exemplos conhecidos no Android virtual. Eles **não são uma nova medida de acurácia**. Os tempos dependem do emulador e da inicialização do modelo; não representam latência no celular físico.

## Teste posterior pelo microfone virtual

Uma primeira tentativa de reproduzir um arquivo `go` pelo alto-falante do computador produziu `STOP`, mas ainda não havia confirmação do sinal recebido. Uma tentativa de injeção direta de áudio travou o emulador antes de produzir um resultado válido. Depois, a captura foi medida e duas reproduções acústicas foram confirmadas no microfone virtual, com resultados GO e STOP corretos. O procedimento, as medições e as telas estão em [emulator_microphone_test.md](emulator_microphone_test.md). O celular físico é opcional pelo enunciado.
