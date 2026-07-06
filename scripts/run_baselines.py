#!/usr/bin/env python3
"""Compare baseline architectures for paper ablation table."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import argparse
import json
from pathlib import Path

from xstep_ml.config import ROOT


def parse_args():
    p = argparse.ArgumentParser(description="Run ulcer model architecture ablations")
    p.add_argument("--task", choices=["ulcer", "heatmap"], default="ulcer")
    p.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "ablations")
    p.add_argument("--epochs", type=int, default=30)
    p.add_argument("--quick", action="store_true", help="Fewer epochs for smoke test")
    return p.parse_args()


def main():
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    epochs = 5 if args.quick else args.epochs

    if args.task == "ulcer":
        architectures = ["ulcer_cnn", "resnet50", "efficientnet_b0"]
        losses = ["cross_entropy", "focal", "ordinal"]
        results = {}
        for arch in architectures:
            for loss in losses:
                key = f"{arch}_{loss}"
                out = args.output_dir / "ulcer" / key
                print(f"\n>>> Running {key}")
                import subprocess
                import sys

                cmd = [
                    sys.executable,
                    str(ROOT / "scripts" / "train_ulcer.py"),
                    "--architecture", arch,
                    "--loss", loss,
                    "--epochs", str(epochs),
                    "--output-dir", str(out),
                    "--image-size", "64" if arch == "ulcer_cnn" else "224",
                ]
                subprocess.run(cmd, check=False)
                eval_path = out / "evaluation.json"
                if eval_path.exists():
                    with open(eval_path) as f:
                        results[key] = json.load(f)
        with open(args.output_dir / "ulcer_ablation.json", "w") as f:
            json.dump(results, f, indent=2)
    else:
        architectures = ["heat_cnn", "resnet50", "efficientnet_b0"]
        results = {}
        for arch in architectures:
            key = arch
            out = args.output_dir / "heatmap" / key
            print(f"\n>>> Running {key}")
            import subprocess
            import sys

            cmd = [
                sys.executable,
                str(ROOT / "scripts" / "train_heatmap.py"),
                "--architecture", arch,
                "--epochs", str(epochs),
                "--output-dir", str(out),
            ]
            subprocess.run(cmd, check=False)
            eval_path = out / "evaluation.json"
            if eval_path.exists():
                with open(eval_path) as f:
                    results[key] = json.load(f)
        with open(args.output_dir / "heatmap_ablation.json", "w") as f:
            json.dump(results, f, indent=2)

    print(f"\nAblations saved under {args.output_dir}")


if __name__ == "__main__":
    main()
