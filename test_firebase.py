#!/usr/bin/env python3
"""
Тестовый скрипт для проверки Firebase интеграции
"""

import os
from firebase_manager import FirebaseManager
from config import Config

def test_firebase_connection():
    """Тестирует подключение к Firebase"""
    print("🔥 Тестирование Firebase интеграции...")
    
    # Проверяем наличие ключа
    key_path = Config.FIREBASE_SERVICE_ACCOUNT_KEY
    if not os.path.exists(key_path):
        print(f"❌ Файл ключа не найден: {key_path}")
        return False
    
    print(f"✅ Файл ключа найден: {key_path}")
    
    try:
        # Инициализируем Firebase Manager
        firebase_manager = FirebaseManager()
        
        # Проверяем подключение
        if firebase_manager.is_connected():
            print("✅ Подключение к Firebase успешно!")
            
            # Тестируем сохранение алерта
            test_alert = {
                'symbol': 'BTCUSDT',
                'type': 'BUY',
                'price': 45000.0,
                'timestamp': '2024-12-24 20:00:00',
                'indicators': {
                    'rsi': 35.5,
                    'macd': 'bullish',
                    'volume': 'high'
                }
            }
            
            alert_id = firebase_manager.save_alert(test_alert)
            if alert_id:
                print(f"✅ Тестовый алерт сохранен с ID: {alert_id}")
                
                # Получаем алерты
                alerts = firebase_manager.get_alerts(limit=1)
                if alerts:
                    print(f"✅ Получен алерт: {alerts[0]['symbol']} - {alerts[0]['type']}")
                    return True
            
        else:
            print("❌ Не удалось подключиться к Firebase")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании Firebase: {e}")
        return False

if __name__ == "__main__":
    success = test_firebase_connection()
    if success:
        print("\n🎉 Firebase интеграция работает корректно!")
    else:
        print("\n💥 Проблемы с Firebase интеграцией. Проверьте настройки.")