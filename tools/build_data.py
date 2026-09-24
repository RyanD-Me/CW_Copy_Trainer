#!/usr/bin/env python3
"""index.html に埋め込んでいる出題データを data/ のファイルから作り直す。

使い方:  python3 tools/build_data.py        （index.html を上書き更新）
         python3 tools/build_data.py --check（差分があれば終了コード1）

対象:
  - ACAG_NUMBERS : 全市全郡の市郡区ナンバー（data/jcc-list.txt, jcg-list.txt, ku-list.txt）
  - CALLS_J / CALLS_7 : 実在局コールサイン（data/MASTER.txt = Super Check Partial）
JARLのリストは Shift_JIS (cp932)。行頭 * は削除済み、区リストの「〜以前」行も削除済み。
政令指定都市（区リストに区がある市）は市番号を除外し、区番号のみを使う。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
HTML = ROOT / "index.html"


def read_cp932(name):
    return (DATA / name).read_bytes().decode("cp932", errors="replace").splitlines()


def acag_numbers():
    ku = [m.group(1) for l in read_cp932("ku-list.txt")
          if (m := re.match(r"^(\d{6})", l)) and "以前" not in l]
    parents = {k[:4] for k in ku}
    jcc = [m.group(2) for l in read_cp932("jcc-list.txt")
           if (m := re.match(r"^(\*?)\s+(\d{4}|\d{6})\s", l)) and not m.group(1)]
    jcg = [m.group(2) for l in read_cp932("jcg-list.txt")
           if (m := re.match(r"^(\*?)\s+(\d{5})\s", l)) and not m.group(1)]
    cities = [c for c in jcc if c not in parents]
    nums = cities + ku + jcg
    assert len(nums) == len(set(nums)), "duplicate numbers"
    return nums


def calls():
    lines = [l.strip().upper() for l in (DATA / "MASTER.txt").read_text(errors="replace").splitlines()]
    j = [l for l in lines if re.fullmatch(r"J[A-S][0-9][A-Z]{3}", l)]
    s = [l for l in lines if re.fullmatch(r"7[K-N][0-9][A-Z]{3}", l)]
    return j, s


def main():
    html = HTML.read_text()
    nums = acag_numbers()
    j, s = calls()
    new = html
    new, n1 = re.subn(r"var ACAG_NUMBERS = '[^']*'\.split\(' '\);",
                      lambda _: "var ACAG_NUMBERS = '" + " ".join(nums) + "'.split(' ');", new)
    new, n2 = re.subn(r"var CALLS_J = '[^']*'\.split\(' '\);",
                      lambda _: "var CALLS_J = '" + " ".join(j) + "'.split(' ');", new)
    new, n3 = re.subn(r"var CALLS_7 = '[^']*'\.split\(' '\);",
                      lambda _: "var CALLS_7 = '" + " ".join(s) + "'.split(' ');", new)
    assert (n1, n2, n3) == (1, 1, 1), "embedded data markers not found"
    print(f"ACAG_NUMBERS={len(nums)}  CALLS_J={len(j)}  CALLS_7={len(s)}")
    if "--check" in sys.argv:
        if new != html:
            print("index.html is out of date"); sys.exit(1)
        print("index.html is up to date"); return
    HTML.write_text(new)
    print("index.html updated")


if __name__ == "__main__":
    main()
