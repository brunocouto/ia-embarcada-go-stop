# Reconhecimento de “go” e “stop” no Android

Projeto final da disciplina **IA Embarcada e Modelos Compactos**.

## Objetivo

Treinar um classificador pequeno para reconhecer as palavras `go` e `stop` em gravações curtas. Depois, converter e comprimir o modelo e executá-lo em um aplicativo Android que lê o microfone virtual do emulador. O celular físico pode ser usado, mas não é exigido pelo enunciado.

## Fluxo previsto

1. Capturar áudio pelo microfone Android no emulador.
2. Preparar o áudio no mesmo formato usado no treinamento.
3. Executar o modelo embarcado no Android simulado.
4. Mostrar a palavra prevista e a pontuação de confiança.

O aplicativo será acionado por um botão de gravação. O dataset público de treinamento será o **Mini Speech Commands**, limitado às classes `go` e `stop`. A entrada do microfone virtual servirá para demonstrar a coleta pelo sensor; amostras conhecidas do dataset verificam separadamente a inferência no emulador.

## Estado do projeto

O acompanhamento, os critérios de conclusão e a etapa atual estão em [PLANO_DO_PROJETO.md](PLANO_DO_PROJETO.md). **O dataset, o modelo treinado, a compressão e o aplicativo Android no emulador estão prontos. `Go` e `stop` foram captados pelo microfone virtual e classificados no Android simulado.** Veja as [instruções do aplicativo](android/README.md), o [teste do microfone virtual](results/emulator_microphone_test.md), os [resultados do treinamento](results/README.md) e a [comparação da conversão](results/conversion_README.md).

## Estrutura

- `data/`: descrição da origem e preparação dos dados; o download do dataset fica apenas na máquina local.
- `training/`: scripts de preparação, treinamento, avaliação e conversão.
- `models/`: modelos finais e seus rótulos.
- `android/`: código do aplicativo.
- `results/`: métricas e comparações medidas.
- `presentation/`: arquivos da apresentação final, ainda a preparar.

## Fonte do dataset

Tutorial oficial do TensorFlow: https://www.tensorflow.org/tutorials/audio/simple_audio

## Reproduzir o treinamento e a conversão

Com Python e as dependências de `training/requirements.txt`, execute na raiz:

```powershell
python -m pip install -r training/requirements.txt
python training/prepare_dataset.py
python training/train.py
python training/convert_model.py
python android/sync_model.py
```

O primeiro script baixa o Mini Speech Commands da fonte oficial. Os arquivos grandes em `data/raw/` são locais e não entram no repositório. Os modelos finais, os rótulos, o manifesto de dados e os resultados medidos estão incluídos para inspeção. Para compilar ou testar o aplicativo, siga o [guia Android](android/README.md).
