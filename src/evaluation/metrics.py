"""Métricas de avaliação da tarefa de leitura de placas.

Duas famílias de métrica, propositalmente não misturadas:

1. Exact Match Accuracy: um campo só conta como acerto se, após
   ``normalize_exact``, for idêntico ao Ground Truth. É a métrica principal:
   um único caractere errado em um número de série ou tensão pode tornar a
   placa inutilizável na prática.
2. Character-level Accuracy (1 - CER): baseada em distância de edição
   (Levenshtein) sobre ``normalize_cer``. Mede o quão "perto" a leitura
   chegou, mesmo quando não é um acerto exato.
"""

from dataclasses import dataclass

from rapidfuzz.distance import Levenshtein

from src.evaluation.normalization import normalize_cer, normalize_exact


def exact_match(predicao: object, gabarito: object) -> bool:
    """Retorna True se a predição bate exatamente com o gabarito (normalizado)."""
    return normalize_exact(predicao) == normalize_exact(gabarito)


def character_error_rate(predicao: object, gabarito: object) -> float:
    """Character Error Rate = distância de edição / tamanho do gabarito.

    Gabarito vazio e predição vazia => CER 0.0 (nada a errar).
    Gabarito vazio e predição não vazia => CER 1.0 (alucinação total).
    """
    pred_norm = normalize_cer(predicao)
    gt_norm = normalize_cer(gabarito)
    if not gt_norm:
        return 0.0 if not pred_norm else 1.0
    distancia = Levenshtein.distance(pred_norm, gt_norm)
    return min(distancia / len(gt_norm), 1.0)


def character_level_accuracy(predicao: object, gabarito: object) -> float:
    """1 - CER, limitado a [0, 1]."""
    return max(0.0, 1.0 - character_error_rate(predicao, gabarito))


@dataclass(frozen=True)
class RegistroAvaliado:
    """Resultado da avaliação de um campo de uma imagem por um método."""

    image_id: str
    difficulty: str
    metodo: str
    campo: str
    valor_predito: str
    valor_esperado: str
    acerto_exato: bool
    cer: float
    acuracia_caractere: float


def avaliar_campo(
    image_id: str,
    difficulty: str,
    metodo: str,
    campo: str,
    valor_predito: object,
    valor_esperado: object,
) -> RegistroAvaliado:
    """Avalia um único campo extraído contra o Ground Truth correspondente."""
    cer = character_error_rate(valor_predito, valor_esperado)
    return RegistroAvaliado(
        image_id=image_id,
        difficulty=difficulty,
        metodo=metodo,
        campo=campo,
        valor_predito="" if valor_predito is None else str(valor_predito),
        valor_esperado="" if valor_esperado is None else str(valor_esperado),
        acerto_exato=exact_match(valor_predito, valor_esperado),
        cer=cer,
        acuracia_caractere=max(0.0, 1.0 - cer),
    )
