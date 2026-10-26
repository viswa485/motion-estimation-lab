"""Create compact plots and a markdown summary from benchmark CSV output."""
from __future__ import annotations
import argparse
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

def create_report(csv_path: Path, output_dir: Path) -> tuple[Path, Path, Path]:
    data = pd.read_csv(csv_path)
    required = {"algorithm", "avg_candidates_per_block", "avg_sad_per_pixel", "mc_psnr_db", "elapsed_ms"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {sorted(missing)}")
    output_dir.mkdir(parents=True, exist_ok=True)
    candidate_plot = output_dir / "candidate_evaluations.svg"
    quality_plot = output_dir / "quality_complexity.svg"
    summary_path = output_dir / "SUMMARY.md"
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.bar(data["algorithm"], data["avg_candidates_per_block"])
    ax.set_title("Motion-search complexity")
    ax.set_ylabel("Mean candidate evaluations per block")
    ax.set_xlabel("Search algorithm")
    ax.tick_params(axis="x", rotation=15)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(candidate_plot, dpi=160)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.scatter(data["avg_candidates_per_block"], data["mc_psnr_db"], s=75)
    for _, row in data.iterrows():
        ax.annotate(str(row["algorithm"]), (row["avg_candidates_per_block"], row["mc_psnr_db"]),
                    xytext=(5, 5), textcoords="offset points", fontsize=8)
    ax.set_title("Quality–complexity proxy")
    ax.set_xlabel("Mean candidate evaluations per block (lower is faster proxy)")
    ax.set_ylabel("Motion-compensated PSNR (dB)")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(quality_plot, dpi=160)
    plt.close(fig)
    sorted_data = data.sort_values("avg_candidates_per_block")
    table = sorted_data[["algorithm", "avg_candidates_per_block", "avg_sad_per_pixel", "mc_psnr_db", "elapsed_ms"]].to_markdown(index=False, floatfmt=".4f")
    summary_path.write_text(
        "# Benchmark summary\n\n"
        "This report measures block-matching search cost and motion-compensated reconstruction quality "
        "on the supplied grayscale frame pair. PSNR is a motion-compensation proxy, **not encoded-video PSNR or BD-rate**.\n\n"
        f"Input CSV: {csv_path}\n\n"
        "## Results\n\n" + table +
        "\n\n## Interpretation checklist\n\n"
        "- Compare candidate evaluations before interpreting wall-clock time; runtime is sensitive to the machine and build.\n"
        "- Full search is the exact minimum-SAD baseline within the configured square window.\n"
        "- Fast searches can miss that minimum; quantify the quality/complexity trade-off across multiple clips and search ranges.\n"
        "- These measurements do not demonstrate encoder bitrate savings. Validate in a complete encoder before making that claim.\n",
        encoding="utf-8",
    )
    return candidate_plot, quality_plot, summary_path

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path, nargs="?", default=Path("results/benchmark.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("results/report"))
    args = parser.parse_args()
    for path in create_report(args.csv, args.output_dir):
        print(path)

if __name__ == "__main__":
    main()
