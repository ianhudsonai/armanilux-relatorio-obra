"""Gera um export fictício de WhatsApp para demonstração e teste.

Nomes, endereços e a obra 1001 são inventados. Não há cliente real.
"""

from __future__ import annotations

import shutil
import subprocess
import zipfile
from pathlib import Path

CHAT = """[08/01/2026, 07:59:00] As mensagens e as ligações são protegidas com a criptografia de ponta a ponta.
[08/01/2026, 08:00:01] Helena Duarte: Registro inicial da Obra 1001. Cliente: Família Almeida. Construtora: Construtora Horizonte Ltda. Engenheiro: Paulo Ribeiro. Arquitetura: Marina Costa Arquitetura. Responsável Armanilux: Helena Duarte. Endereço: Rua das Acácias, 120, São Paulo. O prazo contratual não foi lançado neste grupo.
[08/01/2026, 09:20:11] Lucas Ferreira: Aprovo as chapas do lote 3, pedra branca, para a cozinha e os dois banheiros.
\u200e<anexado: chapa-lote-3.jpg>
[08/01/2026, 09:22:40] Carlos Mendes: Ok, obrigado.
[09/01/2026, 11:00:04] Carlos Mendes: Solicito uma visita in loco para conferir o ambiente antes da medição.
[13/01/2026, 10:30:18] Helena Duarte: Medição in loco realizada hoje na cozinha e nos banheiros. Segue o áudio com as cotas.
\u200e<anexado: audio-medicao.opus>
[20/01/2026, 16:40:33] Lucas Ferreira: Envio o projeto preliminar da cozinha e dos banheiros.
\u200e<anexado: Projeto-preliminar-cozinha.pdf>
[22/01/2026, 09:05:12] Marina Costa: Solicito revisão do projeto: a ilha ficou 8 cm maior que o vão combinado com a marcenaria.
[28/01/2026, 15:10:44] Lucas Ferreira: Envio o projeto revisado R1, com a ilha ajustada.
\u200e<anexado: Projeto-revisado-R1.pdf>
[03/02/2026, 10:15:02] Carlos Mendes: Solicito nova revisão: o cliente quer a cuba deslocada 5 cm.
[10/02/2026, 18:00:27] Lucas Ferreira: Envio o projeto revisado R2 e o memorial descritivo.
\u200e<anexado: Memorial-descritivo.docx>
[11/02/2026, 09:40:15] Paulo Ribeiro: Projeto aprovado pela engenharia e pela arquitetura. Pode seguir para produção.
[02/03/2026, 14:00:08] Helena Duarte: Material entregue na obra hoje. A marcenaria não liberou a frente da cozinha.
[02/03/2026, 15:20:41] Helena Duarte: Interferência de obra: contrapiso irregular na área molhada. A instalação ficou impedida neste trecho. Segue o vídeo.
\u200e<anexado: video-contrapiso.mp4>
[04/03/2026, 08:30:19] Helena Duarte: A equipe de instalação entrou na obra hoje, nos banheiros. A cozinha segue aguardando a marcenaria.
[05/03/2026, 11:10:55] Helena Duarte: Interferência: o ponto de água da cozinha está fora de posição.
\u200e<anexado: foto-ponto-hidraulico.jpg>
[09/03/2026, 16:00:03] Carlos Mendes: A obra corrigiu o ponto de água e o contrapiso. Frente liberada.
[12/03/2026, 17:45:36] Helena Duarte: Serviços de instalação concluídos nos banheiros e na cozinha. Validação final feita no local com o engenheiro. Falta o cliente devolver o termo assinado.
"""

LEIA_ME = """Exemplo fictício

A Obra 1001, a Família Almeida, a Construtora Horizonte e as pessoas desta
conversa não existem. O arquivo serve para testar a skill e para o Rogério
ver o formato, sem dados de cliente.

Não substitua este exemplo por uma obra real dentro do repositório público.
"""


def _pdf(caminho: Path, texto: str) -> None:
    fluxo = f"BT /F1 12 Tf 72 700 Td ({texto}) Tj ET".encode("ascii")
    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Count 1 /Kids [3 0 R] >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(fluxo)).encode("ascii") + b" >>\nstream\n" + fluxo + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    saida = bytearray(b"%PDF-1.4\n")
    offsets = []
    for indice, objeto in enumerate(objetos, start=1):
        offsets.append(len(saida))
        saida.extend(f"{indice} 0 obj\n".encode("ascii"))
        saida.extend(objeto)
        saida.extend(b"\nendobj\n")
    xref = len(saida)
    saida.extend(f"xref\n0 {len(objetos) + 1}\n".encode("ascii"))
    saida.extend(b"0000000000 65535 f \n")
    for offset in offsets:
        saida.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    saida.extend(
        f"trailer << /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii")
    )
    caminho.write_bytes(saida)


def _jpg(caminho: Path, legenda: str, cor: tuple[int, int, int]) -> None:
    from PIL import Image, ImageDraw

    imagem = Image.new("RGB", (640, 360), cor)
    desenho = ImageDraw.Draw(imagem)
    desenho.rectangle((24, 24, 616, 336), outline=(255, 255, 255), width=4)
    desenho.text((40, 160), legenda, fill=(255, 255, 255))
    imagem.save(caminho, format="JPEG", quality=85)


def _docx(caminho: Path, texto: str) -> None:
    from docx import Document

    documento = Document()
    documento.add_paragraph(texto)
    documento.save(caminho)


def _midia_com_ffmpeg(pasta: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    video = pasta / "video-contrapiso.mp4"
    audio = pasta / "audio-medicao.opus"
    if not ffmpeg:
        video.write_bytes(b"\x00\x00\x00\x18ftypmp42")
        audio.write_bytes(b"OggS")
        return
    subprocess.run(
        [
            ffmpeg, "-y", "-f", "lavfi", "-i", "color=c=0x3D4A55:s=320x240:d=1",
            "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono",
            "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
            str(video),
        ],
        capture_output=True, timeout=60, check=False,
    )
    subprocess.run(
        [
            ffmpeg, "-y", "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono",
            "-t", "1", "-c:a", "libopus", str(audio),
        ],
        capture_output=True, timeout=60, check=False,
    )
    if not video.exists() or video.stat().st_size == 0:
        video.write_bytes(b"\x00\x00\x00\x18ftypmp42")
    if not audio.exists() or audio.stat().st_size == 0:
        audio.write_bytes(b"OggS")


def criar_exemplo(pasta: Path) -> Path:
    pasta = Path(pasta)
    if pasta.exists():
        shutil.rmtree(pasta)
    bruto = pasta / "_bruto"
    bruto.mkdir(parents=True)
    (pasta / "LEIA-ME.txt").write_text(LEIA_ME, encoding="utf-8")
    (bruto / "_chat.txt").write_text(CHAT, encoding="utf-8")
    (pasta / "_chat.txt").write_text(CHAT, encoding="utf-8")
    _jpg(bruto / "chapa-lote-3.jpg", "EXEMPLO FICTICIO - CHAPA LOTE 3", (60, 70, 80))
    _jpg(bruto / "foto-ponto-hidraulico.jpg", "EXEMPLO FICTICIO - PONTO DE AGUA", (70, 80, 90))
    _pdf(bruto / "Projeto-preliminar-cozinha.pdf", "Projeto preliminar da cozinha. Obra 1001. Familia Almeida.")
    _pdf(bruto / "Projeto-revisado-R1.pdf", "Projeto revisado R1. Ilha ajustada.")
    _docx(bruto / "Memorial-descritivo.docx", "Memorial descritivo da Obra 1001. Na revisao R2 a cuba foi deslocada 5 cm.")
    _midia_com_ffmpeg(bruto)
    destino = pasta / "WhatsApp Chat - Obra 1001 Familia Almeida.zip"
    with zipfile.ZipFile(destino, "w", compression=zipfile.ZIP_DEFLATED) as arquivo:
        for item in sorted(bruto.iterdir()):
            arquivo.write(item, item.name)
    shutil.rmtree(bruto)
    return destino


def main() -> None:
    raiz = Path(__file__).resolve().parent / "obra-1001-familia-almeida"
    zip_path = criar_exemplo(raiz)
    print(zip_path)


if __name__ == "__main__":
    main()
