"""Geração do conjunto de teste (30 imagens) e do Ground Truth da Sprint 3.

Reaproveita o gerador de placas sintéticas real da Sprint 1 (projeto FORZY:
``FORZY_Relatorio_Sprint1``/``Visão_Computacional_SPRINT1_FORZY_FIXED.ipynb``),
mesmo schema de campos e mesmas listas de fabricantes/modelos/valores.

Diferença deliberada em relação à Sprint 1: aqui a placa NÃO é inserida em uma
cena de fundo maior (não há etapa de detecção YOLO no escopo desta Sprint,
pois os pesos treinados não foram persistidos e retreinar sem GPU é inviável
no prazo). O experimento controlado desta Sprint isola exatamente a variável
que a Sprint 1 mediu como gargalo real (leitura/extração de campos, 0% de
acurácia global no lote de teste), comparando 3 abordagens de LEITURA sobre a
placa já recortada, não de detecção.

O Ground Truth é gravado em CSV ANTES de qualquer execução de OCR, a partir
dos parâmetros usados para desenhar cada placa (nunca a partir do resultado
de um modelo).
"""

import csv
import random
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from src.utils.config import (
    DIFFICULTIES,
    GROUND_TRUTH_CSV,
    N_IMAGES_PER_DIFFICULTY,
    RANDOM_SEED,
    TEST_DIR,
)
from src.utils.io_utils import imwrite_unicode

# --- Vocabulário reaproveitado da Sprint 1 (FORZY) ---------------------------
FABRICANTES = [
    "WEG Equipamentos", "ABB Ltda", "Siemens SA", "Schneider Electric",
    "Weg Motores", "Voith Turbo", "Grundfos", "Danfoss Brasil",
    "Parker Hannifin", "Bosch Rexroth",
]
MODELOS = [
    "W22 160M", "M2BAX 132", "1LE1 112", "ALTIVAR 31",
    "IE3 200L", "WG20 3F", "CM10-3", "FC102-22kW",
    "VPL-B0752F", "INDRAMAT",
]
TENSOES = ["220/380 V", "380/660 V", "440/760 V", "127/220 V", "208/360 V"]
CORRENTES = ["28.4/16.4 A", "45.2/26.1 A", "12.8/7.4 A", "68.0/39.3 A", "9.2/5.3 A"]
POTENCIAS = ["7.5 kW", "11 kW", "15 kW", "22 kW", "37 kW", "4 kW", "2.2 kW", "55 kW"]
GRAUS_IP = ["IP54", "IP55", "IP65", "IP66", "IP44"]
FREQUENCIAS = ["50 Hz", "60 Hz"]

PALETAS = [
    ((220, 220, 210), (20, 20, 20)),
    ((200, 200, 195), (10, 10, 80)),
    ((240, 240, 230), (80, 0, 0)),
    ((180, 180, 170), (20, 20, 20)),
    ((210, 230, 210), (0, 60, 0)),
]

PLATE_W, PLATE_H = 640, 400


@dataclass(frozen=True)
class DegradationConfig:
    """Parâmetros de degradação aplicados a uma placa (documentados no CSV)."""

    iluminacao: str
    desgaste: str
    sujeira: str
    angulo: int
    resolucao: str


# Espaço de parâmetros permitido por nível de dificuldade. Critérios adaptados
# do enunciado: FÁCIL = alta resolução, boa iluminação, texto frontal, baixo
# ruído; MÉDIO = perspectiva leve, iluminação variável, pequeno desfoque;
# DIFÍCIL = baixa iluminação/reflexo, perspectiva forte, baixa resolução,
# ruído/desgaste.
DIFFICULTY_SPACE = {
    "easy": {
        "iluminacao": ["normal"],
        "desgaste": ["nenhum"],
        "sujeira": ["limpa"],
        "angulo": [0],
        "resolucao": ["alta"],
    },
    "medium": {
        "iluminacao": ["normal", "sombra"],
        "desgaste": ["leve"],
        "sujeira": ["limpa", "poeira"],
        "angulo": [10, -10, 15, -15, 18],
        "resolucao": ["media", "alta"],
    },
    "hard": {
        "iluminacao": ["reflexo", "subexposta", "superexposta", "sombra"],
        "desgaste": ["moderado", "severo"],
        "sujeira": ["poeira", "oleo"],
        "angulo": [25, -25, 30, -30, 40, -40],
        "resolucao": ["baixa", "media"],
    },
}


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def gerar_amostra_dados(rng: random.Random) -> dict:
    """Gera um registro fictício de dados de placa (Ground Truth)."""
    ano = rng.randint(2010, 2024)
    mes = rng.randint(1, 12)
    return {
        "fabricante": rng.choice(FABRICANTES),
        "modelo": rng.choice(MODELOS),
        "num_serie": f"SN-{ano}-{rng.randint(10000, 99999)}",
        "tensao": rng.choice(TENSOES),
        "corrente": rng.choice(CORRENTES),
        "potencia": rng.choice(POTENCIAS),
        "frequencia": rng.choice(FREQUENCIAS),
        "grau_ip": rng.choice(GRAUS_IP),
        "data_fab": f"{mes:02d}/{ano}",
        "cod_equipamento": f"EQ-{ano}-{rng.randint(1000, 9999)}",
    }


def desenhar_placa(dados: dict, rng: random.Random) -> Image.Image:
    """Desenha a placa sintética (layout reaproveitado da Sprint 1)."""
    cor_fundo, cor_texto = rng.choice(PALETAS)
    img = Image.new("RGB", (PLATE_W, PLATE_H), cor_fundo)
    draw = ImageDraw.Draw(img)

    borda = 8
    draw.rectangle([borda, borda, PLATE_W - borda, PLATE_H - borda], outline=cor_texto, width=3)
    draw.rectangle([borda, borda, PLATE_W - borda, 70], fill=cor_texto)
    draw.text(
        (PLATE_W // 2, 38), dados["fabricante"], fill=cor_fundo, anchor="mm", font=_load_font(22)
    )

    campos = [
        ("MODELO", dados["modelo"]),
        ("N SERIE", dados["num_serie"]),
        ("TENSAO", dados["tensao"]),
        ("CORRENTE", dados["corrente"]),
        ("POTENCIA", dados["potencia"]),
        ("FREQUENCIA", dados["frequencia"]),
        ("GRAU IP", dados["grau_ip"]),
        ("FAB.", dados["data_fab"]),
        ("COD. EQ.", dados["cod_equipamento"]),
    ]
    font_label = _load_font(13)
    font_valor = _load_font(17)

    col_w = (PLATE_W - 2 * borda) // 2
    n_rows = 5
    row_h = (PLATE_H - 80 - borda) // n_rows
    x0, y0 = borda, 80

    for i, (label, valor) in enumerate(campos):
        col, row = i % 2, i // 2
        x, y = x0 + col * col_w, y0 + row * row_h
        draw.rectangle([x, y, x + col_w, y + row_h], outline=cor_texto, width=1)
        draw.text((x + 6, y + 4), label, fill=cor_texto, font=font_label)
        draw.text((x + col_w // 2, y + row_h // 2 + 6), str(valor), fill=cor_texto,
                   anchor="mm", font=font_valor)

    return img


def aplicar_degradacao(img_pil: Image.Image, cfg: DegradationConfig, rng: random.Random) -> np.ndarray:
    """Aplica degradações controladas diretamente sobre a placa recortada.

    Adaptado da etapa de augmentation da Sprint 1, removendo a etapa 6
    (inserção em cena de fundo maior): aqui a saída permanece do tamanho da
    placa, pois o experimento avalia apenas leitura, não detecção.
    """
    img = np.array(img_pil)

    if cfg.iluminacao == "subexposta":
        img = (img * 0.45).astype(np.uint8)
    elif cfg.iluminacao == "superexposta":
        img = np.clip(img.astype(np.int32) + 75, 0, 255).astype(np.uint8)
    elif cfg.iluminacao == "reflexo":
        cx, cy = rng.randint(100, img.shape[1] - 100), rng.randint(50, img.shape[0] - 50)
        mask = np.zeros(img.shape[:2], np.float32)
        cv2.ellipse(mask, (cx, cy), (110, 55), rng.randint(0, 180), 0, 360, 1.0, -1)
        mask = cv2.GaussianBlur(mask, (81, 81), 0)
        img = np.clip(img + (mask[:, :, None] * 170).astype(np.int32), 0, 255).astype(np.uint8)
    elif cfg.iluminacao == "sombra":
        x_split = rng.randint(img.shape[1] // 4, 3 * img.shape[1] // 4)
        img[:, :x_split] = (img[:, :x_split] * 0.55).astype(np.uint8)

    if cfg.desgaste == "leve":
        img = np.clip(img + np.random.default_rng(rng.randint(0, 2**31)).normal(0, 8, img.shape), 0, 255).astype(np.uint8)
    elif cfg.desgaste == "moderado":
        img = np.clip(img + np.random.default_rng(rng.randint(0, 2**31)).normal(0, 18, img.shape), 0, 255).astype(np.uint8)
        for _ in range(6):
            x1, y1 = rng.randint(0, img.shape[1]), rng.randint(0, img.shape[0])
            x2, y2 = x1 + rng.randint(-70, 70), y1 + rng.randint(-35, 35)
            cv2.line(img, (x1, y1), (x2, y2), (180, 180, 180), 1)
    elif cfg.desgaste == "severo":
        img = np.clip(img + np.random.default_rng(rng.randint(0, 2**31)).normal(0, 35, img.shape), 0, 255).astype(np.uint8)
        for _ in range(4):
            cx, cy = rng.randint(50, img.shape[1] - 50), rng.randint(50, img.shape[0] - 50)
            cv2.circle(img, (cx, cy), rng.randint(12, 32), (100, 80, 60), -1)
        img = cv2.GaussianBlur(img, (3, 3), 0)

    if cfg.sujeira == "poeira":
        poeira = np.random.default_rng(rng.randint(0, 2**31)).integers(0, 28, img.shape[:2], dtype=np.uint8)
        img[:, :, 0] = np.clip(img[:, :, 0].astype(np.int32) + poeira // 2, 0, 255).astype(np.uint8)
    elif cfg.sujeira == "oleo":
        for _ in range(3):
            cx, cy = rng.randint(0, img.shape[1]), rng.randint(0, img.shape[0])
            ov = np.zeros_like(img)
            cv2.circle(ov, (cx, cy), rng.randint(18, 55), (30, 25, 10), -1)
            img = cv2.addWeighted(img, 0.62, ov, 0.38, 0)

    if cfg.angulo != 0:
        h, w = img.shape[:2]
        shift = int(h * np.tan(np.radians(abs(cfg.angulo))) * 0.5)
        src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
        if cfg.angulo > 0:
            dst = np.float32([[shift, 0], [w, 0], [w - shift, h], [0, h]])
        else:
            dst = np.float32([[0, 0], [w - shift, 0], [w, h], [shift, h]])
        M = cv2.getPerspectiveTransform(src, dst)
        img = cv2.warpPerspective(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)

    if cfg.resolucao == "media":
        h, w = img.shape[:2]
        img = cv2.resize(cv2.resize(img, (w // 2, h // 2)), (w, h))
    elif cfg.resolucao == "baixa":
        h, w = img.shape[:2]
        img = cv2.resize(cv2.resize(img, (w // 4, h // 4)), (w, h))

    return img


def _sortear_config(difficulty: str, rng: random.Random) -> DegradationConfig:
    espaco = DIFFICULTY_SPACE[difficulty]
    return DegradationConfig(
        iluminacao=rng.choice(espaco["iluminacao"]),
        desgaste=rng.choice(espaco["desgaste"]),
        sujeira=rng.choice(espaco["sujeira"]),
        angulo=rng.choice(espaco["angulo"]),
        resolucao=rng.choice(espaco["resolucao"]),
    )


def gerar_dataset_teste(seed: int = RANDOM_SEED, out_dir: Path = TEST_DIR,
                         gt_csv: Path = GROUND_TRUTH_CSV) -> list[dict]:
    """Gera as 30 imagens de teste (10/10/10) e grava o Ground Truth em CSV.

    O CSV é gravado ANTES de qualquer execução de OCR: a coluna
    ``ground_truth_*`` vem exclusivamente dos parâmetros usados para desenhar
    a placa, nunca do resultado de um modelo.
    """
    rng = random.Random(seed)
    linhas: list[dict] = []

    for difficulty in DIFFICULTIES:
        for idx in range(N_IMAGES_PER_DIFFICULTY):
            image_id = f"{difficulty}_{idx:02d}"
            dados = gerar_amostra_dados(rng)
            cfg = _sortear_config(difficulty, rng)

            placa_pil = desenhar_placa(dados, rng)
            img_np = aplicar_degradacao(placa_pil, cfg, rng)

            img_path = out_dir / difficulty / f"{image_id}.png"
            img_path.parent.mkdir(parents=True, exist_ok=True)
            if not imwrite_unicode(img_path, cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)):
                raise OSError(f"Falha ao gravar imagem em {img_path}")

            linha = {
                "image_id": image_id,
                "image_path": str(img_path.relative_to(out_dir.parent.parent)),
                "difficulty": difficulty,
                **dados,
                **{f"cfg_{k}": v for k, v in asdict(cfg).items()},
            }
            linhas.append(linha)

    gt_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(gt_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
        writer.writeheader()
        writer.writerows(linhas)

    return linhas


if __name__ == "__main__":
    registros = gerar_dataset_teste()
    print(f"Dataset gerado: {len(registros)} imagens em {TEST_DIR}")
    print(f"Ground Truth salvo em {GROUND_TRUTH_CSV}")
