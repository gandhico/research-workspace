"""PAL availability matrix (Bridge-1 path). Run:
    set PYTHONPATH=C:\\Quanser\\0_libraries\\python
    echo 2 | python check_pal_matrix.py
The piped "2" pre-answers pal.products.qcar's interactive QCar1/QCar2 prompt
(it blocks at import otherwise — see VALIDATION_STATUS.md finding F3).
Requires the official quanser API wheels:
    pip install --no-index --find-links "C:\\Program Files\\Quanser\\QUARC\\python" quanser-api
"""
import importlib

MODS = ["qube", "aero2", "qarm", "qarm_mini", "qbot_platform", "qbot",
        "qcar", "qdrone2", "actuators", "sensors"]

def main():
    try:
        from quanser.hardware import HIL  # noqa: F401
        print("quanser.hardware.HIL          OK")
    except Exception as e:
        print(f"quanser.hardware.HIL          FAIL: {e}")
        return
    for m in MODS:
        try:
            importlib.import_module("pal.products." + m)
            print(f"pal.products.{m:16s} OK")
        except EOFError:
            print(f"pal.products.{m:16s} BLOCKED: interactive prompt at import")
        except Exception as e:
            print(f"pal.products.{m:16s} FAIL: {type(e).__name__}: {str(e)[:60]}")

if __name__ == "__main__":
    main()
