"""Agrega os resultados brutos das 3 abordagens contra o Ground Truth,
calcula as métricas (Exact Match Accuracy e Character-level Accuracy) e
gera os artefatos de evidência: CSVs detalhados, resumo do benchmark e
gráficos comparativos.

Uso:
    python -m src.evaluation.aggregate
"""

import json
import math

import matplotlib.pyplot as plt
import pandas as pd


def _sem_nan(registro: dict) -> dict:
    """Substitui float('nan') por None (pandas não representa None em
    colunas float64, então .where()/.replace() não bastam; precisa ser
    feito após to_dict(), campo a campo)."""
    return {
        k: (None if isinstance(v, float) and math.isnan(v) else v)
        for k, v in registro.items()
    }

from src.evaluation.metrics import avaliar_campo
from src.utils.config import (
    CAMPOS_AVALIADOS,
    GROUND_TRUTH_CSV,
    METRICS_DIR,
    RAW_RESULTS_DIR,
    VIS_DIR,
)


def _carregar_resultados_metodo(nome_metodo: str) -> dict[str, dict]:
    path = RAW_RESULTS_DIR / f"{nome_metodo}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Resultados de '{nome_metodo}' não encontrados em {path}. "
            "Rode o benchmark dessa abordagem antes de agregar."
        )
    with open(path, encoding="utf-8") as f:
        registros = json.load(f)
    return {r["image_id"]: r for r in registros}


def montar_dataframe_detalhado(metodos: list[str]) -> pd.DataFrame:
    gt = pd.read_csv(GROUND_TRUTH_CSV).set_index("image_id")
    resultados_por_metodo = {m: _carregar_resultados_metodo(m) for m in metodos}

    linhas = []
    for image_id, gt_row in gt.iterrows():
        for metodo in metodos:
            resultado = resultados_por_metodo[metodo].get(image_id)
            campos_preditos = resultado.get("campos", {}) if resultado else {}
            teve_erro = bool(resultado.get("erro")) if resultado else True
            tempo_ms = resultado.get("tempo_ms") if resultado else None

            for campo in CAMPOS_AVALIADOS:
                valor_esperado = gt_row[campo]
                valor_predito = campos_preditos.get(campo, "")
                avaliado = avaliar_campo(
                    image_id=image_id,
                    difficulty=gt_row["difficulty"],
                    metodo=metodo,
                    campo=campo,
                    valor_predito=valor_predito,
                    valor_esperado=valor_esperado,
                )
                linha = {
                    **avaliado.__dict__,
                    "falha_execucao": teve_erro,
                    "tempo_ms": tempo_ms,
                }
                linhas.append(linha)

    return pd.DataFrame(linhas)


def calcular_resumo(df_detalhado: pd.DataFrame) -> pd.DataFrame:
    n_campos_por_imagem = len(CAMPOS_AVALIADOS)
    linhas_resumo = []

    for metodo, grupo in df_detalhado.groupby("metodo"):
        n_imagens = grupo["image_id"].nunique()
        n_campos_total = len(grupo)
        acertos = int(grupo["acerto_exato"].sum())
        tempo_medio = grupo.drop_duplicates("image_id")["tempo_ms"].mean()

        resumo = {
            "metodo": metodo,
            "n_imagens": n_imagens,
            "n_campos_avaliados": n_campos_total,
            "acertos_exatos": acertos,
            "erros_exatos": n_campos_total - acertos,
            "exact_match_accuracy_pct": round(100 * acertos / n_campos_total, 1),
            "character_level_accuracy_pct": round(100 * grupo["acuracia_caractere"].mean(), 1),
            "tempo_medio_ms": None if pd.isna(tempo_medio) else round(tempo_medio, 1),
            "taxa_falha_execucao_pct": round(
                100 * grupo.drop_duplicates("image_id")["falha_execucao"].mean(), 1
            ),
        }
        for dificuldade in ("easy", "medium", "hard"):
            sub = grupo[grupo["difficulty"] == dificuldade]
            resumo[f"accuracy_{dificuldade}_pct"] = (
                round(100 * sub["acerto_exato"].mean(), 1) if len(sub) else None
            )
        linhas_resumo.append(resumo)

    return pd.DataFrame(linhas_resumo).sort_values("exact_match_accuracy_pct", ascending=False)


def gerar_graficos(df_detalhado: pd.DataFrame, df_resumo: pd.DataFrame) -> None:
    VIS_DIR.mkdir(parents=True, exist_ok=True)
    cores = {
        "tesseract": "#c0392b",
        "easyocr": "#2980b9",
        "openai_multimodal": "#27ae60",
        "claude_vision": "#8e44ad",
    }

    # 1. Accuracy geral por abordagem
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ordem = df_resumo["metodo"].tolist()
    valores = df_resumo["exact_match_accuracy_pct"].tolist()
    bars = ax.bar(ordem, valores, color=[cores.get(m, "#888") for m in ordem])
    ax.set_ylim(0, 105)
    ax.set_ylabel("Exact Match Accuracy (%)")
    ax.set_title("Acurácia por Abordagem (30 imagens, 10 campos cada)")
    for bar, v in zip(bars, valores):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 1.5, f"{v:.1f}%",
                 ha="center", fontweight="bold")
    plt.tight_layout()
    plt.savefig(VIS_DIR / "accuracy_comparison.png", dpi=150)
    plt.close(fig)

    # 2. Accuracy por dificuldade
    fig, ax = plt.subplots(figsize=(8, 4.5))
    dificuldades = ["easy", "medium", "hard"]
    x = range(len(dificuldades))
    largura = 0.25
    for i, metodo in enumerate(ordem):
        linha = df_resumo[df_resumo["metodo"] == metodo].iloc[0]
        valores = [linha[f"accuracy_{d}_pct"] or 0 for d in dificuldades]
        ax.bar([xi + i * largura for xi in x], valores, width=largura,
               label=metodo, color=cores.get(metodo, "#888"))
    ax.set_xticks([xi + largura for xi in x])
    ax.set_xticklabels(["Fácil", "Médio", "Difícil"])
    ax.set_ylabel("Exact Match Accuracy (%)")
    ax.set_title("Acurácia por Nível de Dificuldade")
    ax.legend()
    plt.tight_layout()
    plt.savefig(VIS_DIR / "accuracy_by_difficulty.png", dpi=150)
    plt.close(fig)

    # 3. Tempo médio de processamento (métodos sem medição automatizada, como
    # leitura manual multimodal, são anotados em vez de plotados com tempo 0,
    # o que seria enganoso).
    fig, ax = plt.subplots(figsize=(7, 4.5))
    medidos = [(m, t) for m, t in zip(ordem, df_resumo["tempo_medio_ms"]) if t is not None and not pd.isna(t)]
    nao_medidos = [m for m in ordem if m not in [x[0] for x in medidos]]
    if medidos:
        nomes, tempos = zip(*medidos)
        ax.bar(nomes, tempos, color=[cores.get(m, "#888") for m in nomes])
    ax.set_ylabel("Tempo médio por imagem (ms)")
    if medidos:
        ax.set_yscale("log")
    titulo = "Tempo Médio de Processamento (escala log)"
    if nao_medidos:
        titulo += f"\n({', '.join(nao_medidos)}: execução manual, sem tempo automatizado)"
    ax.set_title(titulo, fontsize=10)
    plt.tight_layout()
    plt.savefig(VIS_DIR / "processing_time.png", dpi=150)
    plt.close(fig)

    # 4. Acurácia por campo (heatmap simplificado em barras agrupadas)
    fig, ax = plt.subplots(figsize=(12, 5))
    campos = list(CAMPOS_AVALIADOS)
    x = range(len(campos))
    largura = 0.25
    for i, metodo in enumerate(ordem):
        sub = df_detalhado[df_detalhado["metodo"] == metodo]
        valores = [100 * sub[sub["campo"] == c]["acerto_exato"].mean() for c in campos]
        ax.bar([xi + i * largura for xi in x], valores, width=largura,
               label=metodo, color=cores.get(metodo, "#888"))
    ax.set_xticks([xi + largura for xi in x])
    ax.set_xticklabels(campos, rotation=35, ha="right")
    ax.set_ylabel("Exact Match Accuracy (%)")
    ax.set_title("Acurácia por Campo Extraído")
    ax.legend()
    plt.tight_layout()
    plt.savefig(VIS_DIR / "accuracy_by_field.png", dpi=150)
    plt.close(fig)


def _metodos_disponiveis() -> list[str]:
    """Descobre os métodos com resultados brutos gravados em results/raw/."""
    encontrados = sorted(p.stem for p in RAW_RESULTS_DIR.glob("*.json"))
    if not encontrados:
        raise FileNotFoundError(
            f"Nenhum resultado bruto encontrado em {RAW_RESULTS_DIR}. "
            "Rode ao menos uma abordagem antes de agregar."
        )
    return encontrados


def main() -> None:
    metodos = _metodos_disponiveis()
    print(f"Métodos encontrados: {metodos}")
    df_detalhado = montar_dataframe_detalhado(metodos)
    df_resumo = calcular_resumo(df_detalhado)

    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    df_detalhado.to_csv(METRICS_DIR / "results_detalhado.csv", index=False)
    df_resumo.to_csv(METRICS_DIR / "benchmark_summary.csv", index=False)
    with open(METRICS_DIR / "metrics.json", "w", encoding="utf-8") as f:
        registros_limpos = [_sem_nan(r) for r in df_resumo.to_dict(orient="records")]
        json.dump(registros_limpos, f, ensure_ascii=False, indent=2)

    erros = df_detalhado[~df_detalhado["acerto_exato"]]
    erros.to_csv(METRICS_DIR / "error_analysis.csv", index=False)

    gerar_graficos(df_detalhado, df_resumo)

    print(df_resumo.to_string(index=False))
    print(f"\n✅ Métricas salvas em {METRICS_DIR}")
    print(f"✅ Gráficos salvos em {VIS_DIR}")


if __name__ == "__main__":
    main()
