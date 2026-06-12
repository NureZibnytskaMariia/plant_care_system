#!/usr/bin/env python3
"""
Plant Care System - Arduino Data Bridge
"""

import serial
import requests
import time
import sys
from datetime import datetime
from decouple import config, UndefinedValueError

# ==================== КОНФІГУРАЦІЯ ====================

SERIAL_PORT = '/dev/cu.usbserial-11120'
BAUD_RATE = 9600
SERIAL_TIMEOUT = 2

try:
    API_BASE_URL = config('API_BASE_URL', default='http://127.0.0.1:8000')
    API_USERNAME = config('API_USERNAME')
    API_PASSWORD = config('API_PASSWORD')
except UndefinedValueError:
    print("ERROR: Create .env file with API_USERNAME and API_PASSWORD")
    sys.exit(1)

API_LOGIN_URL = f'{API_BASE_URL}/api/auth/login/'
API_SENSOR_DATA_URL = f'{API_BASE_URL}/api/sensors/'

MAX_RETRIES = 3
RETRY_DELAY = 5

access_token = None
token_expires_at = None

# ==================== ФУНКЦІЇ ====================

def log(message, level='INFO'):
    """Логування з часовою міткою"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [{level}] {message}")


def login_to_api():
    """Логін в API та отримання JWT токена"""
    global access_token, token_expires_at
    
    try:
        log("Logging in to API...")
        response = requests.post(
            API_LOGIN_URL,
            json={'email': API_USERNAME, 'password': API_PASSWORD},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get('access')
            token_expires_at = time.time() + 3600
            log("Login successful! Token expires in 1 hour")
            return access_token
        else:
            log(f"Login failed: {response.status_code}", 'ERROR')
            return None
    except Exception as e:
        log(f"Login error: {e}", 'ERROR')
        return None


def refresh_token_if_needed():
    """Перевірка та оновлення токена"""
    global access_token, token_expires_at
    
    if not access_token or not token_expires_at:
        return login_to_api()
    
    if time.time() > (token_expires_at - 300):
        log("Token expiring soon, refreshing...")
        return login_to_api()
    
    return access_token

def send_sensor_data(plant_id, temperature, air_humidity, light_level):
    """Відправити дані на API"""
    token = refresh_token_if_needed()
    
    if not token:
        log("Cannot send: not authenticated", 'ERROR')
        return False
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'user_plant': plant_id,
        'temperature': temperature,
        'air_humidity': air_humidity,
        'soil_humidity': None,
        'light_level': light_level
    }
    
    try:
        log(f"Sending: Plant {plant_id}, T={temperature}°C, H={air_humidity}%, L={light_level} lux")
        
        response = requests.post(
            API_SENSOR_DATA_URL,
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 201:
            log("Data sent successfully! ", 'SUCCESS')
            return True
        elif response.status_code == 403:
            log("Permission denied: Premium required", 'ERROR')
            return False
        else:
            log(f"Failed: {response.status_code}", 'ERROR')
            return False
    except Exception as e:
        log(f"Network error: {e}", 'ERROR')
        return False
    
def parse_sensor_data(line):
    """
    Парсинг: DATA,<plant_id>,<temp>,<humidity>,<light>
    """
    try:
        parts = line.strip().split(',')
        
        if len(parts) != 5 or parts[0] != 'DATA':
            return None
        
        plant_id = int(parts[1])
        temperature = float(parts[2])
        humidity = float(parts[3])
        light_level = int(parts[4])
        
        return (plant_id, temperature, humidity, light_level)
    except Exception as e:
        log(f"Parse error: {e}", 'WARNING')
        return None


def find_arduino_port():
    """Автопошук Arduino порту"""
    import serial.tools.list_ports
    
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if any(k in port.description.lower() for k in ['arduino', 'usb', 'serial']):
            return port.device
    return None

def connect_to_arduino(port):
    """Підключення до Arduino"""
    try:
        log(f"Connecting to Arduino on {port}...")
        
        # ВАЖЛИВО: dtr=False щоб не перезавантажувати Arduino!
        ser = serial.Serial(
            port, 
            BAUD_RATE, 
            timeout=SERIAL_TIMEOUT,
            dsrdtr=False,  # Відключити DTR
            rtscts=False   # Відключити RTS
        )
        
        # Більша затримка для стабілізації
        time.sleep(3)
        
        # Очистити буфер
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        log("Connected to Arduino! ✓", 'SUCCESS')
        return ser
    except Exception as e:
        log(f"Failed to connect: {e}", 'ERROR')
        return None
    
def safe_readline(arduino, timeout=2):
    """Безпечне читання з обробкою помилок"""
    try:
        line_bytes = arduino.readline()
        
        if not line_bytes:
            return None
        
        # UTF-8
        try:
            return line_bytes.decode('utf-8').strip()
        except UnicodeDecodeError:
            # ASCII з ігноруванням помилок
            try:
                line = line_bytes.decode('ascii', errors='ignore').strip()
                if line:
                    return line
            except:
                pass
            
            log(f"Failed to decode, skipping", 'WARNING')
            return None
    except Exception as e:
        log(f"Read error: {e}", 'ERROR')
        return None
    
def main():
    """Головна функція"""
    global SERIAL_PORT
    
    log("====================================")
    log("Plant Care System - Arduino Bridge")
    log("====================================")
    
    # Логін
    if not login_to_api():
        log("Cannot start: login failed", 'ERROR')
        sys.exit(1)
    
    # Автопошук порту
    if sys.platform != 'win32':
        auto_port = find_arduino_port()
        if auto_port:
            log(f"Auto-detected Arduino on {auto_port}")
            SERIAL_PORT = auto_port
    
    # Підключення
    arduino = connect_to_arduino(SERIAL_PORT)
    
    if not arduino:
        log("Cannot start: Arduino connection failed", 'ERROR')
        sys.exit(1)
    
    log("Starting data collection...")
    log("Press Ctrl+C to stop")
    log("====================================")
    retry_count = 0
    consecutive_errors = 0
    MAX_CONSECUTIVE_ERRORS = 5
    
    try:
        while True:
            try:
                if arduino.in_waiting > 0:
                    line = safe_readline(arduino)
                    
                    if line:
                        # Показуємо ВСІ повідомлення Arduino
                        print(f"[ARDUINO] {line}")
                        
                        consecutive_errors = 0
                        
                        # Парсимо DATA
                        data = parse_sensor_data(line)
                        
                        if data:
                            plant_id, temp, hum, light = data
                            
                            success = send_sensor_data(plant_id, temp, hum, light)
                            
                            if success:
                                retry_count = 0
                            else:
                                retry_count += 1
                                if retry_count >= MAX_RETRIES:
                                    log(f"Too many failures, waiting...", 'WARNING')
                                    time.sleep(RETRY_DELAY)
                                    retry_count = 0
                
                time.sleep(0.1)
            except KeyboardInterrupt:
                raise
            
            except serial.SerialException as e:
                log(f"Serial error: {e}", 'ERROR')
                consecutive_errors += 1
                
                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    log("Too many errors, reconnecting...", 'ERROR')
                    arduino.close()
                    time.sleep(2)
                    arduino = connect_to_arduino(SERIAL_PORT)
                    if not arduino:
                        log("Failed to reconnect", 'ERROR')
                        sys.exit(1)
                    consecutive_errors = 0
                
                time.sleep(1)
            
            except Exception as e:
                log(f"Error: {e}", 'ERROR')
                consecutive_errors += 1
                time.sleep(1)
    
    except KeyboardInterrupt:
        log("\nStopping Arduino Bridge...")
        arduino.close()
        log("Connection closed. Goodbye!")
        sys.exit(0)
# ==================== ЗАПУСК ====================

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
    except Exception as e:
        log(f"Fatal error: {e}", 'ERROR')
        sys.exit(1)