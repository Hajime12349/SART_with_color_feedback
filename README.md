## SART (Sustained Attention to Response Task) 実験アプリ

### セットアップ
1. Python 3.9+ を用意（Windows 10/11 推奨）
2. 仮想環境を作成し有効化（任意）
3. 依存関係をインストール
```bash
pip install -r requirements.txt
```

### 実行方法
```bash
python sart_app.py
```

### 仕様サマリ
- 刺激: 1〜9 の数字（ターゲットは "3"）
- 表示: 黒背景・白文字・中央表示・Symbol フォント
- フォントサイズ: 48, 72, 94, 100, 120 をランダム
- タイミング: 数字 250ms → マスク 900ms（1 試行 1150ms）
- 試行: 練習 18（内ターゲット 2）、本試行 225（内ターゲット 25）
- 応答: スペースキー（3 のときは押さない）
- マスク色: 正解=緑、不正解=赤
- フルスクリーン実行、開始・練習終了・本試行開始画面あり、練習終了画面で ESC 可

### データ出力
- `recoded_data/` に JSON を保存
  - `raw_main_YYYYmmdd_HHMMSS.json`: 試行ごとの記録（digit, is_target, responded, rt_ms, correct）
  - `summary_main_YYYYmmdd_HHMMSS.json`: 集計（commission/omission、平均RT、SD、直前/直後4試行RT）

### 注意
- 時間精度のため、他アプリを閉じ、外部モニタやリフレッシュレートを固定してください。
- PsychoPy は初回実行時に追加コンポーネントをダウンロードする場合があります。

