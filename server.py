import asyncio
import websockets
import json
import vgamepad as vg
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext

PORT = 8080
gamepad = vg.VX360Gamepad()

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except:
        return "127.0.0.1"
    finally:
        s.close()

# --- Логика сервера ---
async def handle_phone(websocket):
    log_to_gui("📱 Телефон подключен!")
    try:
        async for message in websocket:
            data = json.loads(message)
            steer = data.get("steer", 0)
            x_val = int(steer * 32767)
            gamepad.left_joystick(x_value=x_val, y_value=0)
            
            throttle = data.get("throttle", 0)
            if throttle > 0:
                gamepad.right_trigger(value=int(throttle * 255))
            else:
                gamepad.left_trigger(value=int(abs(throttle) * 255))
            gamepad.update()
    except websockets.exceptions.ConnectionClosed:
        log_to_gui("📱 Телефон отключен.")
        gamepad.reset()
        gamepad.update()

async def start_server():
    async with websockets.serve(handle_phone, "0.0.0.0", PORT):
        await asyncio.Future()

def run_server_thread():
    asyncio.run(start_server())

# --- Интерфейс программы ---
def log_to_gui(text):
    log_area.insert(tk.END, text + "\n")
    log_area.see(tk.END)

def start_app():
    ip = get_ip()
    ip_label.config(text=f"IP для подключения: {ip}")
    btn_start.config(state="disabled", text="СЕРВЕР РАБОТАЕТ...")
    log_to_gui(f"Сервер запущен на порту {PORT}")
    log_to_gui(f"Введите в приложении IP: {ip}")
    
    # Запускаем сервер в фоне
    t = threading.Thread(target=run_server_thread, daemon=True)
    t.start()

# Создаем окно
root = tk.Tk()
root.title("Гиро-Руль Сервер")
root.geometry("400x400")
root.configure(bg="#1E1E1E")

tk.Label(root, text="Управление ПК с телефона", fg="white", bg="#1E1E1E", font=("Arial", 14, "bold")).pack(pady=10)

ip_label = tk.Label(root, text="Нажмите Старт для запуска", fg="#00FF00", bg="#1E1E1E", font=("Arial", 12))
ip_label.pack(pady=5)

btn_start = tk.Button(root, text="СТАРТ", command=start_app, bg="#00FF00", fg="black", font=("Arial", 12, "bold"), width=20, height=2)
btn_start.pack(pady=10)

log_area = scrolledtext.ScrolledText(root, width=45, height=10, bg="#000000", fg="#00FF00", font=("Consolas", 9))
log_area.pack(pady=10)

root.mainloop()
