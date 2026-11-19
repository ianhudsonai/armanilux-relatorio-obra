"""Lê export de conversa do WhatsApp no formato Android e no formato iPhone.

Cobre data em pt-BR (dia/mês/ano, com ou sem vírgula, com ou sem segundos),
ano com dois dígitos, horário de 12 horas quando aparece, mensagem de várias
linhas, aviso de criptografia e marcadores de anexo.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from common import corrigir_mojibake, decodificar_bytes, normalizar

_ESPACO = re.compile(r"\s+")
_DATA_HORA_ANDROID = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4}),?\s+"
    r"(\d{1,2}:\d{2}(?::\d{2})?)"
    r"(?:\s*([AaPp][Mm]))?\s*[-–—]\s*(.*)$"
)
_DATA_HORA_IPHONE = re.compile(
    r"^\[(\d{1,2}/\d{1,2}/\d{2,4}),?\s+"
    r"(\d{1,2}:\d{2}(?::\d{2})?)"
    r"(?:\s*([AaPp][Mm]))?\]\s*(.*)$"
)
_ANEXO_EXPLICITO = re.compile(
    r"<(?:anexad[oa]|anexo|attached):\s*([^>]+)>",
    re.IGNORECASE,
)
_ANEXO_SUFIXO = re.compile(
    r"([^\s<>\"]+\.(?:pdf|docx?|xlsx?|jpe?g|png|webp|heic|gif|opus|ogg|mp3|m4a|wav|aac|mp4|mov|3gp|avi|mkv))"
    r"\s+\((?:arquivo anexado|file attached)\)",
    re.IGNORECASE,
)
_MIDIA_OCULTA = re.compile(
    r"(m[ií]dia oculta|media omitted|áudio ocultado|audio omitted|"
    r"vídeo omitido|video omitted|imagem ocultada|image omitted|"
    r"documento omitido|document omitted|sticker omitido|figurinha omitida|"
    r"<mídia oculta>)",
    re.IGNORECASE,
)
# Documento exportado "sem mídia": o nome do arquivo vem na linha logo abaixo
# de "<Mídia oculta>". Legenda de foto não tem extensão e fica de fora.
_NOME_APOS_MIDIA_OCULTA = re.compile(
    r"^<m[ií]dia oculta>\s*\n\s*([^<>\n/\\]+\.(?:pdf|docx?|xlsx?|pptx?|dwg|dxf|zip|rar|txt|csv|"
    r"jpe?g|png|webp|heic|gif|opus|ogg|mp3|m4a|wav|aac|mp4|mov|3gp|avi|mkv))\s*(?:\n|$)",
    re.IGNORECASE,
)
# Linha de mensagem colada de outra conversa: "[21/08, 08:54] Nome: texto" (sem ano).
_LINHA_ENCAMINHADA = re.compile(
    r"^\[(\d{1,2})/(\d{1,2}),?\s+(\d{1,2}):(\d{2})\]\s*([^:\]\n]{1,80}?):\s(.*)$"
)


@dataclass
class Mensagem:
    quando: datetime
    autor: str | None
    texto: str
    anexos: list[str] = field(default_factory=list)
    midia_omitida: bool = False
    sistema: bool = False
    # Mensagem colada/reencaminhada: quem colou no grupo e quando.
    encaminhada_por: str | None = None
    encaminhada_em: datetime | None = None

    @property
    def data(self):
        return self.quando.date()

    @property
    def hora(self) -> str:
        return self.quando.strftime("%H:%M")


def _limpar_linha(linha: str) -> str:
    linha = linha.replace("\ufeff", "").replace("\u200e", "").replace("\u200f", "")
    caracteres = []
    for caractere in linha:
        if unicodedata_espaco(caractere):
            caracteres.append(" ")
        else:
            caracteres.append(caractere)
    return "".join(caracteres).strip()


def unicodedata_espaco(caractere: str) -> bool:
    import unicodedata

    return unicodedata.category(caractere) == "Zs"


def _interpretar_data(data_texto: str, hora_texto: str, periodo: str | None) -> datetime:
    parte_a, parte_b, ano = (int(pedaço) for pedaço in data_texto.split("/"))
    if ano < 100:
        ano += 2000
    # Export brasileiro é dia/mês. Se o segundo número não cabe em mês, é mês/dia.
    if parte_b > 12 and parte_a <= 12:
        mes, dia = parte_a, parte_b
    else:
        dia, mes = parte_a, parte_b
    pedacos_hora = hora_texto.split(":")
    hora = int(pedacos_hora[0])
    minuto = int(pedacos_hora[1])
    segundo = int(pedacos_hora[2]) if len(pedacos_hora) > 2 else 0
    if periodo:
        marcador = periodo.lower()
        if marcador == "pm" and hora < 12:
            hora += 12
        if marcador == "am" and hora == 12:
            hora = 0
    return datetime(ano, mes, dia, hora, minuto, segundo)


def _separar_autor(resto: str) -> tuple[str | None, str]:
    if ": " not in resto:
        return None, resto.strip()
    autor, texto = resto.split(": ", 1)
    autor = corrigir_mojibake(autor.strip())
    if not autor or len(autor) > 80:
        return None, resto.strip()
    return autor, texto.strip()


def _anexos_do_texto(texto: str) -> list[str]:
    encontrados: list[str] = []
    for padrao in (_ANEXO_EXPLICITO, _ANEXO_SUFIXO):
        for achado in padrao.findall(texto):
            nome = corrigir_mojibake(achado.strip().strip("."))
            if nome and nome not in encontrados:
                encontrados.append(nome)
    oculta = _NOME_APOS_MIDIA_OCULTA.match(texto)
    if oculta:
        nome = corrigir_mojibake(oculta.group(1).strip())
        if nome not in encontrados:
            encontrados.append(nome)
    return encontrados


def _data_encaminhada(achado: re.Match, postada: datetime) -> datetime | None:
    dia, mes, hora, minuto = (int(achado.group(i)) for i in range(1, 5))
    try:
        original = datetime(postada.year, mes, dia, hora, minuto)
        if original > postada:
            original = original.replace(year=postada.year - 1)
    except ValueError:
        return None
    return original


def _desmembrar(mensagem: Mensagem) -> list[Mensagem]:
    """Separa as mensagens coladas, cada uma com a data e o autor originais."""
    if mensagem.sistema or not mensagem.autor:
        return [mensagem]
    propria: list[str] = []
    coladas: list[Mensagem] = []
    for linha in mensagem.texto.split("\n"):
        achado = _LINHA_ENCAMINHADA.match(linha)
        quando = _data_encaminhada(achado, mensagem.quando) if achado else None
        if quando is not None:
            coladas.append(
                Mensagem(
                    quando=quando,
                    autor=corrigir_mojibake(achado.group(5).strip()),
                    texto=achado.group(6),
                    encaminhada_por=mensagem.autor,
                    encaminhada_em=mensagem.quando,
                )
            )
        elif coladas:
            coladas[-1].texto += "\n" + linha
        else:
            propria.append(linha)
    if not coladas:
        return [mensagem]
    for colada in coladas:
        colada.texto = colada.texto.strip()
    mensagem.texto = "\n".join(propria).strip()
    return ([mensagem] if mensagem.texto else []) + coladas


def analisar_conversa(texto: str) -> list[Mensagem]:
    mensagens: list[Mensagem] = []
    atual: Mensagem | None = None

    def fechar() -> None:
        nonlocal atual
        if atual is None:
            return
        atual.texto = corrigir_mojibake(atual.texto).strip()
        for parte in _desmembrar(atual):
            parte.anexos = _anexos_do_texto(parte.texto)
            parte.midia_omitida = bool(_MIDIA_OCULTA.search(parte.texto))
            mensagens.append(parte)
        atual = None

    for bruta in texto.splitlines():
        linha = _limpar_linha(bruta)
        if not linha:
            if atual is not None:
                atual.texto += "\n"
            continue
        casou = _DATA_HORA_ANDROID.match(linha) or _DATA_HORA_IPHONE.match(linha)
        if not casou:
            if atual is not None:
                atual.texto += ("\n" if atual.texto else "") + linha
            continue
        try:
            quando = _interpretar_data(casou.group(1), casou.group(2), casou.group(3))
        except ValueError:
            if atual is not None:
                atual.texto += ("\n" if atual.texto else "") + linha
            continue
        fechar()
        autor, corpo = _separar_autor(casou.group(4))
        atual = Mensagem(
            quando=quando,
            autor=autor,
            texto=corpo,
            sistema=autor is None,
        )
    fechar()
    return mensagens


def ler_conversa(caminho: Path) -> list[Mensagem]:
    return analisar_conversa(decodificar_bytes(Path(caminho).read_bytes()))


def texto_util(mensagem: Mensagem) -> str:
    return _ESPACO.sub(" ", mensagem.texto).strip()


def parece_conversa(texto: str) -> bool:
    mensagens = analisar_conversa(texto)
    return any(not item.sistema and item.autor for item in mensagens)
