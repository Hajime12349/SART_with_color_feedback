import PyInstaller.__main__
import os

# 現在のディレクトリを取得
current_dir = os.path.dirname(os.path.abspath(__file__))

print("SARTアプリのEXE化を開始します...")

PyInstaller.__main__.run([
    'sart_app.py',
    '--onedir',                     # ディレクトリ形式で出力（軽量）
    '--windowed',                   # コンソールウィンドウを非表示
    '--name=SART_App',              # 実行ファイル名
    '--distpath=dist',              # 出力ディレクトリ
    '--workpath=build',             # 作業ディレクトリ
    '--specpath=.',                 # specファイルの場所
    '--clean',                      # ビルド前にクリーンアップ
    '--noconfirm',                  # 確認なしで上書き
    '--add-data=recoded_data;recoded_data',  # データディレクトリを含める
    '--hidden-import=psychopy',     # PsychoPyの隠れたインポート
    '--hidden-import=psychopy.visual',
    '--hidden-import=psychopy.core',
    '--hidden-import=psychopy.event',
    '--hidden-import=numpy',        # PsychoPyの依存関係
    '--hidden-import=scipy',
    '--hidden-import=matplotlib',
    '--hidden-import=PIL',
    '--hidden-import=pyglet',
    '--hidden-import=pygame',
    '--hidden-import=wx',
    '--hidden-import=psychtoolbox',
    '--collect-all=psychopy',       # PsychoPyの全モジュールを収集
    '--collect-all=numpy',
    '--collect-all=scipy',
    '--collect-all=matplotlib',
    '--collect-all=PIL',
    '--collect-all=pyglet',
    '--collect-all=pygame',
    '--collect-all=wx',
    '--collect-all=psychtoolbox',
])

print("ビルドが完了しました。")
print("distフォルダ内のSART_App.exeを実行してください。")
