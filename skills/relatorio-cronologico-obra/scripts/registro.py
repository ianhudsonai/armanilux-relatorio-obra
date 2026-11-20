"""Registro local das conversas, pela soma SHA-256 do arquivo.

Fica em %USERPROFILE%\\.armanilux-relatorio\\registro.json. Nada sai do computador.
Estados: pendente -> em andamento -> relatório gerado -> concluído.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

PENDENTE = "pendente"
ANDAMENTO = "em andamento"
GERADO = "relatório gerado"
CONCLUIDO = "concluído"
COM_RELATORIO = {GERADO, CONCLUIDO}
NA_FILA = {PENDENTE, ANDAMENTO}


def caminho_registro() -> Path:
    bruto = os.environ.get("ARMANILUX_REGISTRO", "").strip()
    if bruto:
        return Path(bruto)
    from config_io import caminho_config

    return caminho_config().parent / "registro.json"


def sha256_arquivo(caminho: Path) -> str:
    resumo = hashlib.sha256()
    with Path(caminho).open("rb") as arquivo:
        while True:
            bloco = arquivo.read(8 * 1024 * 1024)
            if not bloco:
                break
            resumo.update(bloco)
    return resumo.hexdigest()


def carregar() -> dict:
    caminho = caminho_registro()
    if not caminho.is_file():
        return {"exportacoes": {}, "fila": [], "repetidos": 0}
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    dados.setdefault("exportacoes", {})
    dados.setdefault("fila", [])
    dados.setdefault("repetidos", 0)
    return dados


def salvar(dados: dict) -> Path:
    caminho = caminho_registro()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(".tmp")
    temporario.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporario, caminho)
    return caminho


def _agora() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _obra_tem_relatorio(dados: dict, numero: str, exceto: str = "") -> bool:
    if not numero:
        return False
    return any(
        sha != exceto and item.get("numero") == numero and item.get("status") in COM_RELATORIO
        for sha, item in dados["exportacoes"].items()
    )


def _ordenar(itens: list[dict]) -> list[dict]:
    return sorted(
        itens,
        key=lambda i: (i.get("ultima_mensagem") or "", i.get("arquivo_original") or ""),
        reverse=True,
    )


def _fila(dados: dict) -> list[dict]:
    """Conversas sem relatório cujo arquivo ainda está no lugar (zip apagado ou movido sai da lista)."""
    return _ordenar(
        [i for i in dados["exportacoes"].values() if i.get("status") in NA_FILA and Path(i.get("caminho") or "").is_file()]
    )


def sincronizar(achados: list[dict], salvar_agora: bool = True) -> dict:
    """Põe no registro o que foi achado. Mesmo conteúdo com outro nome é repetido, não novo."""
    dados = carregar()
    repetidos = 0
    vistos: set[str] = set()
    for achado in achados:
        sha = sha256_arquivo(achado["caminho"])
        achado["sha256"] = sha
        if sha in vistos:
            repetidos += 1
            continue
        vistos.add(sha)
        existente = dados["exportacoes"].get(sha)
        if existente:
            if existente.get("caminho") != achado["caminho"] and not Path(existente.get("caminho", "")).exists():
                existente["caminho"] = achado["caminho"]
                existente["atualizado_em"] = _agora()
            elif existente.get("caminho") != achado["caminho"]:
                repetidos += 1
            continue
        agora = _agora()
        numero = achado.get("numero") or ""
        dados["exportacoes"][sha] = {
            "sha256": sha,
            "arquivo_original": achado["nome"],
            "caminho": achado["caminho"],
            "tipo": achado.get("tipo", "zip"),
            "numero": numero,
            "cliente": achado.get("cliente") or "",
            "primeira_mensagem": achado.get("primeira_mensagem") or "",
            "ultima_mensagem": achado.get("ultima_mensagem") or "",
            "status": PENDENTE,
            "atualiza_relatorio": _obra_tem_relatorio(dados, numero),
            "relatorios": [],
            "pasta_obra": "",
            "criado_em": agora,
            "atualizado_em": agora,
            "concluido_em": "",
        }
    dados["fila"] = [i["sha256"] for i in _fila(dados)]
    dados["repetidos"] = repetidos
    if salvar_agora:
        salvar(dados)
    return dados


def marcar_andamento(sha: str, numero: str | None = None, cliente: str | None = None) -> dict:
    """`numero` e `cliente`: os que valeram nesta rodada (a pessoa pode ter corrigido o adivinhado)."""
    dados = carregar()
    item = dados["exportacoes"][sha]
    if numero:
        item["numero"] = numero
    if cliente:
        item["cliente"] = cliente
    item["status"] = ANDAMENTO
    item["atualizado_em"] = _agora()
    salvar(dados)
    return item


def registrar_relatorio(sha: str, caminho_relatorio: str, versao: int, pasta_obra: str) -> dict:
    dados = carregar()
    item = dados["exportacoes"][sha]
    item["status"] = GERADO
    item["pasta_obra"] = pasta_obra
    _anotar_word(dados, item, caminho_relatorio, versao)
    return item


def _anotar_word(dados: dict, item: dict, caminho_relatorio: str, versao: int) -> None:
    item["atualizado_em"] = _agora()
    item.setdefault("relatorios", []).append(
        {"caminho": caminho_relatorio, "versao": versao, "em": item["atualizado_em"]}
    )
    dados["fila"] = [i["sha256"] for i in _fila(dados)]
    salvar(dados)


def anotar_remontagem(pasta_obra: str, caminho_relatorio: str, versao: int) -> bool:
    """Remontagem (sem zip novo): anota o Word novo na exportação mais recente da obra.
    Conversa já concluída continua concluída. Devolve False se a obra não está no registro."""
    dados = carregar()
    alvo = os.path.normcase(os.path.abspath(pasta_obra))
    da_obra = [
        item
        for item in dados["exportacoes"].values()
        if item.get("pasta_obra") and os.path.normcase(os.path.abspath(item["pasta_obra"])) == alvo
    ]
    if not da_obra:
        return False
    item = max(da_obra, key=lambda i: i.get("atualizado_em", ""))
    if item.get("status") != CONCLUIDO:
        item["status"] = GERADO
    _anotar_word(dados, item, caminho_relatorio, versao)
    return True


def concluir(sha: str, copiar: bool = False) -> Path | None:
    """Só depois que a pessoa aprovar o relatório: guarda o zip na obra e fecha.
    Devolve None se o zip já não estava no lugar (a conversa extraída continua na obra)."""
    dados = carregar()
    item = dados["exportacoes"][sha]
    if item.get("status") != GERADO:
        raise RuntimeError("Esta conversa ainda não tem relatório gerado, ou já foi concluída.")
    origem = Path(item["caminho"])
    destino_dir = Path(item["pasta_obra"]) / "01-conversas"
    destino_dir.mkdir(parents=True, exist_ok=True)
    destino = destino_dir / origem.name
    if not origem.exists() and not destino.exists():
        item["status"] = CONCLUIDO
        item["concluido_em"] = item["atualizado_em"] = _agora()
        salvar(dados)
        return None
    if origem.exists() and os.path.normcase(str(origem.resolve())) != os.path.normcase(str(destino.resolve())):
        if destino.exists():
            destino = destino_dir / f"{origem.stem}-{sha[:6]}{origem.suffix}"
        if copiar:
            shutil.copy2(origem, destino)
        else:
            shutil.move(str(origem), str(destino))
    item["caminho"] = str(destino)
    item["status"] = CONCLUIDO
    item["concluido_em"] = item["atualizado_em"] = _agora()
    salvar(dados)
    return destino


def fixar_lista(dados: dict) -> dict:
    """Guarda a lista numerada que a pessoa viu. Os números valem até o próximo --listar,
    mesmo depois que uma conversa da lista ganha relatório e sai da fila."""
    dados["lista"] = list(dados.get("fila") or [])
    salvar(dados)
    return dados


def escolher(dados: dict, indices: list[int] | None, todas: bool) -> list[str]:
    if todas:
        return list(dados.get("fila") or [])
    lista = list(dados.get("lista") or dados.get("fila") or [])
    escolhidos = []
    for indice in indices or []:
        if indice < 1 or indice > len(lista) or lista[indice - 1] not in dados["exportacoes"]:
            raise IndexError(indice)
        escolhidos.append(lista[indice - 1])
    return escolhidos


def formatar_lista(dados: dict) -> str:
    from common import formatar_data

    itens = _fila(dados)
    if not itens:
        return (
            "Não achei conversa do WhatsApp sem relatório.\n"
            "Pode deixar o arquivo em Downloads, na Área de Trabalho ou na pasta da Armanilux."
        )
    palavra = "conversa" if len(itens) == 1 else "conversas"
    linhas = [f"Achei {len(itens)} {palavra} sem relatório:"]
    for indice, item in enumerate(itens, start=1):
        numero = item.get("numero") or "número não identificado"
        cliente = item.get("cliente") or "cliente não identificado"
        quando = formatar_data(item["ultima_mensagem"]) if item.get("ultima_mensagem") else "data não identificada"
        extra = " — conversa nova de uma obra que já tem relatório; dá para gerar a próxima versão" if item.get("atualiza_relatorio") else ""
        # O nome do arquivo deixa a pessoa conferir número e cliente, que são adivinhados dele.
        arquivo = item.get("arquivo_original") or Path(item.get("caminho") or "").name
        linhas.append(f"{indice}) Obra {numero} – {cliente} (até {quando}){extra}\n   arquivo: {arquivo}")
    linhas.append("Quer começar por qual? (pode escolher várias ou todas)")
    if dados.get("repetidos"):
        linhas.append(f"Ignorei {dados['repetidos']} arquivo(s) repetido(s): mesmo conteúdo, outro nome.")
    return "\n".join(linhas)
