import argparse
import csv
import importlib
import os
import re
import site
import sys
from pathlib import Path


PLUGIN_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0,str(PLUGIN_DIR))
from ddddocr_api import Api


def label_from_name(path, length):
    match = re.match(r"^([0-9A-Za-z]{%d})(?:[_-]|$)" % length, path.stem)
    return match.group(1) if match else ""


def main():
    parser = argparse.ArgumentParser(description="Evaluate ddddocr Umi plugin with exact CAPTCHA accuracy.")
    parser.add_argument("folder", type=Path)
    parser.add_argument("--length", type=int, default=4)
    parser.add_argument("--charset", default="lower_digits")
    parser.add_argument("--custom-chars", default="")
    parser.add_argument("--output", type=Path, default=Path("ddddocr_benchmark.tsv"))
    args = parser.parse_args()
    paths = sorted(p for p in args.folder.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp"))
    engine = Api({})
    local = {
        "charset": args.charset, "custom_chars": args.custom_chars,
        "expected_length": args.length, "decoder": "exact_beam", "beam_width": 12,
        "gray_chroma": 8, "gray_min_luma": 105, "gray_max_luma": 242,
    }
    rows = []
    totals = {mode: [0, 0] for mode in ("beta", "classic", "dual", "race")}
    for path in paths:
        label = label_from_name(path, args.length)
        data = path.read_bytes()
        for mode in totals:
            local["mode"] = mode
            error = engine.start(local)
            if error:
                raise RuntimeError(error)
            response = engine.runBytes(data)
            if response.get("code") not in (100,101):
                raise RuntimeError(response)
            result = response["data"][0] if response["code"]==100 else {"text":"", "score":0}
            text = result.get("text", "")
            correct = bool(label and text == label)
            rows.append({"filename": path.name, "label": label, "mode": mode,
                         "text": text, "score": "%.6f" % result.get("score", 0.0),
                         "correct": int(correct)})
            if label:
                totals[mode][1] += 1
                totals[mode][0] += int(correct)
    engine.stop()
    if not paths or not any(total for correct,total in totals.values()):
        raise RuntimeError("No labelled images; accuracy was NOT evaluated.")
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys() if rows else
                                ["filename", "label", "mode", "text", "score", "correct"], delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    for mode, (correct, total) in totals.items():
        print("%-8s %d/%d = %.2f%%" % (mode, correct, total, 100.0 * correct / total if total else 0.0))
    print("Result:", args.output.resolve())


if __name__ == "__main__":
    main()
