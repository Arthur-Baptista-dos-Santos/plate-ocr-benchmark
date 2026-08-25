<!--
Apresentação resumida — Sprint 3 (Visão Computacional)
Um slide por seção "---". Todos os números abaixo são reais, calculados por
src/evaluation/aggregate.py sobre as 30 imagens de teste.
-->

# Sprint 3 — Leitura de Placas de Ativos Industriais
### Digital Twin de Ativos Industriais | Visão Computacional
Arthur Baptista dos Santos (565346) · Joao Pedro (561738) · Nelson Felix (565603)

---

## De onde viemos

- **Sprint 1 (FORZY):** YOLOv8 (detecção) + Tesseract/TrOCR (leitura), 180 imagens de teste
  - Detecção: 100% · Score OCR médio: 43,9% · **Acurácia global: 0,0%**
  - A leitura de campos, não a detecção, é o gargalo real
- **Sprint 2 (Digital Twin):** EasyOCR isolado, 3 placas (normal/ruído/inclinada)
  - ~87% / ~62% / ~50% — mas avaliação manual, N=3, sem métrica formal

---

## O que muda nesta Sprint

- Escopo controlado: só **leitura/extração de campos** (sem retomar detecção — pesos do YOLO
  não foram persistidos)
- **3 abordagens** sob o mesmo protocolo: Tesseract, EasyOCR, GPT-4o-mini (multimodal)
- **30 imagens** de teste (10 fácil / 10 médio / 10 difícil), gabarito gravado antes do OCR
- Métricas formais: **Exact Match Accuracy** + **Character-level Accuracy** (CER)

---

## As 3 abordagens

| | Tesseract | EasyOCR | Multimodal (visão) |
|---|---|---|---|
| Tipo | OCR clássico | OCR neural | LLM com visão (leitura direta) |
| Pré-processamento | CLAHE/binarização, multi-estratégia | Equalização + blur | Nenhum (imagem direta) |
| Extração de campos | Regex + fuzzy match | Regex + fuzzy match (mesmo parser) | Modelo devolve campos já estruturados |
| Execução nesta rodada | Local (30/30 imagens) | Local (30/30 imagens) | Leitura direta na sessão (sem chave de API configurada) |

---

## Conjunto de teste

- 30 imagens sintéticas, mesmo vocabulário/layout da Sprint 1 (FORZY)
- Gerador determinístico (seed fixa) → reprodutível
- 3 níveis de dificuldade: iluminação, desgaste/sujeira, ângulo de câmera (0° a 40°), resolução
- Ground Truth gravado a partir dos parâmetros de geração — nunca da saída de um modelo

---

## Resultados — acurácia geral

30 imagens × 10 campos = 300 avaliações por abordagem

| Abordagem | Exact Match | Character-level | Fácil | Médio | Difícil |
|---|---|---|---|---|---|
| **Multimodal (visão)** | **78,0%** | **79,4%** | 100% | 100% | 34% |
| Tesseract | 45,7% | 45,9% | 96% | 40% | 1% |
| EasyOCR | 24,0% | 26,3% | 66% | 6% | 0% |

0% de falha de execução em todas as abordagens — toda diferença é acurácia de leitura.

---

## Resultados — por dificuldade e por campo

- Inclinação de câmera + iluminação ruim (reflexo/sub/superexposição) são o que mais derruba a
  acurácia — não o ruído/desgaste isolado
- Campos com separador fixo (`tensão`, `corrente`) e prefixo fixo (`grau_ip`) são os piores para
  os OCRs clássicos — mas o motivo real (confirmado depois) é o texto OCR chegar vazio/destruído
  sob degradação, não um regex frágil (ver slide seguinte)
- `num_serie` é o campo mais difícil mesmo para o multimodal (66,7%) — único alfanumérico longo
  sem vocabulário fechado para comparar

---

## Multimodal vs. OCR clássico — o que observamos

- Multimodal vence claramente nos níveis fácil/médio (100%/100% vs. ≤40% do OCR clássico) e
  ainda lidera no difícil (34% vs. ≤1%), mas degrada bastante lá também — nenhuma abordagem está
  pronta para produção sem um limiar de confiança / recusa de leitura
- Quando erra em condição extrema, o multimodal tende a devolver campo vazio (admite que não
  leu) em vez de um valor errado — mais seguro para popular um banco de ativos
- EasyOCR ficou sistematicamente atrás do Tesseract nesta rodada — contradiz a conclusão da
  Sprint 2 (só EasyOCR havia sido testado lá, com N=3); mostra o valor de comparar abordagens
  lado a lado
- Trade-off ainda em aberto: Abordagem C rodou como leitura direta em sessão, não via API
  (`openai_multimodal.py` está pronto mas não foi executado com chave real) — custo e latência
  reais de API ficam como próximo passo

---

## Tentativa de melhoria do parsing (resultado negativo, mas real)

- Hipótese inicial: erro do OCR clássico era "1 caractere errado no separador" — regex tornado
  mais tolerante (`/` lido como `|`/traço, `kW`/`Hz`/`IP` com espaço entre letras)
- Investigação em `results_detalhado.csv`: **89–100% dos erros por campo são predições vazias**,
  não valores errados — regex nunca chegou a rodar sobre texto útil
- Exemplo real: Tesseract devolveu `"45226414"` para uma corrente esperada `12.8/7.4 A`
  (dígitos presentes, separador e ponto decimal destruídos); em outra imagem difícil, o texto
  bruto inteiro foi `"pO"`
- Regex melhorado + benchmark re-executado → **acurácia idêntica antes/depois** (45,7% / 24,0%)
- Conclusão: o gargalo é a extração OCR sob degradação, não o parsing — regra mais tolerante não
  ajuda quando não há texto para casar
  reais de API ficam como próximo passo

---

## Limitações e próximos passos

- Sem pipeline ponta-a-ponta (falta retomar detecção da placa na cena)
- Dataset ainda sintético — próximo passo: piloto com fotos reais
- Parsing regex/fuzzy não generaliza a layouts fora do vocabulário conhecido
- Medir custo real de API em escala antes de decidir produção
