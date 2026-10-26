import asyncio
import websockets
import json
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
import pyautogui

PORT = 8080

# Отключаем паузу, чтобы клавиши нажимались мгновенно
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except:
        return "127.0.0.1"
    finally:
        s.close()

# Переменные для хранения текущего состояния
current_steer = 0
current_throttle = 0

async def handle_phone(websocket):
    global current_steer, current_throttle
    log_to_gui("📱 Телефон подключен!")
    try:
        async for message in websocket:
            data = json.loads(message)
            current_steer = data.get("steer", 0)
            current_throttle = data.get("throttle", 0)
            
            # Управление клавишами (влево/вправо)
            if current_steer < -0.2:
                pyautogui.keyDown('a') # Или 'left'
                pyautogui.keyUp('d')
                pyautogui.keyUp('right')
            elif current_steer > 0.2:
                pyautogui.keyDown('d') # Или 'right'
                pyautogui.keyUp('a')
                pyautogui.keyUp('left')
            else:
                pyautogui.keyUp('a')
                pyautogui.keyUp('d')
                pyautogui.keyUp('left')
                pyautogui.keyUp('right')

            # Управление газом (вперед/назад)
            if current_throttle > 0:
                pyautogui.keyDown('w') # Или 'up'
                pyautogui.keyUp('s')
                pyautogui.keyUp('down')
            elif current_throttle < -0.2: # Тормоз
                pyautogui.keyDown('s') # Или 'down'
                pyautogui.keyUp('w')
                pyautogui.keyUp('up')
            else:
                pyautogui.keyUp('w')
                pyautogui.keyUp('s')
                pyautogui.keyUp('up')
                pyautogui.keyUp('down')
                
    except websockets.exceptions.ConnectionClosed:
        log_to_gui("📱 Телефон отключен.")
        # Отпускаем все клавиши при отключении
        pyautogui.keyUp('a'); pyautogui.keyUp('d'); pyautogui.keyUp('w'); pyautogui.keyUp('s')
        pyautogui.keyUp('left'); pyautogui.keyUp('right'); pyautogui.keyUp('up'); pyautogui.keyUp('down')

async def start_server():
    async with websockets.serve(handle_phone, "0.0.0.0", PORT):
        await asyncio.Future()

def run_server_thread():
    asyncio.run(start_server())

def log_to_gui(text):
    log_area.insert(tk.END, text + "\n")
    log_area.see(tk.END)

def start_app():
    ip = get_ip()
    ip_label.config(text=f"IP для подключения: {ip}")
    btn_start.config(state="disabled", text="СЕРВЕР РАБОТАЕТ...")
    log_to_gui(f"Сервер запущен на порту {PORT}")
    log_to_gui(f"Введите в приложении IP: {ip}")
    log_to_gui("Включите игру и нажимайте на клавиши WASD (или стрелочки).")
    
    t = threading.Thread(target=run_server_thread, daemon=True)
    t.start()

root = tk.Tk()
root.title("Гиро-Руль Сервер (Клавиатура)")
root.geometry("420x420")
root.configure(bg="#1E1E1E")

tk.Label(root, text="Управление ПК (WASD)", fg="white", bg="#1E1E1E", font=("Arial", 14, "bold")).pack(pady=10)
ip_label = tk.Label(root, text="Нажмите Старт для запуска", fg="#00FF00", bg="#1E1E1E", font=("Arial", 12))
ip_label.pack(pady=5)

btn_start = tk.Button(root, text="СТАРТ", command=start_app, bg="#00FF00", fg="black", font=("Arial", 12, "bold"), width=20, height=2)
btn_start.pack(pady=10)

log_area = scrolledtext.ScrolledText(root, width=48, height=10, bg="#000000", fg="#00FF00", font=("Consolas", 9))
log_area.pack(pady=10)

root.mainloop()
