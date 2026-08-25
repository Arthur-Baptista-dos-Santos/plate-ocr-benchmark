"""Interface comum às 3 abordagens, para que o benchmark trate cada uma de
forma intercambiável e o resultado seja serializável em JSON/CSV.
"""

from dataclasses import asdict, dataclass, field


@dataclass
class ExtractionResult:
    """Resultado padronizado de uma abordagem sobre uma imagem."""

    image_id: str
    metodo: str
    tempo_ms: float | None
    texto_bruto: str
    campos: dict[str, str] = field(default_factory=dict)
    erro: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)
