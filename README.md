# `Plate OCR Benchmark: Leitura de Placas de Ativos Industriais`

> Benchmark controlado de 3 abordagens de leitura/extração de campos de placas de motores elétricos — Tesseract, EasyOCR e um modelo multimodal com visão — sobre 30 imagens de teste com gabarito, medido por Exact Match Accuracy e Character-level Accuracy. Sprint 3 do projeto Forzy, FIAP 2026.

---

## `Tecnologias`

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-4.10-5C3EE8?logo=opencv&logoColor=white)
![Tesseract](https://img.shields.io/badge/Tesseract-OCR%205.4-black)
![EasyOCR](https://img.shields.io/badge/EasyOCR-1.7-orange)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?logo=openai&logoColor=white)
![Pandas](https://img.shields.io/badge/pandas-2.2-150458?logo=pandas&logoColor=white)
![Pytest](https://img.shields.io/badge/pytest-8.3-0A9EDC?logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

---

## `O que faz`

Retoma o gargalo real medido na Sprint 1 do projeto Forzy — pipeline YOLOv8 + OCR com **0% de
acurácia global** de leitura de campos no lote de teste — e ataca especificamente essa etapa,
sob um experimento controlado e reprodutível:

- Gera um conjunto de teste de **30 imagens sintéticas** de placas de motor (10 fácil / 10 médio
  / 10 difícil), com gabarito gravado **antes** de qualquer OCR rodar
- Roda **3 abordagens de leitura** sobre as mesmas 30 imagens: Tesseract, EasyOCR e um modelo
  multimodal com visão
- Calcula **Exact Match Accuracy** e **Character-level Accuracy (1 − CER)** por campo, por
  imagem, por dificuldade e por abordagem
- Gera evidências: CSVs detalhados, análise de erro e 4 gráficos comparativos

### Resultado (30 imagens × 10 campos = 300 avaliações por abordagem)

| Abordagem | Exact Match | Fácil | Médio | Difícil |
|---|---|---|---|---|
| **Multimodal (visão)** | **78,0%** | 100% | 100% | 34% |
| Tesseract + OpenCV | 45,7% | 96% | 40% | 1% |
| EasyOCR + OpenCV | 24,0% | 66% | 6% | 0% |

Detalhe completo, metodologia e análise de erro no relatório técnico:
[`relatorio_tecnico.pdf`](report/relatorio_tecnico.pdf) (versão final) ou
[`relatorio_tecnico.md`](report/relatorio_tecnico.md) (fonte, editável).

---

## `Arquitetura`

```
src/
├── dataset_gen.py            geracao das 30 imagens de teste + ground_truth.csv (seed fixa)
├── run_benchmark.py          roda uma abordagem sobre as 30 imagens
├── methods/
│   ├── base.py                interface comum (ExtractionResult)
│   ├── parsing.py             extracao de campos por regex + fuzzy match (compartilhado A/B)
│   ├── tesseract_method.py    Abordagem A: OpenCV multi-estrategia + Tesseract
│   ├── easyocr_method.py      Abordagem B: OpenCV + EasyOCR (rede neural)
│   └── openai_multimodal.py   Abordagem C: GPT-4o-mini com visao, extracao direta em JSON
├── evaluation/
│   ├── normalization.py       normalizacao para Exact Match e para CER
│   ├── metrics.py             Exact Match Accuracy, Character Error Rate
│   └── aggregate.py           agrega resultados brutos -> CSVs + graficos
└── utils/
    ├── config.py               caminhos e parametros centralizados
    └── io_utils.py             leitura/escrita de imagem segura p/ paths Unicode no Windows
```

---

## `Metodologia`

- **Ground Truth cego**: gravado a partir dos parâmetros usados para desenhar cada placa,
  nunca a partir da saída de um modelo
- **Mesmo parser para A e B**: Tesseract e EasyOCR passam pelo mesmo extrator de campos
  (regex + fuzzy match), isolando a variável "qualidade do OCR" entre as duas
- **Duas métricas, não misturadas**: Exact Match Accuracy (um caractere errado invalida o
  campo — reflete o problema real) e Character-level Accuracy via distância de Levenshtein
  (mede o quão perto chegou mesmo quando erra)
- **3 níveis de dificuldade**: iluminação (normal/sombra/reflexo/sub-superexposta),
  desgaste/sujeira (limpa a severa/óleo), ângulo de câmera (0° a 40°) e resolução

---

## `Estrutura`

```
plate-ocr-benchmark/
├── data/
│   ├── test/{easy,medium,hard}/    30 imagens (10 por dificuldade)
│   └── ground_truth.csv
├── src/                              (ver Arquitetura)
├── results/
│   ├── raw/<metodo>.json             saida bruta de cada abordagem
│   ├── metrics/                      CSVs de metricas e analise de erro
│   └── visualizations/               4 graficos comparativos (PNG)
├── evidencias/                       exemplos lado a lado por dificuldade + README
├── report/
│   ├── relatorio_tecnico.pdf         relatorio tecnico completo (versao final)
│   ├── relatorio_tecnico.md          fonte editavel do relatorio
│   └── build_pdf.py                  gera o PDF a partir do .md (reportlab)
├── presentation/                     apresentacao resumida da Sprint
├── tests/                            testes unitarios (pytest)
├── requirements.txt
└── .env.example                      OPENAI_API_KEY (nunca commitar .env real)
```

---

## `Instalacao`

```bash
git clone https://github.com/Arthur-Baptista-dos-Santos/plate-ocr-benchmark.git
cd plate-ocr-benchmark

python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
copy .env.example .env       # preencher OPENAI_API_KEY (so necessaria p/ Abordagem C via API)

python -m src.dataset_gen                        # gera as 30 imagens + gabarito
python -m src.run_benchmark tesseract
python -m src.run_benchmark easyocr
python -m src.run_benchmark openai_multimodal     # requer OPENAI_API_KEY
python -m src.evaluation.aggregate                # gera metricas + graficos em results/

pytest -q                                         # 17 testes unitarios (metricas, normalizacao)
```

---

## `Roadmap Forzy`

| Sprint | Foco | Repo |
|--------|------|------|
| Sprint 1 | Cadastro e visualizacao de ativos | [`motor-sync`](https://github.com/Arthur-Baptista-dos-Santos/motor-sync) |
| Sprint 2 | Digital Twin: RPA + sensores + pipeline OCR | [`digital-twin-assets`](https://github.com/Arthur-Baptista-dos-Santos/digital-twin-assets) |
| Sprint 3 (este) | Benchmark de 3 abordagens de leitura de placas | `plate-ocr-benchmark` |

---

## `Conceitos aplicados`

- **`OCR clássico`**: Tesseract com múltiplas estratégias de pré-processamento (CLAHE,
  binarização adaptativa) e modos PSM, mantendo a leitura de maior confiança
- **`OCR neural`**: EasyOCR (rede neural convolucional), com pré-processamento por
  equalização de histograma e filtro gaussiano
- **`Modelo multimodal`**: leitura e extração estruturada de campos num único passo,
  sem etapa de regex separada — diferença arquitetural real frente ao OCR clássico
- **`Avaliação cega`**: Ground Truth definido antes de qualquer execução de OCR
- **`Métricas de leitura`**: Exact Match Accuracy e Character Error Rate (distância de
  Levenshtein), aplicadas de forma idêntica às 3 abordagens

---

## `Licenca`

Distribuido sob a licenca MIT. Veja [LICENSE](LICENSE) para mais informacoes.

---

## `Autor`

**Arthur Baptista dos Santos**
RM 565346 · Inteligencia Artificial · FIAP 2025-2026

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Arthur%20Baptista-0077B5?logo=linkedin)](https://linkedin.com/in/arthur-baptista-dos-santos)
[![GitHub](https://img.shields.io/badge/GitHub-Arthur--Baptista--dos--Santos-181717?logo=github)](https://github.com/Arthur-Baptista-dos-Santos)
