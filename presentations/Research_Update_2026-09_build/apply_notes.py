"""Write the full speech + Q&A (speech_content.py) into the deck's speaker notes."""
from pathlib import Path
import sys

from pptx import Presentation

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from speech_content import SLIDES, notes_text  # noqa: E402

SRC = HERE.parent / "Research_Update_Slides_2026-09_rebuilt.pptx"   # output of build_deck.py
DST = HERE.parent / "Research_Update_Slides_2026-09_with_speech_rebuilt.pptx"

prs = Presentation(str(SRC))
assert len(prs.slides) == len(SLIDES), (len(prs.slides), len(SLIDES))
for slide, sl in zip(prs.slides, SLIDES):
    title = slide.shapes.title.text_frame.text
    assert title == sl["title"], (title, sl["title"])
    slide.notes_slide.notes_text_frame.text = notes_text(sl)
prs.save(str(DST))
print("saved", DST.name, "with notes on", len(SLIDES), "slides")
