"""Abordagem C: modelo de linguagem multimodal (OpenAI GPT-4o-mini, visão).

Diferente das abordagens A (Tesseract) e B (EasyOCR), aqui não há uma etapa
de OCR seguida de parsing por regex/fuzzy match (``src/methods/parsing.py``):
o modelo recebe a imagem da placa inteira e é instruído a devolver
diretamente um JSON com os 10 campos avaliados. É uma diferença
arquitetural real entre as abordagens, e é discutida no relatório — o
modelo multimodal une "leitura" e "extração estruturada" em um único passo.

A chave da API é lida exclusivamente da variável de ambiente
``OPENAI_API_KEY`` (nunca hardcoded neste arquivo ou em qualquer outro
artefato do projeto).

Uso:
    export OPENAI_API_KEY=...        (Linux/Git Bash)
    $env:OPENAI_API_KEY = "..."      (PowerShell)
    python -m src.run_benchmark openai_multimodal
"""

import base64
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from src.methods.base import ExtractionResult
from src.utils.config import CAMPOS_AVALIADOS, OPENAI_MODEL

load_dotenv()

_PROMPT_SISTEMA = (
    "Você é um sistema de extração de dados de placas de identificação de "
    "motores elétricos industriais. Leia a imagem da placa e devolva "
    "APENAS um objeto JSON, sem texto adicional, com exatamente estas "
    "chaves: " + ", ".join(CAMPOS_AVALIADOS) + ". "
    "Se um campo não estiver legível ou não existir na placa, use string "
    "vazia \"\" para ele. Não invente valores. Preserve o formato original "
    "do texto da placa (ex.: '220/380 V', 'SN-2020-21773', 'IP54')."
)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY não definida no ambiente. Defina a variável "
                "antes de rodar a abordagem multimodal."
            )
        _client = OpenAI(api_key=api_key)
    return _client


def _image_to_data_url(image_path: Path) -> str:
    raw = image_path.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:image/png;base64,{b64}"


def extrair_campos(image_path: Path, image_id: str) -> ExtractionResult:
    t0 = time.perf_counter()
    try:
        client = _get_client()
        data_url = _image_to_data_url(image_path)

        resposta = client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _PROMPT_SISTEMA},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extraia os campos desta placa:"},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
        )
        texto_bruto = resposta.choices[0].message.content or "{}"
        campos_json = json.loads(texto_bruto)
        campos = {k: str(campos_json.get(k, "") or "") for k in CAMPOS_AVALIADOS}
        tempo_ms = (time.perf_counter() - t0) * 1000

        return ExtractionResult(
            image_id=image_id,
            metodo="openai_multimodal",
            tempo_ms=round(tempo_ms, 1),
            texto_bruto=texto_bruto,
            campos=campos,
        )
    except Exception as exc:  # noqa: BLE001 — precisa capturar qualquer falha de API/rede
        tempo_ms = (time.perf_counter() - t0) * 1000
        return ExtractionResult(
            image_id=image_id,
            metodo="openai_multimodal",
            tempo_ms=round(tempo_ms, 1),
            texto_bruto="",
            erro=str(exc),
        )
