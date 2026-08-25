import pytest

from src.evaluation.metrics import (
    avaliar_campo,
    character_error_rate,
    character_level_accuracy,
    exact_match,
)


def test_exact_match_ignora_formatacao_irrelevante():
    assert exact_match("380/660 V", "380 / 660V") is True


def test_exact_match_detecta_caractere_errado():
    assert exact_match("IP54", "IP55") is False


def test_exact_match_vazio_contra_vazio_e_acerto():
    assert exact_match("", "") is True


def test_exact_match_vazio_contra_valor_e_erro():
    assert exact_match("", "IP54") is False


def test_cer_identico_e_zero():
    assert character_error_rate("WEG", "WEG") == 0.0


def test_cer_totalmente_diferente_e_limitado_a_1():
    assert character_error_rate("XXXXXXXXXX", "AB") == 1.0


def test_cer_predicao_vazia_com_gabarito_nao_vazio_e_1():
    assert character_error_rate("", "IP54") == 1.0


def test_cer_gabarito_vazio_com_predicao_vazia_e_0():
    assert character_error_rate("", "") == 0.0


@pytest.mark.parametrize(
    "pred,gt,esperado_aprox",
    [
        ("WEG", "WEG", 1.0),
        ("WEQ", "WEG", 2 / 3),
    ],
)
def test_character_level_accuracy(pred, gt, esperado_aprox):
    assert character_level_accuracy(pred, gt) == pytest.approx(esperado_aprox, abs=1e-6)


def test_avaliar_campo_monta_registro_consistente():
    registro = avaliar_campo(
        image_id="hard_001",
        difficulty="hard",
        metodo="tesseract",
        campo="grau_ip",
        valor_predito="1P44",
        valor_esperado="IP44",
    )
    assert registro.acerto_exato is False
    assert 0.0 < registro.cer <= 1.0
    assert registro.acuracia_caractere == pytest.approx(1.0 - registro.cer)
