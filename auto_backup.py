import time
import subprocess
import os
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class BackupHandler(FileSystemEventHandler):
    def __init__(self, debounce_seconds=10):
        self.debounce_seconds = debounce_seconds
        self.timer = None
        self._lock = threading.Lock()

    def on_any_event(self, event):
        # Ignore changes inside the .git directory or auto_backup.py itself
        if '.git' in event.src_path or 'auto_backup.py' in event.src_path:
            return
            
        if event.is_directory:
            return

        print(f"[!] Değişiklik algılandı: {event.src_path}")
        self.trigger_backup()

    def trigger_backup(self):
        with self._lock:
            # Cancel the previous timer if it exists
            if self.timer is not None:
                self.timer.cancel()
            
            # Start a new timer to wait before pushing (debounce to avoid multiple commits on single save)
            self.timer = threading.Timer(self.debounce_seconds, self.perform_backup)
            self.timer.start()

    def perform_backup(self):
        print("GitHub'a yedekleniyor...")
        try:
            # Check if there are any changes to commit
            status = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
            if not status.stdout.strip():
                print("Değişiklik yok, yedekleme atlandı.")
                return

            subprocess.run(['git', 'add', '.'], check=True, capture_output=True, text=True)
            subprocess.run(['git', 'commit', '-m', 'Auto backup: Değişiklikler kaydedildi'], check=True, capture_output=True, text=True)
            subprocess.run(['git', 'push'], check=True, capture_output=True, text=True)
            print("✅ Başarıyla GitHub'a yedeklendi!")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Yedekleme sırasında hata oluştu.")
            if e.stderr:
                print(f"Detay: {e.stderr}")

if __name__ == "__main__":
    path = os.path.dirname(os.path.abspath(__file__))
    
    # Check if git is initialized
    if not os.path.exists(os.path.join(path, '.git')):
        print("HATA: Bu klasör bir Git projesi değil!")
        print("Lütfen önce 'git init' yapıp projenizi GitHub'a bağlayın.")
        exit(1)

    event_handler = BackupHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    
    print(f"🔍 Klasör izleniyor: {path}")
    print("Herhangi bir dosya değiştiğinde otomatik olarak 10 saniye bekleyip GitHub'a gönderilecek.")
    print("Durdurmak için arka planda çalışan bu pencereyi kapatın veya CTRL+C yapın.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nİzleme durduruldu.")
    observer.join()
