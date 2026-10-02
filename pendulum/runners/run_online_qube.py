from __future__ import annotations

import sys
from pathlib import Path


PLATFORM_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATFORM_ROOT / "src"))

from servo_pendulum_snn.online_runner import main


if __name__ == "__main__":
    main()
