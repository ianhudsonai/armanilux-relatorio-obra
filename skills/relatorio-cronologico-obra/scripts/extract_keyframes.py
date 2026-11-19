"""Extrai três quadros de cada vídeo com FFmpeg, em arquivo temporário nenhum.

Os quadros vão para 03-midias/quadros/<nome-do-video>/. Se o FFmpeg não
estiver instalado, o relatório segue e o fato fica registrado.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from common import EXT_VIDEO, localizar_ferramenta


def ffmpeg_disponivel() -> bool:
    return localizar_ferramenta("ffmpeg") is not None


def _duracao_segundos(video: Path) -> float | None:
    localizar_ferramenta("ffmpeg")
    ffprobe = localizar_ferramenta("ffprobe")
    if not ffprobe:
        return None
    try:
        resultado = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "csv=p=0",
                str(video),
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        return float(resultado.stdout.strip())
    except (ValueError, subprocess.TimeoutExpired, OSError):
        return None


def extrair_quadros(video: Path, pasta_quadros: Path, quantidade: int = 3) -> list[Path]:
    ffmpeg = localizar_ferramenta("ffmpeg")
    if not ffmpeg:
        return []
    destino_dir = pasta_quadros / video.stem
    destino_dir.mkdir(parents=True, exist_ok=True)
    duracao = _duracao_segundos(video)
    if duracao and duracao > 0.4:
        fracoes = [0.05, 0.45, 0.8][:quantidade]
        instantes = [max(0.0, duracao * fracao) for fracao in fracoes]
    else:
        instantes = [0.0, 0.4, 0.8][:quantidade]
    gerados: list[Path] = []
    for indice, instante in enumerate(instantes, start=1):
        destino = destino_dir / f"quadro-{indice:02d}.jpg"
        try:
            resultado = subprocess.run(
                [
                    ffmpeg,
                    "-y",
                    "-ss",
                    f"{instante:.3f}",
                    "-i",
                    str(video),
                    "-frames:v",
                    "1",
                    "-q:v",
                    "3",
                    str(destino),
                ],
                capture_output=True,
                timeout=60,
                check=False,
            )
        except (subprocess.TimeoutExpired, OSError):
            continue
        if resultado.returncode == 0 and destino.exists() and destino.stat().st_size > 0:
            gerados.append(destino)
    return gerados


def extrair_pasta(pasta_midias: Path) -> dict:
    pasta_quadros = pasta_midias / "quadros"
    pasta_quadros.mkdir(parents=True, exist_ok=True)
    videos = [
        item
        for item in sorted(pasta_midias.iterdir())
        if item.is_file() and item.suffix.lower() in EXT_VIDEO
    ]
    if not videos:
        return {"ffmpeg": ffmpeg_disponivel(), "quadros": [], "videos": 0}
    if not ffmpeg_disponivel():
        return {
            "ffmpeg": False,
            "quadros": [],
            "videos": len(videos),
            "aviso": "FFmpeg não encontrado. Quadros de vídeo não extraídos.",
        }
    quadros: list[str] = []
    for video in videos:
        for quadro in extrair_quadros(video, pasta_quadros):
            quadros.append(str(quadro))
    return {"ffmpeg": True, "quadros": quadros, "videos": len(videos)}
