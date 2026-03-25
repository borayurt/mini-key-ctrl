@echo off
echo ============================================
echo   MiniKeyCtrl - Kurulum
echo ============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi! Lutfen Python 3.8+ yukleyin.
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] Bagimliliklar yukleniyor...
pip install -r requirements.txt
if errorlevel 1 (
    echo [HATA] Bagimliliklar yuklenemedi!
    pause
    exit /b 1
)

echo.
echo [2/3] Interception driver kontrol ediliyor...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "try { $fs = [System.IO.File]::Open('\\\\.\\interception00', 'Open', 'Read', 'ReadWrite'); $fs.Close(); exit 0 } catch { exit 1 }"
if errorlevel 1 (
    echo [UYARI] Interception driver erisilebilir degil.
    echo.
    echo Cihaz bazli remap icin surucuyu kurmaniz gerekiyor:
    echo   1. https://github.com/oblitum/Interception adresinden paketi indirin
    echo   2. Yonetici Komut Istemi acin
    echo   3. install-interception.exe /install komutunu calistirin
    echo   4. Bilgisayari yeniden baslatin
    echo.
) else (
    echo [OK] Interception driver erisilebilir.
)

echo.
echo [3/3] Kurulum tamamlandi!
echo.
echo Programi baslatmak icin:
echo   python main.py
echo.
echo Not: Ilk calistirmada yonetici haklari istenebilir.
echo.
pause
