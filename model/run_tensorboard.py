#!/usr/bin/env python3
"""Start TensorBoard when `python3 -m tensorboard` fails (no __main__ in package).

Usage (from repo root):
  python3 model/run_tensorboard.py --logdir model/tensorboard
"""

from __future__ import annotations

import sys

# absl/tensorboard expect a stable program name
if __name__ == "__main__":
    sys.argv[0] = "tensorboard"
    from tensorboard.main import run_main

    run_main()
