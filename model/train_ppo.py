#!/usr/bin/env python3
"""Train PPO on PandemicEnv (run from repo root: python model/train_ppo.py).

Curves (TensorBoard): add --tensorboard, then run:
  python3 model/run_tensorboard.py --logdir model/tensorboard
and open http://localhost:6006
(On some Mac installs, `tensorboard` and `python3 -m tensorboard` both fail; this wrapper works.)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stable_baselines3 import PPO

from model.env import PandemicEnv


def main() -> None:
    parser = argparse.ArgumentParser(description="PPO training for PandemicEnv")
    parser.add_argument("--timesteps", type=int, default=100_000, help="Total env steps")
    parser.add_argument(
        "--save",
        type=str,
        default="model/checkpoints/ppo_pandemic",
        help="Path prefix (SB3 appends .zip)",
    )
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--difficulty", type=int, default=0)
    parser.add_argument("--num-players", type=int, default=2)
    parser.add_argument(
        "--max-episode-steps",
        type=int,
        default=None,
        metavar="N",
        help="Optional cap on steps per episode (truncated). Speeds up training episodes.",
    )
    parser.add_argument(
        "--tensorboard",
        action="store_true",
        help="Write TensorBoard logs under --tensorboard-log (see docstring).",
    )
    parser.add_argument(
        "--tensorboard-log",
        type=str,
        default="model/tensorboard",
        help="Log directory when --tensorboard is set",
    )
    args = parser.parse_args()

    env = PandemicEnv(
        difficulty=args.difficulty,
        num_players=args.num_players,
        max_episode_steps=args.max_episode_steps,
    )

    tb = args.tensorboard_log if args.tensorboard else None
    if tb:
        Path(tb).mkdir(parents=True, exist_ok=True)

    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=256,
        n_epochs=10,
        gamma=0.99,
        verbose=1,
        seed=args.seed,
        tensorboard_log=tb,
    )
    model.learn(total_timesteps=args.timesteps, progress_bar=True)

    out = Path(args.save)
    out.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(out))
    print(f"Saved model to {out}.zip")


if __name__ == "__main__":
    main()
