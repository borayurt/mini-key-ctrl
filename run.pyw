"""
MiniKeyCtrl - Konsol penceresi olmadan başlatıcı.

Bu dosyayı çift tıklayarak veya kısayol olarak kullanarak
programı arka planda başlatabilirsiniz.
(.pyw uzantısı Windows'ta pythonw.exe ile çalışır = konsol yok)
"""

import sys
import os

# Modüllerin bulunabilmesi için dizini ayarla
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main

main()
