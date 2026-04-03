#!/usr/bin/env python3
"""Evaluate a saved PPO model on PandemicEnv (run from repo root).

Example:
  python3 model/eval_ppo.py --episodes 30 --max-episode-steps 1500
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stable_baselines3 import PPO

from model.env import PandemicEnv


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate PPO on PandemicEnv")
    parser.add_argument(
        "--model",
        type=str,
        default="model/checkpoints/ppo_pandemic",
        help="Path to model (.zip optional)",
    )
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--difficulty", type=int, default=0)
    parser.add_argument("--num-players", type=int, default=2)
    parser.add_argument(
        "--max-episode-steps",
        type=int,
        default=None,
        metavar="N",
        help="Cap steps per episode (truncated). Example: 1500 for faster eval.",
    )
    args = parser.parse_args()

    path = Path(args.model)
    zip_path = path if path.suffix == ".zip" else path.with_suffix(".zip")
    if not zip_path.is_file():
        raise SystemExit(f"Model not found: {zip_path}")

    env = PandemicEnv(
        difficulty=args.difficulty,
        num_players=args.num_players,
        max_episode_steps=args.max_episode_steps,
    )
    model = PPO.load(zip_path, env=env)
    if args.max_episode_steps:
        print(f"Time limit: {args.max_episode_steps} steps/episode (truncated runs count as truncated)", flush=True)

    outcomes: Counter[str] = Counter()
    lengths: list[int] = []
    rewards_sum: list[float] = []

    for ep in range(args.episodes):
        obs, _ = env.reset(seed=args.seed + ep)
        done = False
        steps = 0
        ep_reward = 0.0
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, term, trunc, _ = env.step(int(action))
            ep_reward += float(reward)
            steps += 1
            done = term or trunc

        if trunc and not term:
            out = "truncated"
        else:
            out = env.terminal_outcome() or "unknown"
        outcomes[out] += 1
        lengths.append(steps)
        rewards_sum.append(ep_reward)
        print(
            f"  episode {ep + 1}/{args.episodes}: {out} | steps={steps} | return={ep_reward:.1f}",
            flush=True,
        )

    wins = outcomes.get("win", 0)
    print(f"Episodes: {args.episodes} | wins: {wins} ({100.0 * wins / args.episodes:.1f}%)")
    print("Outcomes:", dict(outcomes))
    if lengths:
        print(f"Steps per episode: mean={sum(lengths)/len(lengths):.0f} min={min(lengths)} max={max(lengths)}")
    if rewards_sum:
        print(f"Return per episode: mean={sum(rewards_sum)/len(rewards_sum):.1f}")


if __name__ == "__main__":
    main()
