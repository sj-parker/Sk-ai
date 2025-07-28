#!/usr/bin/env python3
"""
Скрипт для запуска интегрированной системы VRM + Ассистент
"""

import subprocess
import sys
import os
import time
import threading
import signal
import webbrowser
from pathlib import Path

class IntegratedSystem:
    def __init__(self):
        self.processes = []
        self.running = True
        
        # Настройки
        self.assistant_dir = Path("assistant")
        self.vrm_dir = Path("VRMoverlay")
        
        # Проверяем наличие необходимых файлов
        self.check_requirements()
        
    def check_requirements(self):
        """Проверяет наличие необходимых файлов и зависимостей"""
        print("🔍 Проверка требований...")
        
        # Проверяем папку ассистента
        if not self.assistant_dir.exists():
            print("❌ Папка 'assistant' не найдена")
            sys.exit(1)
            
        if not (self.assistant_dir / "main.py").exists():
            print("❌ Файл 'assistant/main.py' не найден")
            sys.exit(1)
            
        # Проверяем папку VRM
        if not self.vrm_dir.exists():
            print("❌ Папка 'VRMoverlay' не найдена")
            sys.exit(1)
            
        if not (self.vrm_dir / "package.json").exists():
            print("❌ Файл 'VRMoverlay/package.json' не найден")
            sys.exit(1)
            
        print("✅ Все требования выполнены")
        
    def start_assistant(self):
        """Запускает ассистента"""
        print("🤖 Запуск ассистента...")
        try:
            process = subprocess.Popen(
                [sys.executable, "main.py"],
                cwd=self.assistant_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes.append(("assistant", process))
            print("✅ Ассистент запущен")
            return process
        except Exception as e:
            print(f"❌ Ошибка запуска ассистента: {e}")
            return None
            
    def start_vrm(self):
        """Запускает VRM приложение"""
        print("🎭 Запуск VRM приложения...")
        try:
            # Проверяем, установлены ли зависимости
            if not (self.vrm_dir / "node_modules").exists():
                print("📦 Установка зависимостей VRM...")
                subprocess.run(["npm", "install"], cwd=self.vrm_dir, check=True)
                
            process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=self.vrm_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes.append(("vrm", process))
            print("✅ VRM приложение запущено")
            return process
        except Exception as e:
            print(f"❌ Ошибка запуска VRM: {e}")
            return None
            
    def open_browser(self):
        """Открывает браузер с VRM приложением"""
        print("🌐 Открытие браузера...")
        time.sleep(3)  # Ждем запуска сервера
        try:
            webbrowser.open("http://localhost:3000")
            print("✅ Браузер открыт")
        except Exception as e:
            print(f"⚠️ Не удалось открыть браузер: {e}")
            
    def monitor_processes(self):
        """Мониторит процессы и выводит логи"""
        while self.running:
            for name, process in self.processes:
                if process.poll() is not None:
                    print(f"⚠️ Процесс {name} завершился с кодом {process.returncode}")
                    if self.running:
                        print(f"🔄 Перезапуск {name}...")
                        if name == "assistant":
                            self.start_assistant()
                        elif name == "vrm":
                            self.start_vrm()
            time.sleep(1)
            
    def signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения"""
        print("\n🛑 Получен сигнал завершения...")
        self.running = False
        self.stop_all()
        
    def stop_all(self):
        """Останавливает все процессы"""
        print("🛑 Остановка всех процессов...")
        for name, process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ Процесс {name} остановлен")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"⚠️ Процесс {name} принудительно остановлен")
            except Exception as e:
                print(f"❌ Ошибка остановки {name}: {e}")
                
    def run(self):
        """Запускает всю систему"""
        print("🚀 Запуск интегрированной системы VRM + Ассистент")
        print("=" * 50)
        
        # Устанавливаем обработчик сигналов
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Запускаем процессы
        assistant_process = self.start_assistant()
        if not assistant_process:
            print("❌ Не удалось запустить ассистента")
            return
            
        vrm_process = self.start_vrm()
        if not vrm_process:
            print("❌ Не удалось запустить VRM")
            self.stop_all()
            return
            
        # Запускаем мониторинг в отдельном потоке
        monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
        monitor_thread.start()
        
        # Открываем браузер
        browser_thread = threading.Thread(target=self.open_browser, daemon=True)
        browser_thread.start()
        
        print("\n🎉 Система запущена!")
        print("📱 VRM приложение: http://localhost:3000")
        print("📊 Мониторинг ассистента: http://localhost:31994")
        print("🖼️ Overlay: http://localhost:31991")
        print("\n💡 Нажмите Ctrl+C для остановки")
        
        # Ждем завершения
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
            
        self.stop_all()
        print("✅ Система остановлена")

def main():
    """Главная функция"""
    system = IntegratedSystem()
    system.run()

if __name__ == "__main__":
    main() 