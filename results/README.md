# Resultados da etapa 3

O modelo `models/go_stop_model.keras` foi treinado com `training/train.py` usando o manifesto da etapa 2. A entrada é áudio bruto com **16.000 amostras float32**; a saída contém as pontuações na ordem `go`, `stop`. A rede tem **30.338 parâmetros** e o arquivo salvo ocupa **430.922 bytes**.

Treino executado com semente 42, lote de 32 exemplos e parada antecipada. Foram realizadas 12 épocas; os pesos salvos são os da **época 7**, escolhida pela menor perda na validação. A acurácia de validação nessa época foi **78,14%**. O maior valor de acurácia de validação durante o treino, 83,72%, ocorreu em outra época e **não** corresponde aos pesos salvos.

## Conjunto de teste

O teste foi feito uma vez com os **205 arquivos separados por locutor** na etapa 2. O modelo salvo foi recarregado e produziu os mesmos resultados:

- **Acurácia:** 180/205 = **87,80%**.
- **Erros:** 25.
- **Recall de `go`:** 92/109 = **84,40%**.
- **Recall de `stop`:** 88/96 = **91,67%**.

Matriz de confusão (linhas = palavra real; colunas = palavra prevista):

| Real / previsto | `go` | `stop` |
| --- | ---: | ---: |
| `go` | 92 | 17 |
| `stop` | 8 | 88 |

Os números completos estão em [`evaluation.json`](evaluation.json), a evolução por época em [`training_history.csv`](training_history.csv) e os **25 erros** em [`test_errors.csv`](test_errors.csv). A configuração de treino está em [`training_config.json`](training_config.json).

## Limite da avaliação

O modelo conhece somente `go` e `stop`. Ele ainda não foi avaliado com silêncio, outras palavras ou gravações feitas no celular do projeto. Assim, a acurácia acima descreve **apenas a distinção entre essas duas palavras no conjunto de teste**; não mede desempenho de uso ao vivo. Isso será verificado na etapa do aplicativo.

## Reproduzir

Na raiz do projeto, após preparar o dataset e instalar as dependências de `training/requirements.txt`:

```text
python training/train.py
```
