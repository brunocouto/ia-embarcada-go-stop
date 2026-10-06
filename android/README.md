# Aplicativo Android: GO ou STOP

Esta é a implementação da etapa 5 do projeto. O aplicativo usa o microfone Android, lê **1 segundo** de áudio mono PCM16 a **16 kHz**, divide cada amostra por **32768**, executa `go_stop_quantized.tflite` localmente e mostra a palavra prevista, sua pontuação e o tempo da chamada de inferência. No APK release, o áudio fica apenas na memória; o APK debug guarda temporariamente a última captura no armazenamento privado para verificar o sensor.

## Estado verificado em 05/10/2026

- O projeto Android compilou com `assembleDebug`.
- O APK gerado é `app/build/outputs/apk/debug/app-debug.apk` (20.178.890 bytes).
- O APK contém o modelo quantizado e `labels.json`, conferidos com os arquivos em `models/`.
- O manifesto do APK declara a permissão de microfone e exige Android 6.0 ou superior.
- O APK foi instalado e executado em um **emulador Android API 35**. A leitura de `AudioRecord` e a inferência chegaram ao resultado na tela. Duas amostras conhecidas, `go` e `stop`, também foram classificadas corretamente no próprio emulador pelo modo de teste do APK debug; veja o [registro](../results/emulator_test.md).
- O **microfone virtual** recebeu reproduções acústicas de `go` e `stop`; ambas foram classificadas corretamente pelo botão normal. O [registro da coleta e inferência](../results/emulator_microphone_test.md) contém as medições e telas. O celular físico não é obrigatório segundo o enunciado.

## Abrir e compilar

Abra a pasta `android/` no Android Studio, aguarde a sincronização do Gradle e execute **Build > Build APK(s)**. O projeto usa JDK 17, Gradle 8.13, Android Gradle Plugin 8.13.2 e Android SDK Platform 35. O arquivo `gradlew.bat` permite compilar pelo PowerShell na pasta `android/`:

```powershell
python sync_model.py
.\gradlew.bat :app:assembleDebug
```

O script `sync_model.py` atualiza os dois assets a partir de `../models/` e confere seus hashes. Rode-o quando o modelo ou os rótulos mudarem.

O APK **debug** também contém duas amostras de teste em `app/src/debug/assets/`. Para recriá-las a partir dos arquivos do dataset, execute `python prepare_debug_samples.py` antes do build. O modo de teste pode ser iniciado por `adb shell am start -S -n br.senai.gostop/.MainActivity --es debug_sample go` (ou `stop`). A tela identifica que esse modo não lê o microfone. Os assets de teste não entram no APK release.

Se o Gradle não encontrar o SDK Android, defina `ANDROID_HOME` com o caminho local do SDK antes de compilar. Essa variável é usada apenas no computador de desenvolvimento.

## Repetir o teste com o microfone virtual

Inicie o emulador Android, instale o APK debug e habilite a opção **Virtual microphone uses host audio input** nos controles do emulador. Em seguida, toque no botão do aplicativo e fale `go` ou `stop` no microfone do computador. Também é possível reproduzir um WAV conhecido pelos alto-falantes próximos ao microfone, como no [teste registrado](../results/emulator_microphone_test.md). Registre palavra falada, palavra prevista, pontuação, tempo e condições da gravação. Os resultados do modo debug com arquivos embutidos verificam o modelo, mas não substituem esse teste do sensor.

## Teste opcional no celular físico

1. Se optar por testar no aparelho, conecte o Android ao computador e habilite a depuração USB, ou transfira o APK para o aparelho e instale-o manualmente.
2. Abra **Go ou Stop**. Toque em **Gravar e classificar** e conceda a permissão de microfone. Toque novamente para iniciar a gravação.
3. Fale `go` ou `stop` em inglês logo após iniciar a gravação. O aplicativo lê exatamente 16.000 amostras e então mostra previsão, pontuação e tempo de inferência.
4. Registre em `results/device_tests.csv` uma linha por tentativa, com `palavra_falada`, `palavra_prevista`, `pontuacao_percentual`, `inferencia_ms` e observações. Crie o arquivo somente ao realizar os testes; não preencha resultados presumidos.
5. Confira se o fluxo inteiro funciona: permissão → microfone → preparação → inferência → resultado. Anote erros e as condições de gravação. Se possível, filme uma demonstração curta para a entrega final.

As pontuações de `go` e `stop` comparam apenas essas duas classes. Capturas claramente muito baixas (RMS abaixo de `0.004` e pico abaixo de `0.03`) são rejeitadas como ausência de fala; previsões abaixo de `85%` são exibidas como fala incerta. O limite de nível fica abaixo do percentil 5 das amostras de treino. O modelo não foi treinado para reconhecer silêncio, ruído, outras palavras ou comandos contínuos; ruído acima do limite ainda pode receber uma pontuação alta, e erros confiantes podem ocorrer. Para corrigir confusões específicas do microfone ou da voz do aparelho, é necessário avaliar capturas reais e incluir exemplos representativos no treinamento. A tela mostra as duas pontuações e os níveis RMS/pico para ajudar nesse diagnóstico. O tempo informado mede apenas `Interpreter.run`, não a gravação de um segundo nem a inicialização do modelo.

## Arquivos principais

- `app/src/main/java/br/senai/gostop/MainActivity.java`: captura, normalização, inferência e interface.
- `app/src/main/assets/`: modelo e rótulos incluídos no APK.
- `app/src/main/AndroidManifest.xml`: permissão de microfone e atividade inicial.
- `app/build/outputs/apk/debug/app-debug.apk`: APK de teste gerado localmente.
