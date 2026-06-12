/*
 * Plant Care System - Arduino Sensor Module
 * 
 * Датчики:
 * - DHT11: температура та вологість повітря
 * - Фоторезистор 5528: освітленість
 * 
 * Підключення:
 * - DHT11 DATA pin -> Arduino Digital Pin 2
 * - DHT11 VCC -> 5V
 * - DHT11 GND -> GND
 * 
 * - Фоторезистор -> Arduino Analog Pin A0
 * - Резистор 10kΩ (підтягуючий)
 * 
 * Комунікація: Serial (9600 baud)
 * Відправка даних кожні 60 секунд
 */

#include <DHT.h>
#include <EEPROM.h>

// ==================== КОНФІГУРАЦІЯ ====================

// Піни
#define DHTPIN 2              // DHT11 підключений до Digital Pin 2
#define DHTTYPE DHT11         // Тип датчика DHT11
#define PHOTORESISTOR_PIN A0  // Фоторезистор підключений до Analog Pin A0

// Таймінги
#define SEND_INTERVAL 60000   // Інтервал відправки даних (60 секунд)
#define SENSOR_READ_DELAY 2000 // Затримка між читаннями DHT11

// EEPROM адреси
#define EEPROM_PLANT_ID_ADDR 0   // Адреса збереження plant_id (int = 2 байти)
#define EEPROM_INIT_FLAG_ADDR 10 // Адреса прапорця ініціалізації

// ==================== ГЛОБАЛЬНІ ЗМІННІ ====================

DHT dht(DHTPIN, DHTTYPE);

int plantId = -1;              // ID рослини (-1 = не призначено)
unsigned long lastSendTime = 0; // Час останньої відправки даних
bool isInitialized = false;    // Чи ініціалізовано систему

// ==================== ФУНКЦІЇ ====================

/**
 * Зчитати plant_id з EEPROM
 */
void loadPlantIdFromEEPROM() {
  byte initFlag = EEPROM.read(EEPROM_INIT_FLAG_ADDR);
  
  if (initFlag == 0xAA) {  // 0xAA = прапорець ініціалізації
    // Читаємо plant_id (2 байти, int)
    byte lowByte = EEPROM.read(EEPROM_PLANT_ID_ADDR);
    byte highByte = EEPROM.read(EEPROM_PLANT_ID_ADDR + 1);
    plantId = (highByte << 8) | lowByte;
    
    isInitialized = true;
    Serial.print(F("Loaded plant_id from EEPROM: "));
    Serial.println(plantId);
  } else {
    Serial.println(F("No plant_id stored in EEPROM"));
  }
}

/**
 * Зберегти plant_id в EEPROM
 */
void savePlantIdToEEPROM(int id) {
  byte lowByte = id & 0xFF;
  byte highByte = (id >> 8) & 0xFF;
  
  EEPROM.write(EEPROM_PLANT_ID_ADDR, lowByte);
  EEPROM.write(EEPROM_PLANT_ID_ADDR + 1, highByte);
  EEPROM.write(EEPROM_INIT_FLAG_ADDR, 0xAA);  // Встановлюємо прапорець
  
  plantId = id;
  isInitialized = true;
  
  Serial.print(F("Saved plant_id to EEPROM: "));
  Serial.println(plantId);
}

/**
 * Зчитати дані з DHT11
 */
bool readDHT11(float &temperature, float &humidity) {
  humidity = dht.readHumidity();
  temperature = dht.readTemperature();
  
  // Перевірка чи зчитування успішне
  if (isnan(humidity) || isnan(temperature)) {
    Serial.println(F("ERROR: Failed to read from DHT11 sensor!"));
    return false;
  }
  
  return true;
}

/**
 * Зчитати освітленість з фоторезистора
 * Конвертує аналогове значення (0-1023) в люкси
 */
int readLightLevel() {
  int analogValue = analogRead(PHOTORESISTOR_PIN);
  
  // Конвертація analog value -> lux (приблизна формула)
  // Для фоторезистора 5528:
  // - 0 (темрява) -> ~0 lux
  // - 1023 (яскраве світло) -> ~10000+ lux
  // Формула калібрована для приміщення
  
  int lux = map(analogValue, 0, 1023, 0, 10000);
  
  // Додаткова корекція для більш реалістичних значень
  if (analogValue < 100) {
    lux = map(analogValue, 0, 100, 0, 100);  // Темрява: 0-100 lux
  } else if (analogValue < 500) {
    lux = map(analogValue, 100, 500, 100, 1000);  // Кімната: 100-1000 lux
  } else {
    lux = map(analogValue, 500, 1023, 1000, 10000);  // Яскраво: 1000-10000 lux
  }
  
  return lux;
}

/**
 * Відправити дані на комп'ютер через Serial
 * Формат: DATA,<plant_id>,<temperature>,<humidity>,<light_level>
 */
void sendSensorData(float temperature, float humidity, int lightLevel) {
  Serial.print(F("DATA,"));
  Serial.print(plantId);
  Serial.print(F(","));
  Serial.print(temperature, 1);  // 1 знак після коми
  Serial.print(F(","));
  Serial.print(humidity, 2);     // 2 знаки після коми
  Serial.print(F(","));
  Serial.println(lightLevel);
  
  // Додаткове логування (для відладки)
  Serial.print(F("DEBUG: Temperature="));
  Serial.print(temperature);
  Serial.print(F("°C, Humidity="));
  Serial.print(humidity);
  Serial.print(F("%, Light="));
  Serial.print(lightLevel);
  Serial.println(F(" lux"));
}

/**
 * Обробка команд з Serial Monitor
 * Формат команди: SET_PLANT_ID:<id>
 */
void processSerialCommands() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command.startsWith("SET_PLANT_ID:")) {
      String idStr = command.substring(13);  // Витягуємо ID після "SET_PLANT_ID:"
      int newPlantId = idStr.toInt();
      
      if (newPlantId > 0) {
        savePlantIdToEEPROM(newPlantId);
        Serial.print(F("SUCCESS: Plant ID set to "));
        Serial.println(newPlantId);
      } else {
        Serial.println(F("ERROR: Invalid plant_id. Must be > 0"));
      }
    }
    else if (command == "GET_PLANT_ID") {
      Serial.print(F("Current plant_id: "));
      Serial.println(plantId);
    }
    else if (command == "RESET") {
      EEPROM.write(EEPROM_INIT_FLAG_ADDR, 0x00);
      plantId = -1;
      isInitialized = false;
      Serial.println(F("RESET: Plant ID cleared from EEPROM"));
    }
    else if (command == "TEST") {
      // Тестова команда для перевірки датчиків
      float temp, hum;
      if (readDHT11(temp, hum)) {
        int light = readLightLevel();
        Serial.println(F("TEST: Sensor readings:"));
        Serial.print(F("  Temperature: "));
        Serial.print(temp);
        Serial.println(F("°C"));
        Serial.print(F("  Humidity: "));
        Serial.print(hum);
        Serial.println(F("%"));
        Serial.print(F("  Light: "));
        Serial.print(light);
        Serial.println(F(" lux"));
      }
    }
    else {
      Serial.println(F("ERROR: Unknown command"));
      Serial.println(F("Available commands:"));
      Serial.println(F("  SET_PLANT_ID:<id> - Set plant ID"));
      Serial.println(F("  GET_PLANT_ID - Show current plant ID"));
      Serial.println(F("  RESET - Clear plant ID"));
      Serial.println(F("  TEST - Test sensors"));
    }
  }
}

// ==================== SETUP ====================

void setup() {
  Serial.begin(9600);
  
  // Чекаємо на підключення Serial (для відладки)
  while (!Serial) {
    ; // Чекаємо
  }
  
  Serial.println(F("========================================"));
  Serial.println(F("Plant Care System - Arduino Sensor"));
  Serial.println(F("========================================"));
  
  // Ініціалізація DHT11
  dht.begin();
  Serial.println(F("DHT11 sensor initialized"));
  
  // Ініціалізація фоторезистора (pinMode для аналогового піна не потрібен)
  Serial.println(F("Photoresistor initialized on A0"));
  
  // Завантажуємо plant_id з EEPROM
  loadPlantIdFromEEPROM();
  
  if (!isInitialized) {
    Serial.println(F(""));
    Serial.println(F("SETUP REQUIRED:"));
    Serial.println(F("1. Call API endpoint: POST /api/sensors/assign/"));
    Serial.println(F("2. Send command: SET_PLANT_ID:<your_plant_id>"));
    Serial.println(F(""));
  } else {
    Serial.println(F("Arduino is ready to send data"));
  }
  
  Serial.println(F("========================================"));
  
  delay(2000);  // Чекаємо 2 секунди для стабілізації DHT11
}

// ==================== LOOP ====================

void loop() {
  // Обробка команд з Serial Monitor
  processSerialCommands();
  
  // Відправка даних тільки якщо plant_id призначено
  if (isInitialized && plantId > 0) {
    unsigned long currentTime = millis();
    
    // Перевіряємо чи минув час для відправки
    if (currentTime - lastSendTime >= SEND_INTERVAL) {
      lastSendTime = currentTime;
      
      // Зчитуємо дані з датчиків
      float temperature, humidity;
      if (readDHT11(temperature, humidity)) {
        int lightLevel = readLightLevel();
        
        // Відправляємо дані через Serial
        sendSensorData(temperature, humidity, lightLevel);
      } else {
        Serial.println(F("ERROR: Skipping data send due to sensor error"));
      }
    }
  }
  
  delay(100);  // Невелика затримка для стабільності
}
