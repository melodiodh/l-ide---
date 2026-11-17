# -*- coding: utf-8 -*-
"""Прогоняет все примеры (кроме оконных) через интерпретатор."""
import glob
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from lpp import Interpreter  # noqa: E402


def main():
    bad = 0
    for path in sorted(glob.glob(os.path.join(ROOT, "examples", "*.lpp"))):
        name = os.path.basename(path)
        if "графика" in name:
            print(f"[SKIP] {name} (открывает окна)")
            continue
        buf = io.StringIO()
        interp = Interpreter(output=buf.write, input_reader=lambda p="": "",
                             notice=buf.write)
        with open(path, encoding="utf-8") as f:
            source = f.read()
        try:
            interp.run(source)
            lines = buf.getvalue().strip().splitlines()
            print(f"[OK]   {name}  (строк вывода: {len(lines)})")
            for line in lines[:3]:
                print(f"       {line}")
        except Exception as e:
            bad += 1
            print(f"[FAIL] {name}: {type(e).__name__}: {e}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
