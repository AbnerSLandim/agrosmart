from __future__ import annotations

import json
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps
from moviepy import AudioFileClip, ImageClip, concatenate_videoclips


ROOT = Path(__file__).resolve().parent.parent
VIDEO_DIR = ROOT / "video"
FRAMES_DIR = VIDEO_DIR / "frames"
OUTPUT = ROOT / "entrega" / "AgroSmart_Sprint6_video.mp4"
W, H = 1280, 720
BG = "#0f1f17"
PANEL = "#183024"
GREEN = "#55b765"
MUTED = "#b8c8bc"
WHITE = "#f4f7f4"
ORANGE = "#ffad32"
RED = "#ef4444"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "seguisb.ttf" if bold else "segoeui.ttf"
    return ImageFont.truetype(str(Path("C:/Windows/Fonts") / name), size)


def fit_image(path: Path, box: tuple[int, int, int, int]) -> Image.Image:
    x0, y0, x1, y1 = box
    image = Image.open(path).convert("RGB")
    contained = ImageOps.contain(image, (x1 - x0, y1 - y0), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (x1 - x0, y1 - y0), "white")
    canvas.paste(contained, ((canvas.width - contained.width) // 2, (canvas.height - contained.height) // 2))
    return canvas


def base_slide(title: str, index: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((35, 28, W - 35, H - 28), 22, fill=PANEL, outline="#2c5a3b", width=2)
    draw.text((70, 55), title, font=font(38, True), fill=WHITE)
    draw.text((70, H - 62), "AgroSmart • FIAP Fase 6 • dados sintéticos e simulação", font=font(20), fill=MUTED)
    draw.text((W - 110, H - 62), f"{index}/7", font=font(20, True), fill=GREEN)
    return image, draw


def bullets(draw: ImageDraw.ImageDraw, items: list[str], x: int, y: int, width: int, size: int = 26) -> None:
    body = font(size)
    line_h = int(size * 1.45)
    cursor = y
    chars = max(22, int(width / (size * 0.55)))
    for item in items:
        wrapped = textwrap.wrap(item, width=chars)
        draw.ellipse((x, cursor + 10, x + 10, cursor + 20), fill=GREEN)
        for line_no, line in enumerate(wrapped):
            draw.text((x + 25, cursor + line_no * line_h), line, font=body, fill=WHITE)
        cursor += max(1, len(wrapped)) * line_h + 14


def paste_card(image: Image.Image, source: Path, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    card = fit_image(source, box)
    image.paste(card, (x0, y0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(box, 14, outline="#5f8069", width=3)


def create_frames() -> list[Path]:
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    frames: list[Path] = []

    image, draw = base_slide("AgroSmart — visão integrada", 1)
    paste_card(image, ROOT / "docs" / "arquitetura.png", (80, 125, 1200, 625))
    frames.append(save(image, "01_abertura.png"))

    image, draw = base_slide("Sensores e bancada TinkerCad", 2)
    sensors = [
        ROOT / "sensores" / "prints" / "01_circuito.jpg",
        ROOT / "sensores" / "prints" / "02_normal_solo_umido.jpg",
        ROOT / "sensores" / "prints" / "03_moderado_solo_secando.jpg",
        ROOT / "sensores" / "prints" / "04_alto_solo_seco.jpg",
    ]
    boxes = [(70, 125, 620, 410), (660, 125, 1210, 285), (660, 305, 925, 545), (945, 305, 1210, 545)]
    for source, box in zip(sensors, boxes):
        paste_card(image, source, box)
    bullets(draw, ["Umidade e temperatura", "LEDs por nível de risco", "Buzzer para alerta local", "34 observações seriais integradas"], 95, 445, 500, 23)
    frames.append(save(image, "02_sensores.png"))

    image, draw = base_slide("Pipeline e qualidade dos dados", 3)
    draw.rounded_rectangle((80, 135, 1200, 565), 18, fill="#10281a", outline="#4c7a58", width=2)
    steps = [("1", "INGESTÃO"), ("2", "PROCESSAMENTO"), ("3", "AUTOMAÇÃO"), ("4", "DASHBOARD")]
    for idx, (num, label) in enumerate(steps):
        x = 120 + idx * 275
        draw.ellipse((x, 175, x + 76, 251), fill=GREEN)
        draw.text((x + 26, 185), num, font=font(34, True), fill=BG)
        draw.text((x - 20, 270), label, font=font(21, True), fill=WHITE)
        if idx < 3:
            draw.line((x + 90, 213, x + 245, 213), fill=ORANGE, width=6)
    draw.text((125, 360), "397 entradas", font=font(34, True), fill=WHITE)
    draw.text((470, 360), "394 válidas", font=font(34, True), fill=GREEN)
    draw.text((805, 360), "3 descartes auditáveis", font=font(34, True), fill=ORANGE)
    bullets(draw, ["duplicata", "umidade inválida", "sensor sem medição"], 820, 420, 330, 20)
    frames.append(save(image, "03_pipeline.png"))

    image, draw = base_slide("Motor de regras e ações propostas", 4)
    paste_card(image, ROOT / "dashboard" / "prints" / "figura_riscos_20261008.png", (610, 125, 1200, 610))
    bullets(draw, ["Alto: umidade < 18% ou temperatura ≥ 35 °C", "Moderado: umidade < 22% ou temperatura ≥ 30 °C", "Irrigado: propor irrigação", "Sem irrigação: propor notificação", "Nenhum atuador ou mensagem real"], 90, 145, 470, 25)
    frames.append(save(image, "04_automacao.png"))

    image, draw = base_slide("Dashboard e principais indicadores", 5)
    paste_card(image, ROOT / "dashboard" / "prints" / "figura_umidade_20261008.png", (70, 135, 760, 610))
    draw.rounded_rectangle((805, 135, 1195, 610), 18, fill="#10281a", outline="#4c7a58", width=2)
    metrics = [("360", "leituras de campo", GREEN), ("32,1%", "umidade média", WHITE), ("38", "riscos altos", RED), ("46", "riscos moderados", ORANGE), ("6,1%", "mínimo no Talhão 03", RED)]
    y = 165
    for value, label, color in metrics:
        draw.text((845, y), value, font=font(39, True), fill=color)
        draw.text((845, y + 46), label, font=font(21), fill=MUTED)
        y += 88
    frames.append(save(image, "05_dashboard.png"))

    image, draw = base_slide("Leitura responsável dos resultados", 6)
    paste_card(image, ROOT / "dashboard" / "prints" / "figura_temperatura_20261008.png", (70, 135, 700, 610))
    bullets(draw, ["Campo com dados sintéticos", "Bancada TinkerCad simulada", "Linha do tempo da bancada artificial", "Ingestão ainda manual", "Resultados descrevem o cenário; não provam causalidade", "Limitações e procedência documentadas"], 750, 145, 420, 24)
    frames.append(save(image, "06_limites.png"))

    image, draw = base_slide("Entrega técnica", 7)
    draw.text((85, 145), "O que foi entregue", font=font(32, True), fill=GREEN)
    bullets(draw, ["Arquitetura e documentação", "Arduino, sensores e evidências do TinkerCad", "Dados brutos, validação e rastreabilidade", "Motor de regras e saídas em CSV", "Dashboard HTML/SVG offline", "13 testes automatizados"], 90, 205, 520, 26)
    draw.text((690, 145), "Próximas evoluções", font=font(32, True), fill=ORANGE)
    bullets(draw, ["Ingestão MQTT real", "Cadastro seguro de atuadores", "Validação agronômica dos parâmetros"], 695, 205, 450, 27)
    draw.rounded_rectangle((685, 430, 1160, 555), 18, fill="#10281a", outline=GREEN, width=2)
    draw.text((725, 458), "AgroSmart", font=font(45, True), fill=WHITE)
    draw.text((725, 512), "monitorar • analisar • agir com evidência", font=font(21), fill=MUTED)
    frames.append(save(image, "07_encerramento.png"))
    return frames


def save(image: Image.Image, name: str) -> Path:
    path = FRAMES_DIR / name
    image.save(path, quality=95)
    return path


def main() -> None:
    segments = json.loads((VIDEO_DIR / "narracao.json").read_text(encoding="utf-8"))
    frames = create_frames()
    clips = []
    total_duration = 0.0
    for segment, frame in zip(segments, frames):
        audio_path = VIDEO_DIR / "audio" / f"{segment['id']}.wav"
        audio = AudioFileClip(str(audio_path))
        duration = audio.duration + 0.35
        total_duration += duration
        clip = ImageClip(str(frame), duration=duration).with_audio(audio)
        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose")
    if not 180 <= total_duration <= 300:
        raise RuntimeError(f"Duração fora de 3–5 minutos: {total_duration:.1f}s")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    video.write_videofile(
        str(OUTPUT),
        fps=24,
        codec="libx264",
        audio_codec="aac",
        bitrate="2200k",
        audio_bitrate="160k",
        preset="medium",
        threads=4,
        logger="bar",
    )
    print(f"VIDEO={OUTPUT}")
    print(f"DURATION={total_duration:.2f}")
    for clip in clips:
        clip.close()
    video.close()


if __name__ == "__main__":
    main()
