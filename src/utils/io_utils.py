"""Leitura/escrita de imagens seguras para caminhos com Unicode no Windows.

``cv2.imread``/``cv2.imwrite`` usam ``fopen`` internamente e falham
silenciosamente (retornam ``None``/``False``, sem exceção) quando o caminho
contém caracteres não-ASCII — como o nome deste projeto ("VISÃO...2º SEM").
As funções abaixo contornam isso via ``imdecode``/``imencode`` + I/O padrão
do Python, que lida corretamente com Unicode no Windows.
"""

from pathlib import Path

import cv2
import numpy as np


def imread_unicode(path: Path | str) -> np.ndarray | None:
    """Equivalente a ``cv2.imread`` que funciona com caminhos Unicode."""
    data = np.fromfile(str(path), dtype=np.uint8)
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def imwrite_unicode(path: Path | str, img: np.ndarray) -> bool:
    """Equivalente a ``cv2.imwrite`` que funciona com caminhos Unicode."""
    path = Path(path)
    ok, buf = cv2.imencode(path.suffix, img)
    if not ok:
        return False
    buf.tofile(str(path))
    return True
