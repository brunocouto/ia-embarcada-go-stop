# Plano e acompanhamento do projeto final

- **Disciplina:** IA Embarcada e Modelos Compactos
- **Fonte dos requisitos:** enunciado do professor recebido localmente; os arquivos originais e uma conversa pessoal não são publicados
- **Estado geral:** em andamento
- **Etapa atual:** 6 — repositório e entrega
- **Última atualização:** 05/10/2026

## Projeto escolhido

**Reconhecimento de duas palavras por áudio em Android.** O usuário toca em um botão, fala **“go”** ou **“stop”** durante uma gravação curta, e o aplicativo mostra a palavra prevista pelo modelo. A captura e a inferência acontecem no Android, que pode ser executado no emulador. A gravação sob comando evita ter de construir escuta contínua e mantém a demonstração simples.

- **Sensor:** microfone Android, virtual no emulador ou físico no celular.
- **Dataset de treinamento:** Mini Speech Commands, conjunto público usado no tutorial oficial de reconhecimento de áudio do TensorFlow. Utilizar somente as gravações rotuladas `go` e `stop`.
- **Modelo:** classificador pequeno de áudio, treinado pelo grupo em Python/TensorFlow.
- **Conversão:** modelo TensorFlow para `.tflite`.
- **Compressão:** quantização pós-treinamento; comparar tamanho e resultado com o `.tflite` sem compressão.
- **Dispositivo de inferência:** emulador Android; teste no celular físico é opcional.
- **Entrada do aplicativo:** uma gravação de áudio de duração fixa, iniciada pelo usuário.
- **Saída do aplicativo:** palavra prevista e pontuação de confiança.

Essas são **decisões do projeto**, não exigências adicionais do professor. O enunciado permite dispositivo real ou simulado e cita Android/iOS Mobile entre as opções; portanto, este plano não exige instalar o aplicativo em um celular físico.

## Correspondência com o enunciado

| Exigência do professor | Como será demonstrada |
| --- | --- |
| Coleta de dados de sensores | O aplicativo lê o microfone Android no emulador e cria a entrada para inferência. |
| Treinamento com dataset público ou próprio | O grupo treina um modelo com `go` e `stop` do Mini Speech Commands. |
| Conversão e compressão | Gerar o modelo `.tflite` comum e uma versão quantizada; medir tamanho e qualidade. |
| Pipeline no dispositivo, da leitura à inferência | No Android simulado: botão → microfone virtual → preparação do áudio → modelo embarcado → resultado na tela. |
| Repositório GitHub com Git Flow e commits de todos | Branches `main`, `develop` e `feature/...`; cada integrante faz seus próprios commits. |
| Apresentação e vídeo de demonstração | Mostrar dados, treino, compressão, código e execução no emulador Android. |
| PDF da apresentação e `.txt` com link público | Arquivos preparados na etapa final. |

## Etapas e critérios de conclusão

### 0. Planejamento

- [x] Ler os dois arquivos fornecidos e registrar os requisitos.
- [x] Escolher o projeto simples e o dataset.
- [x] Criar este arquivo de acompanhamento.

**Resultado:** plano salvo nesta pasta.

### 1. Preparar o projeto local — CONCLUÍDA

- [x] Criar a estrutura de pastas de código, modelos, resultados e apresentação.
- [x] Criar `README.md` com objetivo, arquitetura e instruções iniciais.
- [x] Verificar as ferramentas já disponíveis antes de definir a forma de execução.

**Resultado:** estrutura local criada. Python estava disponível. Na etapa 5 foram preparados SDK Android e Gradle suficientes para compilar o aplicativo. Por solicitação do usuário, nenhuma configuração de Git foi feita. O Git Flow permanece planejado para a etapa 6.

### 2. Dataset e preparação — CONCLUÍDA

- [x] Obter o Mini Speech Commands da fonte oficial.
- [x] Selecionar arquivos `go` e `stop`.
- [x] Registrar licença, origem, contagem por classe e divisões de treino, validação e teste.
- [x] Definir e implementar uma única especificação de áudio (taxa, canais, duração e normalização) para treino e celular.

**Resultado:** 2.000 gravações válidas, 1.000 de cada classe, 1.070 locutores. Divisões fixas por locutor: treino 1.580, validação 215, teste 205. Origem, licença, hash, manifesto e especificação de áudio estão em `data/`. A coleta no microfone Android pertence à etapa 5.

### 3. Treinamento e avaliação — CONCLUÍDA

- [x] Implementar e executar o script de treino.
- [x] Salvar modelo, rótulos e configurações usadas.
- [x] Avaliar no conjunto de teste; registrar matriz de confusão e acurácia por classe.
- [x] Registrar erros observados no conjunto de teste.

**Resultado:** CNN de 30.338 parâmetros treinada e salva em `models/go_stop_model.keras`. O teste por locutor teve 180 acertos em 205 arquivos (**87,80%**), com 25 erros documentados em `results/`. O modelo foi recarregado e a métrica confirmada. O desempenho em áudio captado ao vivo no Android ainda não foi medido.

### 4. Conversão e compressão — CONCLUÍDA

- [x] Converter o modelo para `.tflite` sem quantização.
- [x] Gerar uma segunda versão com quantização pós-treinamento.
- [x] Executar ambos com os mesmos exemplos de teste.
- [x] Comparar tamanho dos arquivos e resultados; escolher a versão para o aplicativo.

**Resultado:** a versão `.tflite` sem compressão tem 126.768 bytes e 180/205 acertos. A versão quantizada tem 39.824 bytes (68,59% menor) e 179/205 acertos. Os dois modelos foram executados com os mesmos 205 áudios; o quantizado foi escolhido para Android. A comparação detalhada está em `results/conversion_comparison.json`.

### 5. Aplicativo e pipeline no dispositivo — CONCLUÍDA NO EMULADOR

- [x] Criar aplicativo Android com permissão de microfone e botão de gravação.
- [x] Confirmar que o microfone virtual do emulador recebe áudio identificável, para comprovar a coleta do sensor.
- [x] Implementar e executar a captura e preparação do áudio conforme o treino: 16 kHz, mono, 1 segundo, PCM16 dividido por 32768.
- [x] Incluir o modelo `.tflite` escolhido e executar inferência local no Android virtual.
- [x] Implementar a exibição da palavra prevista, pontuação e tempo de inferência.
- [x] Compilar o APK de depuração e verificar modelo, rótulos e permissão incluídos nele.
- [x] Instalar e executar o APK em um emulador Android; verificar que `AudioRecord` → preparação → modelo → resultado funciona sem erro.
- [x] Executar no emulador duas amostras conhecidas de teste (`go` e `stop`) no modo de depuração, sem microfone; ambas foram classificadas corretamente.
- [x] Testar `go` e `stop` pela entrada do microfone virtual; registrar resultados e tempo de inferência no emulador.
- [x] Registrar os dois acertos observados e a correspondência entre o sinal captado e as gravações reproduzidas, sem apresentar isso como acurácia geral.

**Resultado:** aplicativo compilado; APK debug em `android/app/build/outputs/apk/debug/app-debug.apk` (20.178.890 bytes). O fluxo completo executou no emulador Android API 35. Gravações `go` e `stop` foram reproduzidas pelos alto-falantes do computador, captadas pelo microfone virtual e classificadas corretamente pelo aplicativo. As capturas continham 13.611 e 13.095 amostras não nulas, com correspondência ao respectivo WAV original. Pontuações, tempos e telas estão em `results/emulator_microphone_test.md`. São duas tentativas, não uma avaliação de acurácia geral. O celular físico é opcional pelo enunciado.

**Critério de conclusão atendido:** microfone virtual → preparação → inferência → resultado no Android simulado.

### 6. Git Flow e entrega

- [x] Publicar repositório público no GitHub: `https://github.com/brunocouto/ia-embarcada-go-stop`.
- [x] Criar o primeiro commit do projeto em `main` e a branch `develop` para a continuação do trabalho.
- [ ] Trabalhar em branches `feature/...`, integrar em `develop` e finalizar em `main`.
- [ ] Verificar commits de cada integrante.
- [ ] Produzir apresentação de até 10 minutos e exportá-la como PDF.
- [ ] Gravar vídeo de demonstração.
- [x] Criar `link_repositorio.txt` com o link do repositório público.
- [ ] Preparar todos os integrantes para perguntas sobre cada etapa.

**Concluída quando:** todos os arquivos de entrega existem e o repositório público corresponde ao que foi demonstrado.

## Registro de progresso

| Data | Etapa | Registro |
| --- | --- | --- |
| 05/10/2026 | 0 | Planejamento criado. Próxima atividade: etapa 1. |
| 05/10/2026 | 1 | Estrutura e documentação inicial criadas. Git adiado por solicitação do usuário. Próxima atividade: etapa 2. |
| 05/10/2026 | 2 | Dataset oficial obtido e validado; manifesto por locutor e especificação de áudio salvos. Próxima atividade: etapa 3. |
| 05/10/2026 | 3 | Modelo treinado e recarregado; 180/205 acertos no teste, 25 erros registrados. Próxima atividade: etapa 4. |
| 05/10/2026 | 4 | Dois arquivos LiteRT convertidos e testados; quantizado 68,59% menor, 179/205 acertos. Próxima atividade: etapa 5. |
| 05/10/2026 | 5 (parcial) | Aplicativo Android implementado e APK compilado. Falta instalar no celular, testar o microfone e registrar resultados reais. Git continua adiado. |
| 05/10/2026 | 5 (simulação) | APK instalado em emulador API 35; captura virtual até resultado confirmada. Amostras conhecidas `go` e `stop` classificadas corretamente dentro do Android virtual. Teste de fala pelo microfone continua pendente. |
| 05/10/2026 | Correção do escopo | Conferida a página 6 do PDF: deploy em dispositivo real ou simulado é permitido. Celular físico removido dos critérios obrigatórios; emulador Android passa a ser o dispositivo planejado. |
| 05/10/2026 | 5 (conclusão) | Microfone virtual recebeu WAVs `go` e `stop` reproduzidos pelo computador; o aplicativo classificou ambos corretamente. Sinal captado e inferência documentados. Próxima atividade: etapa 6, sem iniciar Git até nova orientação. |
| 05/10/2026 | 6 (parcial) | Usuário autorizou Git. Repositório público criado na conta `brunocouto`, primeiro commit publicado em `main` e branch `develop` preparada. Faltam commits dos outros integrantes, trabalho em `feature/...`, apresentação e vídeo. |

## Fontes técnicas previstas

- Dataset e tutorial: https://www.tensorflow.org/tutorials/audio/simple_audio
- Conversão e quantização: https://developers.google.com/edge/litert/conversion/tensorflow/quantization/post_training_quantization
- Áudio no Android: https://developer.android.com/media/platform/mediarecorder

Este arquivo deve ser atualizado **ao concluir cada etapa**, com os arquivos criados, resultados medidos e o próximo passo. Não marcar uma tarefa como concluída sem verificá-la.
