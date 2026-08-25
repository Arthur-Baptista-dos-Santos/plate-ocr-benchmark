"""Executa uma abordagem (tesseract | easyocr | openai_multimodal) sobre as
mesmas 30 imagens do Ground Truth e salva os resultados brutos em
``results/raw/<metodo>.json``.

Uso:
    python -m src.run_benchmark tesseract
    python -m src.run_benchmark easyocr
    python -m src.run_benchmark openai_multimodal   # requer OPENAI_API_KEY
"""

import json
import sys
from pathlib import Path

import pandas as pd

from src.utils.config import GROUND_TRUTH_CSV, PROJECT_ROOT, RAW_RESULTS_DIR


def _carregar_metodo(nome: str):
    if nome == "tesseract":
        from src.methods.tesseract_method import extrair_campos
        return extrair_campos
    if nome == "easyocr":
        from src.methods.easyocr_method import extrair_campos
        return extrair_campos
    if nome == "openai_multimodal":
        from src.methods.openai_multimodal import extrair_campos
        return extrair_campos
    raise ValueError(
        f"Método desconhecido: {nome}. Use 'tesseract', 'easyocr' ou 'openai_multimodal'."
    )


def executar(nome_metodo: str) -> Path:
    extrair_campos = _carregar_metodo(nome_metodo)
    gt = pd.read_csv(GROUND_TRUTH_CSV)

    resultados = []
    for _, linha in gt.iterrows():
        image_path = PROJECT_ROOT / linha["image_path"]
        resultado = extrair_campos(image_path, linha["image_id"])
        resultados.append(resultado.to_dict())
        status = "erro" if resultado.erro else "ok"
        print(f"[{nome_metodo}] {linha['image_id']} ({status}) — {resultado.tempo_ms:.0f} ms")

    RAW_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_RESULTS_DIR / f"{nome_metodo}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print(f"\n✅ {len(resultados)} imagens processadas. Resultados em {out_path}")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python -m src.run_benchmark <tesseract|easyocr>")
        sys.exit(1)
    executar(sys.argv[1])
