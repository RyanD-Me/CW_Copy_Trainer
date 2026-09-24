# CW Copy Trainer

CW（電信）の聞き取り練習アプリ。`index.html` をブラウザで開くだけで使えます。

- 通常練習: 英数字・略符号・実在局コールサイン・各コンテストのナンバーを繰り返し再生して聞き取り
- スコアアタック: 練習 / コールサイン / コンテストナンバー / コンテストの4モード、モード別ハイスコア

開発者向けの仕様・ルールは `CLAUDE.md` を参照してください。

```
python3 tools/build_data.py          # data/ から出題データを再生成して index.html に埋め込む
python3 tools/build_data.py --check  # 埋め込みデータが最新か確認
node tests/smoke.js                  # Playwright で簡易動作確認
```
