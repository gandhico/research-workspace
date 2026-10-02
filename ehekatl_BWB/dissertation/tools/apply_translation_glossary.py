"""Apply deterministic aerospace terminology corrections to English LaTeX."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "source_en"

# Long and specific phrases precede their component words.
REPLACEMENTS = (
    ("Control of the Push Vector", "thrust-vector control"),
    ("Push Vector Control", "Thrust Vector Control"),
    ("push vector control", "thrust-vector control"),
    ("Push Vector", "Thrust Vector"),
    ("push vector", "thrust vector"),
    ("push-to-weight", "thrust-to-weight"),
    ("Push-Weight", "thrust-to-weight ratio"),
    ("push-weight", "thrust-to-weight ratio"),
    ("push load", "thrust loading"),
    ("Push Load", "Thrust loading"),
    ("Minimum Push Required", "Minimum thrust required"),
    ("minimum push required", "minimum thrust required"),
    ("engines must give a minimum push", "engines must provide a minimum thrust"),
    ("leakage edge", "trailing edge"),
    ("Leaking edge", "Trailing edge"),
    ("leaking edge", "trailing edge"),
    ("supporting force", "lift"),
    ("support force", "lift"),
    ("support coefficient", "lift coefficient"),
    ("Support coefficient", "Lift coefficient"),
    ("resistance coefficient", "drag coefficient"),
    ("Resistance coefficient", "Drag coefficient"),
    ("trailer coefficient", "drag coefficient"),
    ("support generated", "lift generated"),
    ("sliding angle", "sideslip angle"),
    ("Sliding angle", "Sideslip angle"),
    ("drift angle", "sideslip angle"),
    ("angle of skid", "sideslip angle"),
    ("moment of heading", "pitching moment"),
    ("heading moments", "pitching moments"),
    ("head stability", "pitch stability"),
    ("timing coefficient", "pitching-moment coefficient"),
    ("pending negative", "negative slope"),
    ("positive pending", "positive slope"),
    ("arrowing", "sweep angle"),
    ("Arrowing", "Sweep angle"),
    ("arrow body", "body sweep"),
    ("diedron", "dihedral"),
    ("diedral", "dihedral"),
    ("Winking", "Yawing"),
    ("winking", "yawing"),
    ("Wink", "Yaw"),
    ("wink", "yaw"),
    ("Winging", "Rolling"),
    ("winging", "rolling"),
    ("alabating", "rolling"),
    ("Praise", "Roll"),
    ("praise", "roll"),
    ("Flattery", "Roll"),
    ("flattery", "roll"),
    ("Winnings", "Gains"),
    ("winnings", "gains"),
    ("Profits", "Gains"),
    ("profits", "gains"),
    ("eaves", "ailerons"),
    ("aleons", "ailerons"),
    ("aleon", "aileron"),
    ("alabeo", "roll"),
    ("guiñada", "yaw"),
    ("sustentación", "lift"),
    ("respectivamente", "respectively"),
    ("suelen  emplearse", "are usually used"),
    ("definidas", "defined"),
    ("grados", "degrees"),
    ("Proporcional", "Proportional"),
    ("Derivativa", "Derivative"),
    ("Carga Alar", "Wing loading"),
    ("Superficie Alar", "Wing area"),
    ("Empuje", "Thrust"),
    ("timon-elevador", "ruddervator"),
    ("Ala-Integrade", "BWB aircraft"),
)


def main() -> None:
    changed_files = 0
    replacement_count = 0
    for path in ROOT.rglob("*.tex"):
        original = path.read_text(encoding="utf-8")
        updated = original
        for old, new in REPLACEMENTS:
            count = updated.count(old)
            if count:
                updated = updated.replace(old, new)
                replacement_count += count
        if updated != original:
            path.write_text(updated, encoding="utf-8", newline="\n")
            changed_files += 1
    print({"changed_files": changed_files, "replacements": replacement_count})


if __name__ == "__main__":
    main()
