from src.evaluation.normalization import normalize_cer, normalize_exact


def test_normalize_exact_ignora_espacos_e_pontuacao():
    assert normalize_exact("380 / 660 V") == normalize_exact("380/660V")


def test_normalize_exact_ignora_hifen_em_numero_de_serie():
    assert normalize_exact("SN-2020-21773") == normalize_exact("SN 2020 21773")


def test_normalize_exact_ignora_caixa():
    assert normalize_exact("ip54") == normalize_exact("IP54")


def test_normalize_exact_none_vira_vazio():
    assert normalize_exact(None) == ""


def test_normalize_cer_preserva_espaco_unico_e_estrutura():
    assert normalize_cer("  weg   motores  ") == "WEG MOTORES"


def test_normalize_cer_nao_remove_hifen():
    assert normalize_cer("SN-2020-21773") == "SN-2020-21773"
