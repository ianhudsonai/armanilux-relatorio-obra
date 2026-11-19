"""Gráficos do relatório: dias úteis entre marcos e linha do tempo das etapas.

As figuras são desenhadas já na largura em que entram no Word (16,2 cm), para a
letra sair no tamanho escolhido e não encolher. Não há gráfico de 'atraso acumulado'.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from analyze import ORDEM, TITULOS
from common import LARGURA_FIGURA_CM

LARGURA_POL = LARGURA_FIGURA_CM / 2.54  # mesma largura com que o Word insere a figura
DPI = 200
MARROM = "#442819"
DOURADO = "#C3A56D"
_MESES = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")

_CORES_ETAPA = {
    "A": "#5C6B73",
    "B": "#442819",
    "C": "#3D6B8C",
    "D": "#8C734B",
    "E": "#A15C38",
    "F": "#C48A4A",
    "G": "#1B7F4E",
    "H": "#3E7C6F",
    "I": "#2F5D50",
    "J": "#8E2F2F",
    "L": "#442819",
}


def _preparar():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams["font.family"] = "DejaVu Sans"
    plt.rcParams["font.size"] = 9
    return plt


# Nome curto de cada etapa, para caber no gráfico. O nome completo está na tabela.
NOME_CURTO = {
    "A": "Chapas",
    "B": "Visita",
    "C": "Medição",
    "D": "Projeto preliminar",
    "E": "Revisão de projeto",
    "F": "Projeto revisado",
    "G": "Aprovação",
    "H": "Entrega de material",
    "I": "Instalação",
    "J": "Interferências",
    "L": "Conclusão",
}


def _nome_curto(codigo: str) -> str:
    return NOME_CURTO.get(codigo, TITULOS.get(codigo, codigo))


def _dia_mes_ano(iso: str) -> str:
    dia = datetime.fromisoformat(iso)
    return dia.strftime("%d/%m/%y")


def _vazio(eixo) -> None:
    eixo.axis("off")
    eixo.text(0.5, 0.5, "dado não identificado", ha="center", va="center", fontsize=11, color=MARROM)


def _salvar(plt, fig, destino: Path) -> Path:
    fig.savefig(destino, dpi=DPI, facecolor="white")
    plt.close(fig)
    return destino


def grafico_barras(intervalos_marcos: list[dict], destino: Path) -> Path:
    """Uma barra deitada por intervalo entre marcos, com as datas legíveis à esquerda."""
    plt = _preparar()
    destino.parent.mkdir(parents=True, exist_ok=True)
    linhas = len(intervalos_marcos)
    fig, eixo = plt.subplots(figsize=(LARGURA_POL, 1.5 + 0.5 * max(linhas, 2)), layout="constrained")
    if not intervalos_marcos:
        _vazio(eixo)
    else:
        rotulos = [
            f"{item['de']} {_nome_curto(item['de'])} → {item['para']} {_nome_curto(item['para'])}\n"
            f"{_dia_mes_ano(item['inicio'])} a {_dia_mes_ano(item['fim'])}"
            for item in intervalos_marcos
        ]
        valores = [item["dias_uteis"] for item in intervalos_marcos]
        barras = eixo.barh(range(linhas), valores, color=DOURADO, edgecolor=MARROM, linewidth=0.6, height=0.6)
        eixo.set_yticks(range(linhas))
        eixo.set_yticklabels(rotulos, fontsize=9)
        eixo.invert_yaxis()
        topo = max(valores) or 1
        eixo.set_xlim(0, topo * 1.24)
        for barra, valor in zip(barras, valores):
            eixo.text(
                barra.get_width() + topo * 0.015,
                barra.get_y() + barra.get_height() / 2,
                f"{valor} d.u.",
                va="center",
                fontsize=9,
                fontweight="bold",
                color=MARROM,
            )
        eixo.set_xlabel("Dias úteis", fontsize=9)
        eixo.tick_params(axis="x", labelsize=8.5)
        eixo.spines["top"].set_visible(False)
        eixo.spines["right"].set_visible(False)
    # Título na figura inteira: no eixo ele ficava cortado pelos rótulos longos da esquerda.
    fig.suptitle(
        "Dias úteis entre marcos (primeiro registro de cada etapa)\nO número é intervalo de calendário, não soma de atraso.",
        fontsize=10,
        color=MARROM,
    )
    return _salvar(plt, fig, destino)


def _formatar_mes(valor, _posicao=None) -> str:
    import matplotlib.dates as mdates

    dia = mdates.num2date(valor)
    return f"{_MESES[dia.month - 1]}/{dia.strftime('%y')}"


def grafico_gantt(eventos: list[dict], destino: Path) -> Path:
    """Uma barra por etapa, do primeiro ao último registro. Sem borda vermelha: quase toda
    etapa de obra longa vem depois de algum intervalo longo, e a cor deixava de dizer algo."""
    plt = _preparar()
    import matplotlib.dates as mdates
    from matplotlib.ticker import FuncFormatter

    destino.parent.mkdir(parents=True, exist_ok=True)

    linhas = []
    for codigo in ORDEM:
        datas = [item["data"] for item in eventos if item["etapa"] == codigo]
        if not datas:
            continue
        linhas.append({"codigo": codigo, "inicio": min(datas), "fim": max(datas)})

    fig, eixo = plt.subplots(figsize=(LARGURA_POL, 1.4 + 0.42 * max(len(linhas), 2)), layout="constrained")
    if not linhas:
        _vazio(eixo)
    else:
        for indice, linha in enumerate(linhas):
            inicio = datetime.fromisoformat(linha["inicio"])
            fim = datetime.fromisoformat(linha["fim"]) + timedelta(days=1)
            if fim <= inicio:
                fim = inicio + timedelta(days=1)
            eixo.barh(
                indice,
                fim - inicio,
                left=inicio,
                height=0.6,
                color=_CORES_ETAPA.get(linha["codigo"], MARROM),
                edgecolor=MARROM,
                linewidth=0.5,
            )
        eixo.set_yticks(range(len(linhas)))
        eixo.set_yticklabels([f"{item['codigo']}  {_nome_curto(item['codigo'])}" for item in linhas], fontsize=8.5)
        eixo.invert_yaxis()
        primeiro = datetime.fromisoformat(min(item["inicio"] for item in linhas))
        ultimo = datetime.fromisoformat(max(item["fim"] for item in linhas))
        meses = (ultimo.year - primeiro.year) * 12 + ultimo.month - primeiro.month
        if meses >= 3:
            # Uma marca no começo do mês, no máximo 7 marcas: "jan/26".
            eixo.xaxis.set_major_locator(mdates.MonthLocator(interval=max(1, -(-meses // 7))))
            eixo.xaxis.set_major_formatter(FuncFormatter(_formatar_mes))
        else:
            eixo.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=7))
            eixo.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
        eixo.tick_params(axis="x", labelsize=8.5)
        eixo.spines["top"].set_visible(False)
        eixo.spines["right"].set_visible(False)
        eixo.grid(axis="x", color="#E6E2DA", linewidth=0.6)
    eixo.set_title(
        "Linha do tempo das etapas\nCada barra vai do primeiro ao último registro da etapa.",
        fontsize=10,
        color=MARROM,
    )
    return _salvar(plt, fig, destino)
