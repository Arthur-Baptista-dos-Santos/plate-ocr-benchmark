"""Abordagem A: OpenCV (pré-processamento) + Tesseract OCR + regex.

Reaproveita a lógica multi-estratégia real da Sprint 1 (FORZY): 3
pré-processamentos (original, CLAHE, binarizado) x 2 modos PSM do Tesseract,
mantendo o resultado de maior confiança média.
"""

import os
import time
from pathlib import Path

import cv2
import numpy as np
import pytesseract

from src.methods.base import ExtractionResult
from src.methods.parsing import parse_campos_placa
from src.utils.io_utils import imread_unicode

_DEFAULT_TESSERACT_WIN = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.name == "nt" and os.path.exists(_DEFAULT_TESSERACT_WIN):
    pytesseract.pytesseract.tesseract_cmd = _DEFAULT_TESSERACT_WIN

TESS_BLOCK = "--oem 3 --psm 6 -l por+eng"
TESS_SPARSE = "--oem 3 --psm 11 -l por+eng"
MIN_WIDTH_UPSCALE = 800


def _upscale(img: np.ndarray, min_width: int = MIN_WIDTH_UPSCALE) -> np.ndarray:
    h, w = img.shape[:2]
    if w >= min_width:
        return img
    escala = min_width / w
    return cv2.resize(img, (int(w * escala), int(h * escala)), interpolation=cv2.INTER_CUBIC)


def _extrair_texto(img_bgr: np.ndarray) -> tuple[str, float]:
    img_bgr = _upscale(img_bgr)
    melhor_palavras: list[str] = []
    melhor_confianca = -1.0

    for estrategia in ("original", "clahe", "binaria"):
        if estrategia == "original":
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        elif estrategia == "clahe":
            lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            lab_eq = cv2.merge([clahe.apply(l), a, b])
            gray = cv2.cvtColor(cv2.cvtColor(lab_eq, cv2.COLOR_LAB2BGR), cv2.COLOR_BGR2GRAY)
        else:
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            gray = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10
            )

        for cfg in (TESS_BLOCK, TESS_SPARSE):
            data = pytesseract.image_to_data(gray, config=cfg, output_type=pytesseract.Output.DICT)
            palavras, confs = [], []
            for texto, conf in zip(data["text"], data["conf"]):
                conf_i = int(conf)
                if texto.strip() and conf_i > 0:
                    palavras.append(texto.strip())
                    confs.append(conf_i)
            conf_media = float(np.mean(confs)) if confs else 0.0
            if conf_media > melhor_confianca:
                melhor_palavras, melhor_confianca = palavras, conf_media

    return " ".join(melhor_palavras), max(melhor_confianca, 0.0)


def extrair_campos(image_path: Path, image_id: str) -> ExtractionResult:
    t0 = time.perf_counter()
    img = imread_unicode(image_path)
    if img is None:
        return ExtractionResult(
            image_id=image_id, metodo="tesseract", tempo_ms=0.0,
            texto_bruto="", erro="imagem_nao_encontrada",
        )

    texto, _confianca = _extrair_texto(img)
    campos = parse_campos_placa(texto)
    tempo_ms = (time.perf_counter() - t0) * 1000

    return ExtractionResult(
        image_id=image_id, metodo="tesseract", tempo_ms=round(tempo_ms, 1),
        texto_bruto=texto, campos=campos,
    )
