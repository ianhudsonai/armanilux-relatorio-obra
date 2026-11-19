"""Transcreve fala de áudio e de vídeo com faster-whisper, no computador.

Não chama API. O modelo (padrão: small, português) é baixado uma vez para o
cache local do Whisper e, depois disso, a transcrição funciona sem rede.
Se a biblioteca ou o FFmpeg não existirem, cada arquivo recebe status
claro e o relatório marca a fala como dado não identificado.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from common import EXT_AUDIO, EXT_VIDEO, localizar_ferramenta
from registro import sha256_arquivo


def listar_midias_de_fala(pasta_midias: Path) -> list[Path]:
    if not pasta_midias.exists():
        return []
    extensoes = EXT_AUDIO | EXT_VIDEO
    return [
        item
        for item in sorted(pasta_midias.iterdir())
        if item.is_file() and item.suffix.lower() in extensoes
    ]


def _converter_para_wav(origem: Path, destino: Path) -> bool:
    ffmpeg = localizar_ferramenta("ffmpeg")
    if not ffmpeg:
        return False
    destino.parent.mkdir(parents=True, exist_ok=True)
    try:
        resultado = subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(origem),
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                str(destino),
            ],
            capture_output=True,
            timeout=180,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return False
    return resultado.returncode == 0 and destino.exists() and destino.stat().st_size > 0


def _ler_amostras(wav: Path):
    """Lê o WAV de 16 kHz mono e devolve amostras float32 entre -1 e 1."""
    import wave

    import numpy as np

    with wave.open(str(wav), "rb") as arquivo:
        bruto = arquivo.readframes(arquivo.getnframes())
    return np.frombuffer(bruto, dtype=np.int16).astype(np.float32) / 32768.0


def _registro(caminho: Path, status: str, texto: str = "", erro: str = "") -> dict:
    return {
        "arquivo": caminho.name,
        "caminho": str(caminho),
        "status": status,
        "texto": texto,
        "erro": erro,
    }


NOME_CACHE = "transcricoes-cache.json"


class _ErroDeTranscricao(Exception):
    """Falha com motivo claro; `status` vai para o registro do arquivo."""

    def __init__(self, motivo: str, status: str = "erro"):
        super().__init__(motivo)
        self.status = status


def _ler_cache(pasta_saida: Path) -> dict:
    caminho = pasta_saida / NOME_CACHE
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _gravar_cache(pasta_saida: Path, cache: dict) -> None:
    caminho = pasta_saida / NOME_CACHE
    temporario = caminho.with_suffix(".tmp")
    temporario.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    temporario.replace(caminho)


def _transcricao_guardada(arquivo: Path, pasta_saida: Path, cache: dict, sha: str, modelo: str) -> str | None:
    """Texto já transcrito deste mesmo arquivo, com o mesmo modelo; senão None."""
    texto = pasta_saida / f"{arquivo.stem}.txt"
    if not texto.exists():
        return None
    guardado = cache.get(arquivo.name)
    if guardado and (guardado.get("sha256") != sha or guardado.get("modelo") != modelo):
        return None
    return texto.read_text(encoding="utf-8").strip()


def _transcritor_whisper(modelo: str, pasta_saida: Path):
    """Carrega o Whisper uma vez e devolve uma função arquivo -> texto."""
    try:
        from faster_whisper import WhisperModel
    except ImportError as erro:
        raise _ErroDeTranscricao("faster-whisper não instalado", "indisponivel") from erro
    try:
        motor = WhisperModel(modelo, device="cpu", compute_type="int8")
    except Exception as erro:
        raise _ErroDeTranscricao(f"não foi possível carregar o modelo: {erro}") from erro

    def transcrever(arquivo: Path) -> str:
        wav = pasta_saida / f"{arquivo.stem}-16k.wav"
        # Sempre passa pelo FFmpeg e entrega ao Whisper as amostras já lidas. Assim a
        # transcrição não depende da biblioteca PyAV, que quebrou em versões novas.
        if not _converter_para_wav(arquivo, wav):
            raise _ErroDeTranscricao(
                "FFmpeg não encontrado para preparar o áudio"
                if localizar_ferramenta("ffmpeg") is None
                else "não consegui preparar o áudio com o FFmpeg"
            )
        try:
            amostras = _ler_amostras(wav)
            try:
                segmentos, _info = motor.transcribe(amostras, language="pt", vad_filter=True)
                return " ".join(pedaço.text.strip() for pedaço in segmentos).strip()
            except Exception:
                segmentos, _info = motor.transcribe(amostras, language="pt", vad_filter=False)
                return " ".join(pedaço.text.strip() for pedaço in segmentos).strip()
        finally:
            if wav.exists():
                wav.unlink()

    return transcrever


def transcrever_pasta(
    pasta_midias: Path,
    pasta_saida: Path,
    *,
    pular: bool = False,
    modelo: str = "small",
    transcritor=None,
    progresso=None,
) -> list[dict]:
    """Transcreve cada áudio e vídeo uma vez só.

    O texto fica em `<arquivo>.txt` e `transcricoes-cache.json` guarda o SHA-256
    e o modelo de cada um. Numa nova execução, o arquivo igual não é refeito; se
    a execução parar no meio, a próxima continua de onde parou.
    `transcritor` (arquivo -> texto) substitui FFmpeg + Whisper nos testes.
    `progresso` recebe uma linha por arquivo que vai ser transcrito agora.
    """
    arquivos = listar_midias_de_fala(pasta_midias)
    pasta_saida.mkdir(parents=True, exist_ok=True)
    if not arquivos:
        return []

    cache = _ler_cache(pasta_saida)
    resultados = []
    falha_geral: _ErroDeTranscricao | None = None
    for posicao, arquivo in enumerate(arquivos, start=1):
        sha = sha256_arquivo(arquivo)
        guardado = _transcricao_guardada(arquivo, pasta_saida, cache, sha, modelo)
        if guardado is not None:
            if arquivo.name not in cache:
                cache[arquivo.name] = {"sha256": sha, "modelo": modelo}
                _gravar_cache(pasta_saida, cache)
            resultados.append(_registro(arquivo, "ok", texto=guardado))
            continue
        if pular:
            resultados.append(_registro(arquivo, "ignorado"))
            continue
        if transcritor is None and falha_geral is None:
            try:
                transcritor = _transcritor_whisper(modelo, pasta_saida)
            except _ErroDeTranscricao as erro:
                falha_geral = erro
        if falha_geral is not None:
            resultados.append(_registro(arquivo, falha_geral.status, erro=str(falha_geral)))
            continue
        if progresso:
            progresso(f"Transcrevendo {posicao}/{len(arquivos)}: {arquivo.name}")
        try:
            texto = transcritor(arquivo)
        except Exception as erro:
            resultados.append(_registro(arquivo, "erro", erro=str(erro)))
            continue
        (pasta_saida / f"{arquivo.stem}.txt").write_text(texto + "\n", encoding="utf-8")
        cache[arquivo.name] = {"sha256": sha, "modelo": modelo}
        _gravar_cache(pasta_saida, cache)
        resultados.append(_registro(arquivo, "ok", texto=texto))
    return resultados
