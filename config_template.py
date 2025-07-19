#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Шаблон конфигурационного файла для системы торговых алертов
Скопируйте этот файл в config.py и заполните своими данными
"""

import os
from typing import List

class Config:
    """Основные настройки системы"""
    
    # === BINANCE API ===
    BINANCE_API_KEY = 'YOUR_BINANCE_API_KEY_HERE'  # Ваш API ключ Binance
    BINANCE_SECRET_KEY = 'YOUR_BINANCE_SECRET_KEY_HERE'  # Ваш секретный ключ
    BINANCE_TESTNET = False  # True для тестовой сети
    
    # === TELEGRAM ===
    TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN_HERE'  # Токен бота от @BotFather
    TELEGRAM_CHAT_ID = 'YOUR_TELEGRAM_CHAT_ID_HERE'  # Ваш Chat ID - получите его через @userinfobot
    
    # === ТОРГОВЫЕ НАСТРОЙКИ ===
    ACCOUNT_BALANCE = 220  # Размер депозита в USD
    RISK_PERCENTAGE = 5  # Риск на сделку в % от депозита (5-10%)
    MAX_LEVERAGE = 20  # Максимальное плечо
    MIN_LEVERAGE = 10  # Минимальное плечо
    STOP_LOSS_PERCENTAGE = 2  # Максимальный стоп-лосс в %
    MIN_RISK_REWARD = 3  # Минимальное соотношение риск/прибыль
    
    # === ФИЛЬТРЫ РЫНКА ===
    MIN_VOLUME_USD = 1000000  # Минимальный объем торгов в USD
    MIN_PRICE_CHANGE_24H = -50  # Минимальное изменение цены за 24ч в %
    MAX_PRICE_CHANGE_24H = 100  # Максимальное изменение цены за 24ч в %
    
    # === ВРЕМЕННЫЕ РАМКИ ===
    MAIN_TIMEFRAME = '1h'  # Основной таймфрейм для анализа
    CONFIRMATION_TIMEFRAME = '15m'  # Таймфрейм для подтверждения
    SCAN_INTERVAL_MINUTES = 30  # Интервал сканирования в минутах
    
    # === WATCHLIST ===
    PRIORITY_SYMBOLS = [
        'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT',
        'XRP/USDT', 'DOT/USDT', 'AVAX/USDT', 'MATIC/USDT', 'LINK/USDT',
        'UNI/USDT', 'LTC/USDT', 'BCH/USDT', 'ALGO/USDT', 'VET/USDT'
    ]
    
    # === ТЕХНИЧЕСКИЕ ИНДИКАТОРЫ ===
    RSI_PERIOD = 14
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    
    SMA_FAST = 20
    SMA_SLOW = 50
    EMA_PERIOD = 21
    
    VOLUME_SMA_PERIOD = 20
    VOLUME_MULTIPLIER = 0.1  # Объем должен быть в X раз больше среднего
    
    # === ПАТТЕРНЫ ===
    BREAKOUT_CONFIRMATION_PERCENTAGE = 0.5  # % выше уровня для подтверждения пробоя
    SUPPORT_RESISTANCE_WINDOW = 20  # Окно для поиска уровней
    HIGHER_LOWS_MIN_COUNT = 3  # Минимальное количество Higher Lows
    
    # === УВЕДОМЛЕНИЯ ===
    ENABLE_TELEGRAM = True
    ENABLE_FILE_LOGGING = True
    ENABLE_CONSOLE_OUTPUT = True
    
    # === ФАЙЛЫ ===
    ALERTS_FILE = 'alerts.json'
    LOG_FILE = 'trading_alerts.log'
    PERFORMANCE_FILE = 'performance.json'
    
    # === ДОПОЛНИТЕЛЬНЫЕ ФИЛЬТРЫ ===
    ENABLE_BTC_DOMINANCE_FILTER = True  # Учитывать доминацию BTC
    BTC_DOMINANCE_THRESHOLD = 45  # Минимальная доминация BTC для алертов
    
    ENABLE_MARKET_CAP_FILTER = True  # Фильтр по рыночной капитализации
    MIN_MARKET_CAP_RANK = 100  # Максимальный ранг по капитализации
    
    # === РАСШИРЕННЫЕ НАСТРОЙКИ ===
    MAX_ALERTS_PER_HOUR = 5  # Максимум алертов в час
    COOLDOWN_MINUTES = 60  # Время ожидания между алертами для одной монеты
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """Проверка корректности конфигурации"""
        errors = []
        
        if not cls.BINANCE_API_KEY or cls.BINANCE_API_KEY == 'YOUR_BINANCE_API_KEY_HERE':
            errors.append("BINANCE_API_KEY не установлен")
        
        if not cls.BINANCE_SECRET_KEY or cls.BINANCE_SECRET_KEY == 'YOUR_BINANCE_SECRET_KEY_HERE':
            errors.append("BINANCE_SECRET_KEY не установлен")
        
        if cls.ENABLE_TELEGRAM:
            if not cls.TELEGRAM_BOT_TOKEN or cls.TELEGRAM_BOT_TOKEN == 'YOUR_TELEGRAM_BOT_TOKEN_HERE':
                errors.append("TELEGRAM_BOT_TOKEN не установлен")
            if not cls.TELEGRAM_CHAT_ID or cls.TELEGRAM_CHAT_ID == 'YOUR_TELEGRAM_CHAT_ID_HERE':
                errors.append("TELEGRAM_CHAT_ID не установлен")
        
        if cls.RISK_PERCENTAGE < 1 or cls.RISK_PERCENTAGE > 20:
            errors.append("RISK_PERCENTAGE должен быть между 1 и 20")
        
        if cls.MIN_RISK_REWARD < 1:
            errors.append("MIN_RISK_REWARD должен быть больше 1")
        
        return errors
    
    @classmethod
    def get_position_size(cls, entry_price: float, stop_loss: float) -> float:
        """Расчет размера позиции на основе риска"""
        risk_amount = cls.ACCOUNT_BALANCE * (cls.RISK_PERCENTAGE / 100)
        price_diff = abs(entry_price - stop_loss)
        position_size = risk_amount / price_diff
        return position_size
    
    @classmethod
    def get_leverage_for_position(cls, position_size: float, entry_price: float) -> int:
        """Расчет необходимого плеча"""
        position_value = position_size * entry_price
        required_leverage = position_value / cls.ACCOUNT_BALANCE
        
        # Ограничиваем плечо заданными рамками
        leverage = max(cls.MIN_LEVERAGE, min(cls.MAX_LEVERAGE, int(required_leverage)))
        return leverage

class MarketConditions:
    """Настройки для различных рыночных условий"""
    
    # Бычий рынок
    BULL_MARKET = {
        'min_volume_multiplier': 1.2,
        'rsi_threshold': 40,
        'trend_confirmation_periods': 3,
        'breakout_strength': 0.3
    }
    
    # Медвежий рынок
    BEAR_MARKET = {
        'min_volume_multiplier': 2.0,
        'rsi_threshold': 60,
        'trend_confirmation_periods': 5,
        'breakout_strength': 0.8
    }
    
    # Боковой рынок
    SIDEWAYS_MARKET = {
        'min_volume_multiplier': 1.8,
        'rsi_threshold': 50,
        'trend_confirmation_periods': 4,
        'breakout_strength': 0.6
    }

class AlertMessages:
    """Шаблоны сообщений для алертов"""
    
    BREAKOUT_TEMPLATE = """
🚀 ПРОБОЙ УРОВНЯ 🚀

💰 Монета: {symbol}
📈 Цена: ${current_price:.4f}
🎯 Уровень: ${resistance_level:.4f}
📊 Объем: {volume_increase:.1f}x от среднего

💵 Вход: ${entry_price:.4f}
🛑 Стоп: ${stop_loss:.4f} (-{stop_percentage:.1f}%)
🎯 Цель: ${take_profit:.4f} (+{profit_percentage:.1f}%)
📊 R:R: 1:{risk_reward:.1f}

⚡ Плечо: {leverage}x
💰 Размер: ${position_size:.0f}
⭐ Уверенность: {confidence:.0f}%

⏰ {timestamp}
    """
    
    HIGHER_LOWS_TEMPLATE = """
📈 HIGHER LOWS 📈

💰 Монета: {symbol}
📈 Цена: ${current_price:.4f}
🔄 Паттерн: {lows_count} восходящих минимума
🎯 Сопротивление: ${resistance_level:.4f}

💵 Вход: ${entry_price:.4f}
🛑 Стоп: ${stop_loss:.4f} (-{stop_percentage:.1f}%)
🎯 Цель: ${take_profit:.4f} (+{profit_percentage:.1f}%)
📊 R:R: 1:{risk_reward:.1f}

⚡ Плечо: {leverage}x
💰 Размер: ${position_size:.0f}
⭐ Уверенность: {confidence:.0f}%

⏰ {timestamp}
    """
    
    IMPULSE_PULLBACK_TEMPLATE = """
⚡ ИМПУЛЬС → ОТКАТ ⚡

💰 Монета: {symbol}
📈 Цена: ${current_price:.4f}
📊 Импульс: +{impulse_percentage:.1f}% за {impulse_period}ч
🔄 Откат: -{pullback_percentage:.1f}%

💵 Вход: ${entry_price:.4f}
🛑 Стоп: ${stop_loss:.4f} (-{stop_percentage:.1f}%)
🎯 Цель: ${take_profit:.4f} (+{profit_percentage:.1f}%)
📊 R:R: 1:{risk_reward:.1f}

⚡ Плечо: {leverage}x
💰 Размер: ${position_size:.0f}
⭐ Уверенность: {confidence:.0f}%

⏰ {timestamp}
    """