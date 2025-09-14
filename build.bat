@echo off
echo SARTアプリのEXE化を開始します...

REM 仮想環境をアクティベート（必要に応じて）
if exist "sart2\Scripts\activate.bat" (
    echo 仮想環境をアクティベートしています...
    call sart2\Scripts\activate.bat
)

REM ビルドスクリプトを実行
echo ビルドスクリプトを実行しています...
python build_exe.py

echo.
echo ビルドが完了しました。
echo distフォルダ内のSART_App.exeを実行してください。
echo.
pause
