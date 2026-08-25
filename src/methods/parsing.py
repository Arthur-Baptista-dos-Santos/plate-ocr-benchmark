"""Parsing estruturado compartilhado pelas abordagens A (Tesseract) e B
(EasyOCR): as duas recebem texto bruto de motores de OCR diferentes, mas
usam exatamente a mesma lógica de extração de campos a partir daqui. Isso
garante que diferenças de acurácia venham do OCR, não do parsing.

A abordagem C (multimodal) NÃO usa este módulo — o modelo extrai os campos
estruturados diretamente da imagem, sem uma etapa de regex separada. Essa é
uma diferença arquitetural real entre as abordagens, discutida no relatório.
"""

import re

from rapidfuzz import fuzz

from src.dataset_gen import FABRICANTES, MODELOS

_RE_NUM_SERIE = re.compile(r"SN[\s\-]?(\d{4})[\s\-]?(\d{4,6})", re.IGNORECASE)
_RE_COD_EQUIP = re.compile(r"EQ[\s\-]?(\d{4})[\s\-]?(\d{3,4})", re.IGNORECASE)
_RE_TENSAO = re.compile(r"(\d{2,3})\s*[/\\]\s*(\d{3,4})\s*V", re.IGNORECASE)
_RE_CORRENTE = re.compile(r"(\d{1,3}[.,]\d{1,2})\s*[/\\]\s*(\d{1,3}[.,]\d{1,2})\s*A", re.IGNORECASE)
_RE_POTENCIA = re.compile(r"(\d+[.,]?\d*)\s*kW", re.IGNORECASE)
_RE_FREQUENCIA = re.compile(r"\b(50|60)\s*Hz\b", re.IGNORECASE)
_RE_GRAU_IP = re.compile(r"IP\s*[\.\s]?(\d{2})", re.IGNORECASE)
_RE_DATA_FAB = re.compile(r"\b(0?[1-9]|1[0-2])\s*[/\\]\s*(20\d{2})\b")

LIMIAR_FUZZY_VOCABULARIO = 70


def _melhor_correspondencia(texto: str, vocabulario: list[str]) -> str:
    """Encontra o item do vocabulário mais próximo do texto OCR (fuzzy match).

    Usado para fabricante/modelo, que são campos de texto livre e não seguem
    um padrão regex — a alternativa realista de parsing é casar contra um
    catálogo conhecido, como sistemas de gestão de ativos fazem na prática.
    """
    melhor_item, melhor_score = "", 0.0
    for item in vocabulario:
        score = fuzz.partial_ratio(item.upper(), texto.upper())
        if score > melhor_score:
            melhor_item, melhor_score = item, score
    return melhor_item if melhor_score >= LIMIAR_FUZZY_VOCABULARIO else ""


def parse_campos_placa(texto_bruto: str) -> dict[str, str]:
    """Extrai os 10 campos avaliados a partir do texto bruto de um OCR."""
    campos: dict[str, str] = {}

    if m := _RE_NUM_SERIE.search(texto_bruto):
        campos["num_serie"] = f"SN-{m.group(1)}-{m.group(2)}"
    if m := _RE_COD_EQUIP.search(texto_bruto):
        campos["cod_equipamento"] = f"EQ-{m.group(1)}-{m.group(2)}"
    if m := _RE_TENSAO.search(texto_bruto):
        campos["tensao"] = f"{m.group(1)}/{m.group(2)} V"
    if m := _RE_CORRENTE.search(texto_bruto):
        campos["corrente"] = f"{m.group(1)}/{m.group(2)} A"
    if m := _RE_POTENCIA.search(texto_bruto):
        campos["potencia"] = f"{m.group(1)} kW"
    if m := _RE_FREQUENCIA.search(texto_bruto):
        campos["frequencia"] = f"{m.group(1)} Hz"
    if m := _RE_GRAU_IP.search(texto_bruto):
        campos["grau_ip"] = f"IP{m.group(1)}"
    if m := _RE_DATA_FAB.search(texto_bruto):
        campos["data_fab"] = f"{int(m.group(1)):02d}/{m.group(2)}"

    campos["fabricante"] = _melhor_correspondencia(texto_bruto, FABRICANTES)
    campos["modelo"] = _melhor_correspondencia(texto_bruto, MODELOS)

    return campos
