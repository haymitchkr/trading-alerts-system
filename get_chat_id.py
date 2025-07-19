#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для получения вашего Telegram Chat ID
"""

import requests
import json
from config import Config

def get_chat_id():
    """
    Получает Chat ID из последних сообщений бота
    
    Инструкция:
    1. Напишите любое сообщение вашему боту в Telegram
    2. Запустите этот скрипт
    3. Скопируйте полученный Chat ID в config.py
    """
    
    bot_token = Config.TELEGRAM_BOT_TOKEN
    
    if not bot_token:
        print("❌ Ошибка: TELEGRAM_BOT_TOKEN не установлен в config.py")
        return
    
    # Получаем обновления от бота
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if not data.get('ok'):
            print(f"❌ Ошибка API Telegram: {data.get('description', 'Неизвестная ошибка')}")
            return
        
        updates = data.get('result', [])
        
        if not updates:
            print("📱 Сначала напишите любое сообщение вашему боту в Telegram")
            print("   Затем запустите этот скрипт снова")
            return
        
        # Получаем последнее сообщение
        last_update = updates[-1]
        
        if 'message' in last_update:
            chat_id = last_update['message']['chat']['id']
            username = last_update['message']['chat'].get('username', 'Не указан')
            first_name = last_update['message']['chat'].get('first_name', 'Не указано')
            
            print("✅ Chat ID найден!")
            print(f"📋 Ваш Chat ID: {chat_id}")
            print(f"👤 Имя: {first_name}")
            print(f"🔗 Username: @{username}" if username != 'Не указан' else "🔗 Username: Не указан")
            print("\n📝 Скопируйте этот Chat ID в config.py:")
            print(f"   TELEGRAM_CHAT_ID = '{chat_id}'")
            
            return str(chat_id)
        else:
            print("❌ Не удалось найти сообщения в обновлениях")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети: {e}")
    except json.JSONDecodeError:
        print("❌ Ошибка декодирования ответа от Telegram API")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")

if __name__ == "__main__":
    print("🤖 Получение Telegram Chat ID")
    print("=" * 40)
    print("\n📋 Инструкция:")
    print("1. Найдите вашего бота в Telegram")
    print("2. Напишите ему любое сообщение (например: 'Привет')")
    print("3. Дождитесь выполнения этого скрипта")
    print("\n🔄 Получаем Chat ID...\n")
    
    chat_id = get_chat_id()
    
    if chat_id:
        print("\n✅ Готово! Теперь обновите config.py с полученным Chat ID")
    else:
        print("\n❌ Не удалось получить Chat ID")
        print("\n🔧 Альтернативные способы:")
        print("1. Используйте бота @userinfobot - отправьте ему /start")
        print("2. Используйте бота @chatid_echo_bot")
        print("3. Проверьте правильность токена бота")