#!/usr/bin/env python3
"""index.html に埋め込んでいる出題データを data/ のファイルから作り直す。

使い方:  python3 tools/build_data.py        （index.html を上書き更新）
         python3 tools/build_data.py --check（差分があれば終了コード1）

対象:
  - ACAG_NUMBERS : 全市全郡の市郡区ナンバー（data/jcc-list.txt, jcg-list.txt, ku-list.txt）
  - CALLS_J / CALLS_7 : 実在局コールサイン（data/MASTER.txt = Super Check Partial）
  - PAIRS_ALLJA / PAIRS_FD / PAIRS_ACAG : 実在の「コールサイン:ナンバー」の組（data/logs/ の公開ログ）
      ALL JA と 6m AND DOWN は同じナンバー体系なのでまとめる。
      コールサインの形式・ナンバーの形式・エリア（/n か、コールのエリア数字。7K〜7N は関東）が
      合わないものは記入ミスとみなして捨てる。
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


# 都府県コード（市郡区ナンバーの先頭2桁と同じ）→ エリア。48 は小笠原（東京都）、01 は北海道
AREA_OF_PREF = {p: a for a, ps in {
    "1": "10 11 12 13 14 15 16 17 48", "2": "18 19 20 21", "3": "22 23 24 25 26 27",
    "4": "31 32 33 34 35", "5": "36 37 38 39", "6": "40 41 42 43 44 45 46 47",
    "7": "02 03 04 05 06 07", "8": "01", "9": "28 29 30", "0": "08 09"}.items() for p in ps.split()}
CALL_RE = re.compile(r"(J[A-S][0-9][A-Z]{1,3}|7[J-N][0-9][A-Z]{3})(/[0-9])?")  # 8J などの記念局は除く
LOGS = {"PAIRS_ALLJA": ["allja-2025", "allja-2026", "6d-2025"],
        "PAIRS_FD": ["fd-2025"],
        "PAIRS_ACAG": ["acag-2025"]}


def call_area(call):
    if "/" in call:
        return call.split("/")[1]
    return "1" if re.match(r"7[K-N]", call) else call[2]


def pairs(names, valid, num_area):
    out, dropped = set(), 0
    for name in names:
        for line in (DATA / "logs" / f"{name}.txt").read_text().split():
            call, _, num = line.upper().partition(",")
            if CALL_RE.fullmatch(call) and num in valid and num_area(num) == call_area(call):
                out.add(f"{call}:{num}")
            else:
                dropped += 1
    return sorted(out), dropped


def main():
    html = HTML.read_text()
    nums = acag_numbers()
    j, s = calls()
    pref = {f"{i:02d}" for i in range(2, 49)} | {str(i) for i in range(101, 115)}
    pref_area = lambda n: "8" if len(n) == 3 else AREA_OF_PREF[n]
    acag_area = lambda n: AREA_OF_PREF.get(n[:2])
    new = html
    for var, names in LOGS.items():
        acag = var == "PAIRS_ACAG"
        ps, dropped = pairs(names, set(nums) if acag else pref, acag_area if acag else pref_area)
        new, n = re.subn(r"var %s = '[^']*'\.split\(' '\);" % var,
                         lambda _: f"var {var} = '" + " ".join(ps) + "'.split(' ');", new)
        assert n == 1, f"{var} marker not found"
        print(f"{var}={len(ps)} (dropped {dropped})", end="  ")
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
