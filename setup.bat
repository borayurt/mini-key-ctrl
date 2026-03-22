@echo off
echo ============================================
echo   MiniKeyCtrl - Kurulum
echo ============================================
echo.

REM Python kontrolu
python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi! Lutfen Python 3.8+ yukleyin.
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/2] Bagimliliklar yukleniyor...
pip install -r requirements.txt
if errorlevel 1 (
    echo [HATA] Bagimliliklar yuklenemedi!
    pause
    exit /b 1
)

echo.
echo [2/2] Kurulum tamamlandi!
echo.
echo Programi baslatmak icin:
echo   python main.py
echo.
echo Not: Ilk calistirmada yonetici haklari istenebilir.
echo.
pause
