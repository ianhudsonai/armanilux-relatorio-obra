"""Gráficos do relatório: barras de dias úteis e linha do tempo das etapas.

As cores marcam a leitura do intervalo (fluxo contínuo, atenção, intervalo longo).
Não há gráfico de 'atraso acumulado'.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from analyze import ORDEM, TITULOS
from business_days import cor_leitura
from common import formatar_data

_CORES_ETAPA = {
    "A": "#5C6B73",
    "B": "#1F3A5F",
    "C": "#3D6B8C",
    "D": "#8C734B",
    "E": "#A15C38",
    "F": "#C48A4A",
    "G": "#1B7F4E",
    "H": "#3E7C6F",
    "I": "#2F5D50",
    "J": "#8E2F2F",
    "L": "#1F3A5F",
}


def _preparar():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams["font.family"] = "DejaVu Sans"
    return plt


def grafico_barras(intervalos: list[dict], destino: Path) -> Path:
    plt = _preparar()
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig, eixo = plt.subplots(figsize=(11, 5.8))
    if not intervalos:
        eixo.axis("off")
        eixo.text(0.5, 0.5, "dado não identificado", ha="center", va="center", fontsize=14, color="#1F3A5F")
    else:
        rotulos = [
            f"{item['rotulo']}\n{formatar_data(item['inicio'])[0:5]}–{formatar_data(item['fim'])[0:5]}"
            for item in intervalos
        ]
        valores = [item["dias_uteis"] for item in intervalos]
        cores = ["#" + cor_leitura(item["leitura"]) for item in intervalos]
        barras = eixo.bar(range(len(valores)), valores, color=cores, width=0.72)
        eixo.set_xticks(range(len(rotulos)))
        eixo.set_xticklabels(rotulos, rotation=35, ha="right", fontsize=7.5)
        eixo.set_ylabel("Dias úteis")
        topo = max(valores) if valores else 1
        eixo.set_ylim(0, topo + max(1, topo * 0.18))
        for barra, valor in zip(barras, valores):
            eixo.text(
                barra.get_x() + barra.get_width() / 2,
                barra.get_height() + topo * 0.03,
                str(valor),
                ha="center",
                va="bottom",
                fontsize=8,
                color="#1F3A5F",
            )
        eixo.spines["top"].set_visible(False)
        eixo.spines["right"].set_visible(False)
    eixo.set_title(
        "Dias úteis entre registros\n"
        "Verde: até 2 (fluxo contínuo). Amarelo: 3 a 5 (atenção). Vermelho: 6 ou mais (intervalo longo).\n"
        "O número não é soma de atraso.",
        fontsize=11,
        color="#1F3A5F",
        pad=12,
    )
    fig.tight_layout()
    fig.savefig(destino, dpi=140, facecolor="white")
    plt.close(fig)
    return destino


def grafico_gantt(eventos: list[dict], intervalos: list[dict], destino: Path) -> Path:
    plt = _preparar()
    import matplotlib.dates as mdates

    destino.parent.mkdir(parents=True, exist_ok=True)
    longos: set[str] = set()
    for intervalo in intervalos:
        if intervalo.get("leitura") == "Intervalo longo":
            longos.update(intervalo.get("para_etapas") or [])

    linhas = []
    for codigo in ORDEM:
        datas = [item["data"] for item in eventos if item["etapa"] == codigo]
        if not datas:
            continue
        linhas.append({"codigo": codigo, "inicio": min(datas), "fim": max(datas)})

    fig, eixo = plt.subplots(figsize=(11, 6.2))
    if not linhas:
        eixo.axis("off")
        eixo.text(0.5, 0.5, "dado não identificado", ha="center", va="center", fontsize=14, color="#1F3A5F")
    else:
        for indice, linha in enumerate(linhas):
            inicio = datetime.fromisoformat(linha["inicio"])
            fim = datetime.fromisoformat(linha["fim"]) + timedelta(days=1)
            if fim <= inicio:
                fim = inicio + timedelta(days=1)
            borda = "#C62828" if linha["codigo"] in longos else "#1F3A5F"
            eixo.barh(
                indice,
                fim - inicio,
                left=inicio,
                height=0.55,
                color=_CORES_ETAPA.get(linha["codigo"], "#1F3A5F"),
                edgecolor=borda,
                linewidth=2 if linha["codigo"] in longos else 0.6,
            )
        eixo.set_yticks(range(len(linhas)))
        eixo.set_yticklabels(
            [f"{item['codigo']}  {TITULOS[item['codigo']].split('–', 1)[-1].strip()}" for item in linhas],
            fontsize=8,
        )
        eixo.invert_yaxis()
        eixo.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
        eixo.spines["top"].set_visible(False)
        eixo.spines["right"].set_visible(False)
        eixo.grid(axis="x", color="#E6E2DA", linewidth=0.6)
    eixo.set_title(
        "Linha do tempo das etapas\nBorda vermelha: etapa precedida por intervalo longo (6 dias úteis ou mais).",
        fontsize=11,
        color="#1F3A5F",
        pad=12,
    )
    fig.tight_layout()
    fig.savefig(destino, dpi=140, facecolor="white")
    plt.close(fig)
    return destino
