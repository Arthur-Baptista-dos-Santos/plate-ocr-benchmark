"""Abordagem B: OpenCV (pré-processamento) + EasyOCR (rede neural) + regex.

Reaproveita o motor validado na Sprint 2 (Digital Twin), substituindo
PaddleOCR (descartado por atrito de instalação no Windows — ver README) por
um OCR neural já testado, usando o MESMO parser de campos da Abordagem A
para isolar a variável "qualidade do OCR".
"""

import time
from pathlib import Path

import cv2
import easyocr

from src.methods.base import ExtractionResult
from src.methods.parsing import parse_campos_placa
from src.utils.io_utils import imread_unicode

_reader: easyocr.Reader | None = None


def _get_reader() -> easyocr.Reader:
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(["pt", "en"], gpu=False, verbose=False)
    return _reader


def _preprocessar(img_bgr) -> object:
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    equalizada = cv2.equalizeHist(gray)
    return cv2.GaussianBlur(equalizada, (3, 3), 0)


def extrair_campos(image_path: Path, image_id: str) -> ExtractionResult:
    t0 = time.perf_counter()
    img = imread_unicode(image_path)
    if img is None:
        return ExtractionResult(
            image_id=image_id, metodo="easyocr", tempo_ms=0.0,
            texto_bruto="", erro="imagem_nao_encontrada",
        )

    reader = _get_reader()
    img_proc = _preprocessar(img)
    linhas = reader.readtext(img_proc, detail=0, paragraph=True)
    texto = " ".join(linhas)
    campos = parse_campos_placa(texto)
    tempo_ms = (time.perf_counter() - t0) * 1000

    return ExtractionResult(
        image_id=image_id, metodo="easyocr", tempo_ms=round(tempo_ms, 1),
        texto_bruto=texto, campos=campos,
    )
