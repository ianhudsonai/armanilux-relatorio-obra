"""Dias úteis da Armanilux: Brasil, estado de São Paulo e capital.

Contagem: dias úteis estritamente depois da data inicial, até a data final
inclusive. Sábado, domingo e os feriados da convenção não entram.
Quarta-feira de Cinzas permanece dia útil.
"""

from __future__ import annotations

from datetime import date, timedelta

from common import CONVENCAO_DIAS_UTEIS, como_data

_FERIADOS: dict[int, set[date]] = {}


def pascoa(ano: int) -> date:
    """Domingo de Páscoa no calendário gregoriano (algoritmo de Meeus/Jones/Butcher)."""
    a = ano % 19
    b = ano // 100
    c = ano % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    erro = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * erro) // 451
    mes = (h + erro - 7 * m + 114) // 31
    dia = ((h + erro - 7 * m + 114) % 31) + 1
    return date(ano, mes, dia)


def carnaval(ano: int) -> tuple[date, date]:
    """Segunda e terça de Carnaval. A quarta de Cinzas não é incluída."""
    domingo = pascoa(ano)
    return domingo - timedelta(days=48), domingo - timedelta(days=47)


def corpus_christi(ano: int) -> date:
    return pascoa(ano) + timedelta(days=60)


def feriados_do_ano(ano: int) -> set[date]:
    if ano in _FERIADOS:
        return _FERIADOS[ano]

    import holidays

    dias: set[date] = set()
    carregou_capital = False
    for subdivisao in ("São Paulo Capital", "SP"):
        try:
            calendario = holidays.country_holidays("BR", subdiv=subdivisao, years=[ano])
        except Exception:
            continue
        dias.update(calendario.keys())
        if subdivisao == "São Paulo Capital":
            carregou_capital = True
            break
    if not dias:
        try:
            dias.update(holidays.country_holidays("BR", years=[ano]).keys())
        except Exception as erro:
            raise RuntimeError(
                "Não foi possível carregar o calendário de feriados do Brasil."
            ) from erro

    # Garante a convenção mesmo se a versão da biblioteca mudar de nome.
    dias.add(date(ano, 1, 25))
    dias.add(date(ano, 7, 9))
    if not carregou_capital:
        dias.add(corpus_christi(ano))
    segunda, terca = carnaval(ano)
    dias.add(segunda)
    dias.add(terca)
    _FERIADOS[ano] = dias
    return dias


def eh_dia_util(dia: date) -> bool:
    dia = como_data(dia)
    if dia.weekday() >= 5:
        return False
    return dia not in feriados_do_ano(dia.year)


def dias_uteis_entre(inicio: date, fim: date) -> int:
    """Dias úteis depois de `inicio`, até `fim` inclusive. Mesmo dia vale 0."""
    inicio = como_data(inicio)
    fim = como_data(fim)
    if fim <= inicio:
        return 0
    total = 0
    cursor = inicio + timedelta(days=1)
    while cursor <= fim:
        if eh_dia_util(cursor):
            total += 1
        cursor += timedelta(days=1)
    return total


def leitura_intervalo(dias: int) -> str:
    if dias <= 2:
        return "Fluxo contínuo"
    if dias <= 5:
        return "Atenção"
    return "Intervalo longo"


def cor_leitura(leitura: str) -> str:
    return {
        "Fluxo contínuo": "1B7F4E",
        "Atenção": "E6A100",
        "Intervalo longo": "C62828",
    }.get(leitura, "5C6B73")
