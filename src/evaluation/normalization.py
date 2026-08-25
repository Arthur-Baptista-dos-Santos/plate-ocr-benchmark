"""Regras de normalização aplicadas de forma idêntica ao Ground Truth e às
saídas das 3 abordagens, antes de qualquer cálculo de métrica.

Duas regras distintas e documentadas, cada uma associada a uma métrica:

- ``normalize_exact``: usada para *Exact Match Accuracy*. Remove ruído de
  formatação (espaços, hífens, pontuação) que não representa erro de leitura,
  mas preserva os dígitos/letras em ordem. Ex.: "380 / 660 V" e "380/660V"
  tornam-se equivalentes; "IP54" e "IP 54" também.
- ``normalize_cer``: usada para *Character-level Accuracy* (1 - CER). Mantém
  a estrutura do texto (apenas caixa alta e espaços colapsados), pois a
  distância de edição precisa refletir erros reais de caractere, não a
  remoção artificial de separadores.
"""

import re
import unicodedata

_PONTUACAO_EXATA = re.compile(r"[\s\-.,/:;]+")
_ESPACOS = re.compile(r"\s+")


def _remover_acentos(texto: str) -> str:
    forma_decomposta = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in forma_decomposta if not unicodedata.combining(c))


def normalize_exact(valor: object) -> str:
    """Normaliza um campo para comparação de Exact Match Accuracy."""
    texto = "" if valor is None else str(valor)
    texto = _remover_acentos(texto).upper()
    texto = _PONTUACAO_EXATA.sub("", texto)
    return texto.strip()


def normalize_cer(valor: object) -> str:
    """Normaliza um campo para cálculo de Character Error Rate."""
    texto = "" if valor is None else str(valor)
    texto = _remover_acentos(texto).upper().strip()
    return _ESPACOS.sub(" ", texto)
