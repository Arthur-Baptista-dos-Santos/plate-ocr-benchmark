"""Configuração centralizada de caminhos e parâmetros do experimento da Sprint 3."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
TEST_DIR = DATA_DIR / "test"
GROUND_TRUTH_CSV = DATA_DIR / "ground_truth.csv"

RESULTS_DIR = PROJECT_ROOT / "results"
RAW_RESULTS_DIR = RESULTS_DIR / "raw"
METRICS_DIR = RESULTS_DIR / "metrics"
VIS_DIR = RESULTS_DIR / "visualizations"

DIFFICULTIES = ("easy", "medium", "hard")
N_IMAGES_PER_DIFFICULTY = 10
N_TOTAL_IMAGES = N_IMAGES_PER_DIFFICULTY * len(DIFFICULTIES)

RANDOM_SEED = 42

# Campos avaliados na tarefa de extração (mesmo schema da Sprint 1 - FORZY).
CAMPOS_AVALIADOS = (
    "fabricante",
    "modelo",
    "num_serie",
    "tensao",
    "corrente",
    "potencia",
    "frequencia",
    "grau_ip",
    "data_fab",
    "cod_equipamento",
)

METODOS = ("tesseract", "easyocr", "openai_multimodal")

OPENAI_MODEL = "gpt-4o-mini"
