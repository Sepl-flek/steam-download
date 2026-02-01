import time
import os
import re
import winreg
import psutil
from datetime import datetime

CHECK_INTERVAL = 60
TOTAL_TIME = 5


def get_steam_path():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Valve\Steam"
        )
        steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
        return steam_path
    except FileNotFoundError:
        raise RuntimeError("Steam не найден в реестре")


def get_active_game(log_path):
    if not os.path.exists(log_path):
        return None, "unknown"

    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()[-200:]

    game_name = None
    status = "paused"

    for line in reversed(lines):
        if "Downloading" in line:
            status = "downloading"
        if "Paused" in line:
            status = "paused"

        match = re.search(r'AppID (\d+).*"(.*)"', line)
        if match:
            game_name = match.group(2)
            break

    return game_name, status


def get_steam_download_speed():
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and 'steam' in proc.info['name'].lower():
                io1 = proc.io_counters()
                time.sleep(1)
                io2 = proc.io_counters()

                bytes_written = io2.write_bytes - io1.write_bytes
                speed_mb = bytes_written / 1024 / 1024
                return max(speed_mb, 0)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return 0.0



def main():
    steam_path = get_steam_path()
    content_log = os.path.join(steam_path, "logs", "content_log.txt")

    print("Steam download monitor started\n")

    for minute in range(1, TOTAL_TIME + 1):
        game, status = get_active_game(content_log)
        speed = get_steam_download_speed()

        print(f"[{datetime.now().strftime('%H:%M:%S')}] "
              f"Минута {minute}/5")
        print(f"Игра: {game or 'не определена'}")
        print(f"Статус: {status}")
        print(f"Скорость: {speed:.2f} MB/s\n")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
