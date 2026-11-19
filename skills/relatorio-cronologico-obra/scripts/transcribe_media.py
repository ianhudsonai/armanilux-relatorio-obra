"""Transcreve fala de áudio e de vídeo com faster-whisper, no computador.

Não chama API. O modelo (padrão: small, português) é baixado uma vez para o
cache local do Whisper e, depois disso, a transcrição funciona sem rede.
Se a biblioteca ou o FFmpeg não existirem, cada arquivo recebe status
claro e o relatório marca a fala como dado não identificado.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from common import EXT_AUDIO, EXT_VIDEO, localizar_ferramenta


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


def transcrever_pasta(
    pasta_midias: Path,
    pasta_saida: Path,
    *,
    pular: bool = False,
    modelo: str = "small",
) -> list[dict]:
    arquivos = listar_midias_de_fala(pasta_midias)
    pasta_saida.mkdir(parents=True, exist_ok=True)
    if not arquivos:
        return []
    if pular:
        return [_registro(item, "ignorado") for item in arquivos]

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return [
            _registro(item, "indisponivel", erro="faster-whisper não instalado")
            for item in arquivos
        ]

    try:
        motor = WhisperModel(modelo, device="cpu", compute_type="int8")
    except Exception as erro:
        return [_registro(item, "erro", erro=f"não foi possível carregar o modelo: {erro}") for item in arquivos]

    resultados = []
    for arquivo in arquivos:
        wav = pasta_saida / f"{arquivo.stem}-16k.wav"
        # Sempre passa pelo FFmpeg e entrega ao Whisper as amostras já lidas. Assim a
        # transcrição não depende da biblioteca PyAV, que quebrou em versões novas.
        if not _converter_para_wav(arquivo, wav):
            motivo = (
                "FFmpeg não encontrado para preparar o áudio"
                if localizar_ferramenta("ffmpeg") is None
                else "não consegui preparar o áudio com o FFmpeg"
            )
            resultados.append(_registro(arquivo, "erro", erro=motivo))
            continue
        try:
            amostras = _ler_amostras(wav)
            try:
                segmentos, _info = motor.transcribe(amostras, language="pt", vad_filter=True)
                texto = " ".join(pedaço.text.strip() for pedaço in segmentos).strip()
            except Exception:
                segmentos, _info = motor.transcribe(amostras, language="pt", vad_filter=False)
                texto = " ".join(pedaço.text.strip() for pedaço in segmentos).strip()
        except Exception as erro:
            resultados.append(_registro(arquivo, "erro", erro=str(erro)))
            continue
        finally:
            if wav.exists():
                wav.unlink()
        (pasta_saida / f"{arquivo.stem}.txt").write_text(texto + "\n", encoding="utf-8")
        resultados.append(_registro(arquivo, "ok", texto=texto))
    return resultados
