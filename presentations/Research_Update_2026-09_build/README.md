# Research update deck, September 2026

`..\Research_Update_Slides_2026-09.pptx`: 12 slides on the NMSU template, speaker notes on every slide.
`..\Research_Update_Slides_2026-09_preview.pdf`: LibreOffice render for quick viewing (PowerPoint is the reference).

Rebuild (python-pptx, matplotlib, pandas, Pillow):

    python make_figs.py    # figures from saved result files (Julia Qube CSV, DILISIC reference, Basilisk trace)
    python build_deck.py   # writes ..\Research_Update_Slides_2026-09_rebuilt.pptx; reads 062526_biwm_ECE.pptx, never writes it

`figs/omni_model.png` (MuJoCo render), `figs/toe_fig1_native.jpeg`, `figs/acc_fig1_arch.png` and
`figs/comrob_fig1_hexa.png` (cropped from the paper PDFs) are inputs, already present.
Every number on the slides is copied from a named source; the list is in the notes of the last slide.

## Speech and Q&A

`speech_content.py` holds the per-slide script, Q&A, numbers and glossary (single source).

    python apply_notes.py         # writes the script into the speaker notes (…_with_speech_rebuilt.pptx)
    python build_study_guide.py   # printable guide (…_Speech_and_QA_Guide_rebuilt.pdf); thumbnails in render2/
