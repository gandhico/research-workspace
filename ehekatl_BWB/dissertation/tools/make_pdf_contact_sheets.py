"""Create numbered contact sheets for visual QA of every dissertation page."""

import argparse

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--pages", type=Path, default=ROOT / "tmp" / "pdfs" / "thesis_pages")
parser.add_argument("--output", type=Path, default=ROOT / "tmp" / "pdfs" / "thesis_contact_sheets")
args = parser.parse_args()
PAGES = args.pages
OUTPUT = args.output
OUTPUT.mkdir(parents=True, exist_ok=True)

files = sorted(PAGES.glob("page-*.png"), key=lambda item: int(item.stem.split("-")[-1]))
per_sheet = 12
columns = 3
thumb_width = 420
label_height = 28
font = ImageFont.load_default(size=18)

for offset in range(0, len(files), per_sheet):
    batch = files[offset:offset + per_sheet]
    thumbs = []
    for file in batch:
        image = Image.open(file).convert("RGB")
        height = round(image.height * thumb_width / image.width)
        thumbs.append(image.resize((thumb_width, height), Image.Resampling.LANCZOS))
    thumb_height = max(image.height for image in thumbs)
    rows = (len(thumbs) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * thumb_width, rows * (thumb_height + label_height)), "#d8d8d8")
    draw = ImageDraw.Draw(sheet)
    for index, (file, image) in enumerate(zip(batch, thumbs)):
        x = (index % columns) * thumb_width
        y = (index // columns) * (thumb_height + label_height)
        sheet.paste(image, (x, y + label_height))
        page_number = int(file.stem.split("-")[-1])
        draw.text((x + 8, y + 4), f"PDF page {page_number}", fill="black", font=font)
    first = int(batch[0].stem.split("-")[-1])
    last = int(batch[-1].stem.split("-")[-1])
    sheet.save(OUTPUT / f"contact_{first:03d}_{last:03d}.jpg", quality=92)

print({"pages": len(files), "contact_sheets": len(list(OUTPUT.glob('contact_*.jpg')))})
