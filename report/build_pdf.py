"""Gera report/relatorio_tecnico.pdf a partir dos dados reais do benchmark.

Não depende de pandoc/weasyprint (indisponíveis no ambiente); usa reportlab
diretamente. Layout em tons de preto, cinza e branco, com formatação
inspirada na ABNT (NBR 14724): fonte Times, margens 3-2-3-2 cm, texto
principal com espaçamento 1,5, numeração de página, e títulos sempre
mantidos junto do primeiro parágrafo/tabela que os segue (sem título
"órfão" isolado no fim de uma página).

Uso:
    python -m report.build_pdf
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
VIS = ROOT / "results" / "visualizations"
EVID = ROOT / "evidencias"
OUT = ROOT / "report" / "relatorio_tecnico.pdf"

# --- Paleta em tons de preto, cinza e branco (sem azul) ----------------------
PRETO = colors.HexColor("#000000")
CINZA_ESCURO = colors.HexColor("#262626")
CINZA_MEDIO = colors.HexColor("#595959")
CINZA_CLARO = colors.HexColor("#e6e6e6")
CINZA_LINHA_ALT = colors.HexColor("#f2f2f2")
CINZA_BORDA = colors.HexColor("#bfbfbf")
BRANCO = colors.white

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    "Body9", parent=styles["Normal"], fontName="Times-Roman", fontSize=11,
    leading=16.5, textColor=CINZA_ESCURO, spaceAfter=8, alignment=4,  # justificado
))
styles.add(ParagraphStyle(
    "H1", parent=styles["Heading1"], fontName="Times-Bold", fontSize=13, leading=16,
    textColor=BRANCO, backColor=PRETO,
    spaceBefore=16, spaceAfter=10, leftIndent=6, borderPadding=(6, 6, 6, 6),
))
styles.add(ParagraphStyle(
    "H2", parent=styles["Heading2"], fontName="Times-Bold", fontSize=11.5, leading=14,
    textColor=PRETO, spaceBefore=12, spaceAfter=6,
))
styles.add(ParagraphStyle(
    "Caption", parent=styles["Normal"], fontName="Times-Italic", fontSize=9, leading=11,
    textColor=CINZA_MEDIO, spaceBefore=3, spaceAfter=12, alignment=1,
))
styles.add(ParagraphStyle(
    "Note", parent=styles["Normal"], fontName="Times-Roman", fontSize=9.5, leading=13.5,
    textColor=CINZA_ESCURO, backColor=CINZA_CLARO, borderPadding=8,
    spaceBefore=6, spaceAfter=10,
))
styles.add(ParagraphStyle(
    "CoverTitle", parent=styles["Title"], fontName="Times-Bold", fontSize=22, leading=26,
    textColor=PRETO, spaceAfter=6,
))
styles.add(ParagraphStyle(
    "CoverSubtitle", parent=styles["Normal"], fontName="Times-Roman", fontSize=13, leading=17,
    textColor=CINZA_ESCURO, spaceAfter=4, alignment=1,
))


def p(text: str) -> Paragraph:
    return Paragraph(text, styles["Body9"])


def h1(text: str) -> Paragraph:
    return Paragraph(text, styles["H1"])


def h2(text: str) -> Paragraph:
    return Paragraph(text, styles["H2"])


def note(text: str) -> Paragraph:
    return Paragraph(text, styles["Note"])


def bullets(items: list[str]) -> ListFlowable:
    return ListFlowable(
        [ListItem(p(t), leftIndent=6) for t in items],
        bulletType="bullet", start="•", leftIndent=14, spaceBefore=2, spaceAfter=8,
    )


def make_table(header: list[str], rows: list[list[str]], col_widths=None,
               font_size: int = 8) -> Table:
    data = [[Paragraph(f"<b>{c}</b>", ParagraphStyle(
        "th", parent=styles["Body9"], fontName="Times-Bold", fontSize=font_size,
        textColor=BRANCO, alignment=0)) for c in header]]
    for r in rows:
        data.append([Paragraph(str(c), ParagraphStyle(
            "td", parent=styles["Body9"], fontName="Times-Roman", fontSize=font_size,
            alignment=0)) for c in r])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), CINZA_ESCURO),
        ("GRID", (0, 0), (-1, -1), 0.4, CINZA_BORDA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), CINZA_LINHA_ALT))
    t.setStyle(TableStyle(style))
    return t


def figure(path: Path, caption: str, width: float = 15 * cm) -> list:
    if not path.exists():
        return [note(f"[figura ausente: {path.name}]")]
    img = Image(str(path))
    ratio = img.imageHeight / img.imageWidth
    img.drawWidth = width
    img.drawHeight = width * ratio
    return [img, Paragraph(caption, styles["Caption"])]


def secao(story: list, titulo: str, *primeiro_conteudo) -> None:
    """Adiciona um título de seção (H1) mantido junto do que vem logo depois,
    para que o título nunca fique sozinho no fim de uma página."""
    story.append(KeepTogether([h1(titulo), *primeiro_conteudo]))


def subsecao(story: list, titulo: str, *primeiro_conteudo) -> None:
    """Mesmo princípio de `secao`, para subtítulos (H2)."""
    story.append(KeepTogether([h2(titulo), *primeiro_conteudo]))


def _numerar_paginas(canvas, doc) -> None:
    """Numera todas as páginas exceto a capa, no canto inferior direito."""
    pagina = canvas.getPageNumber()
    if pagina == 1:
        return
    canvas.saveState()
    canvas.setFont("Times-Roman", 9)
    canvas.setFillColor(CINZA_MEDIO)
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, str(pagina))
    canvas.restoreState()


def build() -> None:
    doc = SimpleDocTemplate(
        str(OUT), pagesize=A4,
        leftMargin=3 * cm, rightMargin=2 * cm, topMargin=3 * cm, bottomMargin=2 * cm,
        title="Sprint 3: Benchmark de Leitura de Placas Industriais",
        author="Arthur Baptista dos Santos",
    )
    story = []

    # --- Capa -----------------------------------------------------------
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("SPRINT 3", styles["CoverTitle"]))
    story.append(Paragraph("Evolução do Protótipo de Leitura de Placas", styles["CoverSubtitle"]))
    story.append(Paragraph("Digital Twin de Ativos Industriais: Disciplina de Visão Computacional",
                            styles["CoverSubtitle"]))
    story.append(Spacer(1, 1.5 * cm))
    story.append(make_table(
        ["Nome", "RM"],
        [["Arthur Baptista dos Santos", "565346"],
         ["Joao Pedro", "561738"],
         ["Nelson Felix", "565603"]],
        col_widths=[10 * cm, 4 * cm], font_size=10,
    ))
    story.append(Spacer(1, 2 * cm))
    story.append(PageBreak())

    # --- 1. Continuidade -------------------------------------------------
    secao(story, "1. Continuidade real em relação às Sprints anteriores",
          p("Antes de descrever a Sprint 3, é necessário registrar com precisão o que as "
            "Sprints 1 e 2 efetivamente mostraram, pois a Sprint 3 herda diretamente essas "
            "limitações."))
    subsecao(story, "Sprint 1 (FORZY): o que o notebook realmente produziu",
              p("O relatório da Sprint 1 descreve um pipeline YOLOv8 (detecção) + "
                "Tesseract/TrOCR (OCR) sobre um dataset sintético de 1.200 imagens. A "
                "execução real do notebook sobre o conjunto de teste de <b>180 imagens</b> "
                "registrou:"))
    story.append(make_table(
        ["Métrica", "Valor real (notebook)"],
        [["Taxa de detecção (YOLOv8)", "100,0%"],
         ["Score de detecção médio", "97,2%"],
         ["Score OCR médio", "43,9%"],
         ["Acurácia global (placa 100% correta)", "0,0%"],
         ["CER: tensão/potência/frequência/grau IP/data_fab", "100% (nenhum campo correto)"],
         ["Tempo médio por imagem", "~10,2 s"]],
        col_widths=[10 * cm, 5.5 * cm],
    ))
    story.append(p("Ou seja: a <b>detecção</b> funcionou bem; já a <b>leitura de campos</b> não: "
                    "zero placas tiveram todos os campos lidos corretamente no lote de teste. "
                    "Essa é a lacuna real que a Sprint 3 ataca."))
    subsecao(story, "Sprint 2 (Digital Twin): o que foi medido",
              p("Testou apenas <b>EasyOCR</b>, sobre <b>3 imagens</b> sintéticas, com "
                "avaliação manual (inspeção visual, sem métrica de distância de edição). "
                "Resultado reportado: ~87% / ~62% / ~50% de campos corretos."))
    story.append(bullets([
        "N = 3 não é estatisticamente significativo e não separa condições de forma sistemática;",
        "a verificação era binária e manual, sem diferenciar um erro de 1 caractere de uma "
        "leitura completamente errada.",
    ]))
    subsecao(story, "O que muda na Sprint 3",
              bullets([
                  "<b>Escopo controlado</b>: avalia apenas leitura/extração de campos sobre a "
                  "placa já enquadrada. Os pesos do YOLOv8 da Sprint 1 não foram persistidos e "
                  "retreinar sem GPU não é viável no prazo; retomar a detecção fica como "
                  "próximo passo (seção 7).",
                  "<b>3 abordagens comparadas</b> sob o mesmo protocolo: Tesseract, EasyOCR e "
                  "um modelo multimodal com visão.",
                  "<b>Conjunto de teste formal</b>: 30 imagens (10 fácil / 10 médio / 10 "
                  "difícil), com gabarito gravado antes de qualquer OCR.",
                  "<b>Métricas rigorosas</b>: Exact Match Accuracy e Character-level Accuracy "
                  "(1 − CER), em vez de inspeção manual.",
              ]))

    # --- 2. Abordagens ----------------------------------------------------
    secao(story, "2. Abordagens testadas", make_table(
        ["", "A: Tesseract", "B: EasyOCR", "C: Multimodal (visão)"],
        [
            ["Tipo", "OCR clássico (LSTM)", "OCR neural (CRNN)", "LLM com visão"],
            ["Pré-processamento", "3 variantes x 2 PSM, melhor confiança", "Cinza + equalização + blur", "Nenhum: imagem direta"],
            ["Extração de campos", "Regex + fuzzy match", "Mesmo parser da A", "Modelo devolve JSON estruturado"],
            ["Motor", "pytesseract (Tesseract 5.4 local)", "easyocr.Reader(['pt','en']), CPU", "GPT-4o-mini via API (implementado); executado nesta rodada como leitura direta em sessão"],
        ],
        col_widths=[3.0 * cm, 3.7 * cm, 3.7 * cm, 3.7 * cm], font_size=7.3,
    ))
    story.append(Spacer(1, 8))
    story.append(p("<b>Por que separar OCR clássico de multimodal na arquitetura:</b> as "
                    "abordagens A e B usam o mesmo módulo de parsing (regex/fuzzy) sobre texto "
                    "bruto; isso isola a variável \"qualidade do OCR\" entre elas. A abordagem "
                    "C funde leitura e extração estruturada num único passo do modelo, diferença "
                    "arquitetural real, discutida na seção 6."))

    # --- 3. Dataset ---------------------------------------------------------
    secao(story, "3. Conjunto de teste (30 imagens) e Ground Truth",
          h2("3.1 Geração"),
          p("As 30 imagens são sintéticas, geradas programaticamente "
            "(<b>src/dataset_gen.py</b>), reaproveitando o vocabulário e o layout de "
            "placa da Sprint 1 (FORZY). O gerador é determinístico (seed fixa = 42), o "
            "que torna o experimento reprodutível e o Ground Truth exato por construção."))
    subsecao(story, "3.2 Campos avaliados (10 por imagem)",
              p("fabricante, modelo, num_serie, tensao, corrente, potencia, frequencia, "
                "grau_ip, data_fab, cod_equipamento."))
    subsecao(story, "3.3 Níveis de dificuldade (10 imagens cada)", make_table(
        ["Nível", "Iluminação", "Desgaste/sujeira", "Ângulo", "Resolução"],
        [["Fácil", "normal", "nenhum, limpa", "0°", "alta"],
         ["Médio", "normal / sombra", "leve, poeira", "10° a 18°", "média/alta"],
         ["Difícil", "reflexo/sub/superexposta/sombra", "moderado a severo, poeira/óleo", "25° a 40°", "baixa/média"]],
        col_widths=[2.3 * cm, 4.7 * cm, 5.2 * cm, 2.8 * cm, 2.5 * cm], font_size=7.5,
    ))
    story.append(Spacer(1, 8))
    subsecao(story, "3.4 Ground Truth",
              p("Gravado em <b>data/ground_truth.csv</b> antes de qualquer OCR rodar, a "
                "partir dos parâmetros usados para desenhar cada placa, nunca a partir da "
                "saída de um modelo."))

    # --- 4. Métricas ----------------------------------------------------
    secao(story, "4. Métricas", bullets([
        "<b>Exact Match Accuracy</b>: 1 se o valor normalizado for idêntico ao gabarito, 0 caso "
        "contrário. Métrica principal: um caractere errado torna o dado inutilizável na prática.",
        "<b>Character-level Accuracy (1 − CER)</b>: distância de edição de Levenshtein sobre o "
        "valor normalizado; mede o quão perto a leitura chegou mesmo sem acerto exato.",
    ]))
    story.append(PageBreak())

    # --- 5. Resultados ----------------------------------------------------
    secao(story, "5. Resultados", note(
        "<b>Nota sobre a Abordagem C:</b> sem uma OPENAI_API_KEY válida disponível no ambiente "
        "no momento da execução, a Abordagem C foi realizada como leitura multimodal direta, "
        "sem acesso prévio ao ground_truth.csv (avaliação cega mantida). A arquitetura de "
        "openai_multimodal.py permanece pronta para repetir esta etapa via API."
    ))
    subsecao(story, "5.1 Acurácia geral por abordagem (30 imagens x 10 campos = 300 avaliações)",
              make_table(
                  ["Abordagem", "Exact Match", "Char-level", "Fácil", "Médio", "Difícil"],
                  [["Multimodal (visão)", "78,0%", "79,4%", "100,0%", "100,0%", "34,0%"],
                   ["Tesseract + OpenCV", "45,7%", "45,9%", "96,0%", "40,0%", "1,0%"],
                   ["EasyOCR + OpenCV", "24,0%", "26,3%", "66,0%", "6,0%", "0,0%"]],
                  col_widths=[4.0 * cm, 2.6 * cm, 2.4 * cm, 1.9 * cm, 1.9 * cm, 1.9 * cm],
              ))
    story.append(Spacer(1, 6))
    story.append(p("Nenhuma abordagem teve falha de execução (0%) nas 30 imagens; todas as "
                    "diferenças vêm de acurácia de leitura, não de falhas técnicas."))
    story.append(KeepTogether(figure(VIS / "accuracy_comparison.png",
                                      "Figura 1: Acurácia geral (Exact Match) por abordagem.")))

    subsecao(story, "5.2 Acurácia por nível de dificuldade",
              *figure(VIS / "accuracy_by_difficulty.png",
                      "Figura 2: Acurácia por nível de dificuldade e abordagem."))
    story.append(p("Nas imagens <b>fáceis</b>, multimodal e Tesseract praticamente empatam "
                    "(100% vs. 96%). A partir do nível <b>médio</b> (inclinação 10 a 18 graus), "
                    "Tesseract cai para 40% e EasyOCR para 6%, enquanto o multimodal mantém "
                    "100%. No nível <b>difícil</b> o multimodal também degrada (de 100% para "
                    "34%), mas permanece muito acima do Tesseract (1,0%) e do EasyOCR (0,0%)."))
    story.append(p("Confirma o padrão das Sprints 1 e 2: <b>inclinação de câmera e degradação "
                    "de iluminação são o fator que mais destrói a acurácia do OCR clássico</b>, "
                    "não o ruído/desgaste isoladamente."))

    subsecao(story, "5.3 Acurácia por campo",
              *figure(VIS / "accuracy_by_field.png",
                      "Figura 3: Exact Match Accuracy por campo extraído."))
    story.append(make_table(
        ["Campo", "Tesseract", "EasyOCR", "Multimodal"],
        [["fabricante", "60,0", "26,7", "90,0"],
         ["modelo", "53,3", "33,3", "76,7"],
         ["num_serie", "56,7", "33,3", "66,7"],
         ["tensao", "36,7", "26,7", "80,0"],
         ["corrente", "30,0", "0,0", "73,3"],
         ["potencia", "36,7", "26,7", "80,0"],
         ["frequencia", "53,3", "30,0", "80,0"],
         ["grau_ip", "30,0", "6,7", "86,7"],
         ["data_fab", "56,7", "23,3", "73,3"],
         ["cod_equipamento", "43,3", "33,3", "73,3"]],
        col_widths=[4.5 * cm, 3.5 * cm, 3.5 * cm, 3.5 * cm],
    ))
    story.append(Spacer(1, 6))
    story.append(p("Para os OCRs clássicos, campos com separador (tensão, corrente, formato "
                    "X/Y) e prefixo fixo (grau_ip) são os piores: o regex depende desses "
                    "caracteres serem lidos perfeitamente. num_serie continua sendo o campo mais "
                    "difícil mesmo para o multimodal (66,7%), pois é o único alfanumérico longo "
                    "sem vocabulário fechado."))

    # --- 6. Análise de erros --------------------------------------------
    story.append(PageBreak())
    secao(story, "6. Análise de erros e limitações",
          h2("6.1 Onde cada abordagem erra"),
          note(
              "<b>Análise da causa raiz dos erros:</b> contando predições vazias vs. "
              "erradas-mas-não-vazias em results_detalhado.csv, nos casos de erro do "
              "Tesseract/EasyOCR 89% a 100% das predições por campo são <b>vazias</b> (o regex "
              "não achou nada), não um valor errado por 1 caractere. Exemplo real (medium_01, "
              "corrente esperada 45.2/26.1 A): o Tesseract devolveu \"45226414\". Os dígitos "
              "aparecem, mas ponto decimal e barra desapareceram por completo. Em hard_00, o "
              "texto bruto inteiro devolvido foi \"pO\"."
          ))
    story.append(bullets([
        "<b>Teste de sensibilidade do parsing:</b> para validar essa análise, parsing.py foi "
        "ajustado para tolerar ruído comum de OCR (separador / lido como | ou traço, "
        "abreviações kW/Hz/IP com espaço entre letras). Benchmark re-executado: "
        "<b>resultado, acurácia idêntica antes e depois</b> (Tesseract 45,7%, EasyOCR 24,0%, "
        "sem nenhuma mudança). Confirma empiricamente que o gargalo está na extração OCR sob "
        "degradação, não no parsing.",
        "<b>EasyOCR ficou sistematicamente abaixo do Tesseract</b> em quase todos os campos, "
        "o inverso do sugerido pela Sprint 2 (que só testou EasyOCR, N=3). A conclusão anterior "
        "não se sustentou sob um teste maior e mais adverso.",
        "<b>Multimodal:</b> o ponto fraco é o nível difícil (34,0%). A maioria das falhas é "
        "campo <b>vazio</b> (não lido), não um valor errado, concentrada em imagens com baixa "
        "resolução e reflexo/subexposição forte. Tende a admitir que não leu em vez de alucinar "
        "um valor.",
    ]))
    subsecao(story, "6.2 Multimodal vs. OCR clássico", make_table(
        ["Dimensão", "OCR clássico", "Multimodal"],
        [["Acurácia (fácil)", "Competitivo (96%/66%)", "Melhor (100%)"],
         ["Acurácia (médio/difícil)", "Degrada abruptamente (ate 40%, chega a 0%)", "Degrada, mas fica acima (de 100% a 34%)"],
         ["Arquitetura", "2 etapas (OCR + regex); erro pode vir de qualquer uma", "1 etapa; mais robusto, mas caixa-preta"],
         ["Execução", "Local, offline, sem custo marginal", "Depende de modelo com visão (API paga ou sessão)"],
         ["Erros típicos", "Campo vazio (texto OCR já degradado, não erro de 1 caractere)", "Campo vazio em condição extrema"]],
        col_widths=[3.6 * cm, 5.7 * cm, 5.7 * cm], font_size=7.5,
    ))
    story.append(Spacer(1, 6))
    story.append(p("<b>Conclusão desta Sprint:</b> a leitura multimodal supera claramente os "
                    "dois OCRs clássicos, principalmente por não depender de um parser regex "
                    "frágil, mas nenhuma das 3 abordagens está pronta para produção sem controle "
                    "de qualidade adicional (por exemplo, recusar leitura abaixo de um limiar de "
                    "confiança)."))

    # --- 7. Limitações ----------------------------------------------------
    secao(story, "7. Limitações e próximos passos", make_table(
        ["Limitação", "Impacto", "Próximo passo"],
        [["Sem retomada da detecção (YOLO)", "Mede leitura, não pipeline ponta a ponta", "Retreinar/persistir pesos do detector"],
         ["Dataset ainda sintético", "Degradações são aproximações de campo", "Piloto com fotos reais"],
         ["Parsing regex/fuzzy específico do layout", "Não generaliza a outros fabricantes", "NER treinado ou regras mais genéricas"],
         ["OCR perde informação sob degradação (confirmado: tolerância de regex não mudou nada)", "Teto real baixo do OCR clássico em condição adversa", "Investir em pré-processamento (super-resolução, correção de perspectiva)"],
         ["Multimodal com 1 prompt único", "Não reflete o teto de desempenho do modelo", "Testar variações de prompt e gpt-4o vs. mini"],
         ["Custo de API não mensurado", "Falta trade-off acurácia, custo e latência", "Medir custo por imagem em escala"]],
        col_widths=[4.2 * cm, 5.6 * cm, 5.6 * cm], font_size=7.3,
    ))

    # --- 8. Nota técnica ---------------------------------------------------
    secao(story, "8. Nota técnica: caminhos Unicode no Windows",
          p("O diretório do projeto contém caracteres Unicode (\"VISÃO\", \"º\"). "
            "cv2.imread/cv2.imwrite falham <b>silenciosamente</b> nesse caso no Windows: "
            "retornam None/False sem lançar exceção, o que fez uma primeira execução "
            "do gerador de dataset \"funcionar\" sem erro mas sem gravar nenhum PNG. "
            "Corrigido com wrappers dedicados (src/utils/io_utils.py) usados em "
            "dataset_gen.py, tesseract_method.py e easyocr_method.py."))

    # --- 9. Reprodutibilidade ----------------------------------------------
    secao(story, "9. Reprodutibilidade", Paragraph(
        "cd SPRINT-3 &nbsp;.&nbsp; python -m venv .venv &nbsp;.&nbsp; "
        "pip install -r requirements.txt &nbsp;.&nbsp; copy .env.example .env<br/>"
        "python -m src.dataset_gen &nbsp;.&nbsp; python -m src.run_benchmark tesseract &nbsp;.&nbsp; "
        "python -m src.run_benchmark easyocr &nbsp;.&nbsp; python -m src.run_benchmark openai_multimodal<br/>"
        "python -m src.evaluation.aggregate &nbsp;.&nbsp; pytest -q",
        ParagraphStyle("code", parent=styles["Body9"], fontName="Courier", fontSize=8,
                        alignment=0, backColor=CINZA_CLARO, borderPadding=8, leading=12),
    ))
    story.append(Spacer(1, 10))
    story.append(p("Código completo, evidências de execução (imagens comparadas lado a lado por "
                    "dificuldade) e a fonte editável da apresentação resumida (a seguir, no "
                    "Apêndice A) estão disponíveis no repositório: "
                    "<b>github.com/Arthur-Baptista-dos-Santos/plate-ocr-benchmark</b>."))

    # --- Apêndice A: Apresentação resumida da Sprint -----------------------
    story.append(PageBreak())
    secao(story, "Apêndice A: Apresentação Resumida da Sprint",
          p("Resumo executivo da Sprint 3, na mesma estrutura da apresentação distribuída em "
            "<b>presentation/apresentacao_sprint3.md</b>: evolução em relação à etapa anterior, "
            "testes realizados, acurácia alcançada e próximos passos."))

    subsecao(story, "A.1 De onde viemos", bullets([
        "<b>Sprint 1 (FORZY):</b> YOLOv8 (detecção) + Tesseract/TrOCR (leitura), 180 imagens de "
        "teste. Detecção 100%, score OCR médio 43,9%, <b>acurácia global 0,0%</b>: a leitura de "
        "campos, não a detecção, é o gargalo real.",
        "<b>Sprint 2 (Digital Twin):</b> EasyOCR isolado, 3 placas (normal/ruído/inclinada), "
        "~87%/~62%/~50%, mas avaliação manual, N=3, sem métrica formal.",
    ]))
    subsecao(story, "A.2 O que muda nesta Sprint", bullets([
        "Escopo controlado: só leitura/extração de campos (sem retomar detecção, pois os pesos "
        "do YOLO não foram persistidos).",
        "3 abordagens sob o mesmo protocolo: Tesseract, EasyOCR, modelo multimodal com visão.",
        "30 imagens de teste (10 fácil / 10 médio / 10 difícil), gabarito gravado antes do OCR.",
        "Métricas formais: Exact Match Accuracy e Character-level Accuracy (CER).",
    ]))
    subsecao(story, "A.3 Resultados: acurácia geral", make_table(
        ["Abordagem", "Exact Match", "Character-level", "Fácil", "Médio", "Difícil"],
        [["Multimodal (visão)", "78,0%", "79,4%", "100%", "100%", "34%"],
         ["Tesseract", "45,7%", "45,9%", "96%", "40%", "1%"],
         ["EasyOCR", "24,0%", "26,3%", "66%", "6%", "0%"]],
        col_widths=[4.0 * cm, 2.6 * cm, 2.8 * cm, 1.8 * cm, 1.8 * cm, 1.8 * cm],
    ))
    story.append(Spacer(1, 6))
    story.append(p("30 imagens x 10 campos = 300 avaliações por abordagem. 0% de falha de "
                    "execução em todas as abordagens: toda diferença é acurácia de leitura."))
    subsecao(story, "A.4 Multimodal vs. OCR clássico: o que observamos", bullets([
        "Multimodal vence claramente nos níveis fácil/médio (100%/100% contra até 40% do OCR "
        "clássico) e ainda lidera no difícil (34% contra até 1%), mas degrada bastante lá "
        "também: nenhuma abordagem está pronta para produção sem um limiar de confiança.",
        "Quando erra em condição extrema, o multimodal tende a devolver campo vazio (admite "
        "que não leu) em vez de um valor errado, o que é mais seguro para popular um banco de "
        "ativos.",
        "EasyOCR ficou sistematicamente atrás do Tesseract nesta rodada, o que contradiz a "
        "conclusão da Sprint 2 (só EasyOCR havia sido testado lá, com N=3).",
        "Trade-off ainda em aberto: a Abordagem C rodou como leitura direta em sessão, não via "
        "API; custo e latência reais de API ficam como próximo passo.",
    ]))
    subsecao(story, "A.5 Tentativa de melhoria do parsing (resultado negativo, mas real)", bullets([
        "Hipótese inicial: o erro do OCR clássico era 1 caractere errado no separador; o regex "
        "foi tornado mais tolerante.",
        "Investigação em results_detalhado.csv: 89% a 100% dos erros por campo são predições "
        "vazias, não valores errados; o regex nunca chegou a rodar sobre texto útil.",
        "Regex melhorado e benchmark re-executado: acurácia idêntica antes e depois (45,7% / "
        "24,0%).",
        "Conclusão: o gargalo é a extração OCR sob degradação, não o parsing.",
    ]))
    subsecao(story, "A.6 Limitações e próximos passos", bullets([
        "Sem pipeline ponta a ponta (falta retomar a detecção da placa na cena).",
        "Dataset ainda sintético: próximo passo é um piloto com fotos reais.",
        "Parsing regex/fuzzy não generaliza a layouts fora do vocabulário conhecido.",
        "Medir custo real de API em escala antes de decidir produção.",
    ]))

    doc.build(story, onFirstPage=_numerar_paginas, onLaterPages=_numerar_paginas)
    print(f"PDF gerado em {OUT}")


if __name__ == "__main__":
    build()
