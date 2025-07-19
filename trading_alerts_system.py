#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Умная система алертов для трейдера
Автор: AI Assistant
Описание: Система для автоматического поиска торговых сетапов и отправки уведомлений
"""

import ccxt
import pandas as pd
import numpy as np
import requests
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
import ta

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_alerts.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TradingSetup:
    """Класс для описания торгового сетапа"""
    symbol: str
    setup_type: str
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    confidence: float
    timestamp: datetime
    description: str

class BinanceDataProvider:
    """Провайдер данных с Binance"""
    
    def __init__(self):
        self.exchange = ccxt.binance({
            'apiKey': '',  # Добавить API ключ
            'secret': '',  # Добавить секретный ключ
            'sandbox': False,
            'rateLimit': 1200,
        })
        
    def get_top_volume_symbols(self, limit: int = 50) -> List[str]:
        """Получить топ монет по объему торгов"""
        try:
            tickers = self.exchange.fetch_tickers()
            # Фильтруем только USDT пары
            usdt_pairs = {k: v for k, v in tickers.items() if k.endswith('/USDT')}
            # Сортируем по объему
            sorted_pairs = sorted(usdt_pairs.items(), 
                                key=lambda x: x[1]['quoteVolume'] or 0, 
                                reverse=True)
            return [pair[0] for pair in sorted_pairs[:limit]]
        except Exception as e:
            logger.error(f"Ошибка получения символов: {e}")
            return []
    
    def get_ohlcv_data(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> pd.DataFrame:
        """Получить OHLCV данные для символа"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            logger.error(f"Ошибка получения данных для {symbol}: {e}")
            return pd.DataFrame()

class TechnicalAnalyzer:
    """Класс для технического анализа"""
    
    @staticmethod
    def calculate_sma(data: pd.Series, period: int) -> pd.Series:
        """Простая скользящая средняя"""
        return ta.trend.sma_indicator(data, window=period)
    
    @staticmethod
    def calculate_ema(data: pd.Series, period: int) -> pd.Series:
        """Экспоненциальная скользящая средняя"""
        return ta.trend.ema_indicator(data, window=period)
    
    @staticmethod
    def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """Индекс относительной силы"""
        return ta.momentum.rsi(data, window=period)
    
    @staticmethod
    def find_support_resistance(df: pd.DataFrame, window: int = 20) -> Tuple[List[float], List[float]]:
        """Поиск уровней поддержки и сопротивления"""
        highs = df['high'].rolling(window=window, center=True).max()
        lows = df['low'].rolling(window=window, center=True).min()
        
        resistance_levels = []
        support_levels = []
        
        for i in range(window, len(df) - window):
            if df['high'].iloc[i] == highs.iloc[i]:
                resistance_levels.append(df['high'].iloc[i])
            if df['low'].iloc[i] == lows.iloc[i]:
                support_levels.append(df['low'].iloc[i])
        
        return support_levels, resistance_levels

class SetupDetector:
    """Детектор торговых сетапов"""
    
    def __init__(self, analyzer: TechnicalAnalyzer):
        self.analyzer = analyzer
    
    def detect_breakout_setup(self, df: pd.DataFrame, symbol: str) -> Optional[TradingSetup]:
        """Детектор пробоя уровня"""
        if len(df) < 50:
            return None
            
        # Получаем уровни поддержки и сопротивления
        support_levels, resistance_levels = self.analyzer.find_support_resistance(df)
        
        if not resistance_levels:
            return None
        
        current_price = df['close'].iloc[-1]
        recent_high = df['high'].iloc[-5:].max()
        volume_avg = df['volume'].iloc[-20:].mean()
        current_volume = df['volume'].iloc[-1]
        
        # Ищем ближайший уровень сопротивления
        nearest_resistance = min(resistance_levels, 
                               key=lambda x: abs(x - current_price) if x > current_price else float('inf'))
        
        # Условия для пробоя:
        # 1. Цена близко к сопротивлению (в пределах 2%)
        # 2. Объем выше среднего
        # 3. Восходящий тренд
        if (abs(current_price - nearest_resistance) / current_price < 0.02 and
            current_volume > volume_avg * 1.5 and
            current_price > df['close'].iloc[-10:].mean()):
            
            entry_price = nearest_resistance * 1.005  # Вход на 0.5% выше сопротивления
            stop_loss = current_price * 0.98  # Стоп на 2% ниже
            take_profit = entry_price + (entry_price - stop_loss) * 3  # R:R 1:3
            
            return TradingSetup(
                symbol=symbol,
                setup_type="Breakout",
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_reward=3.0,
                confidence=0.7,
                timestamp=datetime.now(),
                description=f"Пробой сопротивления на уровне {nearest_resistance:.4f}"
            )
        
        return None
    
    def detect_higher_lows_setup(self, df: pd.DataFrame, symbol: str) -> Optional[TradingSetup]:
        """Детектор паттерна Higher Lows"""
        if len(df) < 30:
            return None
        
        # Ищем последние 3 локальных минимума
        lows = []
        for i in range(5, len(df) - 5):
            if (df['low'].iloc[i] < df['low'].iloc[i-5:i].min() and 
                df['low'].iloc[i] < df['low'].iloc[i+1:i+6].min()):
                lows.append((i, df['low'].iloc[i]))
        
        if len(lows) < 3:
            return None
        
        # Берем последние 3 минимума
        recent_lows = lows[-3:]
        
        # Проверяем, что каждый следующий минимум выше предыдущего
        if (recent_lows[1][1] > recent_lows[0][1] and 
            recent_lows[2][1] > recent_lows[1][1]):
            
            current_price = df['close'].iloc[-1]
            resistance_levels, _ = self.analyzer.find_support_resistance(df)
            
            if resistance_levels:
                nearest_resistance = min(resistance_levels, 
                                       key=lambda x: abs(x - current_price) if x > current_price else float('inf'))
                
                # Проверяем, что мы под сопротивлением
                if current_price < nearest_resistance * 0.98:
                    entry_price = nearest_resistance * 1.002
                    stop_loss = recent_lows[-1][1] * 0.995
                    take_profit = entry_price + (entry_price - stop_loss) * 3
                    
                    return TradingSetup(
                        symbol=symbol,
                        setup_type="Higher Lows",
                        entry_price=entry_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        risk_reward=3.0,
                        confidence=0.8,
                        timestamp=datetime.now(),
                        description=f"Higher Lows под сопротивлением {nearest_resistance:.4f}"
                    )
        
        return None

class NotificationManager:
    """Менеджер уведомлений"""
    
    def __init__(self, telegram_token: str = None, chat_id: str = None):
        self.telegram_token = telegram_token
        self.chat_id = chat_id
    
    def send_telegram_alert(self, setup: TradingSetup) -> bool:
        """Отправка уведомления в Telegram"""
        if not self.telegram_token or not self.chat_id:
            logger.warning("Telegram токен или chat_id не настроены")
            return False
        
        message = f"""
🚨 ТОРГОВЫЙ СИГНАЛ 🚨

💰 Монета: {setup.symbol}
📈 Тип: {setup.setup_type}
💵 Вход: {setup.entry_price:.4f}
🛑 Стоп: {setup.stop_loss:.4f}
🎯 Цель: {setup.take_profit:.4f}
📊 R:R: 1:{setup.risk_reward:.1f}
⭐ Уверенность: {setup.confidence*100:.0f}%
📝 Описание: {setup.description}
⏰ Время: {setup.timestamp.strftime('%H:%M:%S')}
        """
        
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        data = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        try:
            response = requests.post(url, data=data)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ошибка отправки в Telegram: {e}")
            return False
    
    def save_to_file(self, setup: TradingSetup, filename: str = "alerts.json"):
        """Сохранение алерта в файл"""
        alert_data = {
            'symbol': setup.symbol,
            'setup_type': setup.setup_type,
            'entry_price': setup.entry_price,
            'stop_loss': setup.stop_loss,
            'take_profit': setup.take_profit,
            'risk_reward': setup.risk_reward,
            'confidence': setup.confidence,
            'timestamp': setup.timestamp.isoformat(),
            'description': setup.description
        }
        
        try:
            # Читаем существующие данные
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    alerts = json.load(f)
            except FileNotFoundError:
                alerts = []
            
            # Добавляем новый алерт
            alerts.append(alert_data)
            
            # Сохраняем обратно
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(alerts, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Алерт сохранен в {filename}")
        except Exception as e:
            logger.error(f"Ошибка сохранения в файл: {e}")

class TradingAlertSystem:
    """Основная система алертов"""
    
    def __init__(self, telegram_token: str = None, chat_id: str = None):
        self.data_provider = BinanceDataProvider()
        self.analyzer = TechnicalAnalyzer()
        self.detector = SetupDetector(self.analyzer)
        self.notification_manager = NotificationManager(telegram_token, chat_id)
        self.processed_setups = set()  # Для избежания дублирования
    
    def scan_markets(self, symbols: List[str] = None) -> List[TradingSetup]:
        """Сканирование рынков на предмет торговых возможностей"""
        if symbols is None:
            symbols = self.data_provider.get_top_volume_symbols(30)
        
        found_setups = []
        
        for symbol in symbols:
            try:
                logger.info(f"Анализируем {symbol}...")
                
                # Получаем данные
                df = self.data_provider.get_ohlcv_data(symbol, '1h', 100)
                if df.empty:
                    continue
                
                # Фильтр по ликвидности (минимальный объем)
                avg_volume = df['volume'].mean()
                if avg_volume < 1000000:  # Минимум $1M среднего объема
                    continue
                
                # Ищем сетапы
                breakout_setup = self.detector.detect_breakout_setup(df, symbol)
                if breakout_setup:
                    setup_id = f"{symbol}_{breakout_setup.setup_type}_{breakout_setup.timestamp.date()}"
                    if setup_id not in self.processed_setups:
                        found_setups.append(breakout_setup)
                        self.processed_setups.add(setup_id)
                
                higher_lows_setup = self.detector.detect_higher_lows_setup(df, symbol)
                if higher_lows_setup:
                    setup_id = f"{symbol}_{higher_lows_setup.setup_type}_{higher_lows_setup.timestamp.date()}"
                    if setup_id not in self.processed_setups:
                        found_setups.append(higher_lows_setup)
                        self.processed_setups.add(setup_id)
                
                time.sleep(0.1)  # Небольшая задержка для API
                
            except Exception as e:
                logger.error(f"Ошибка анализа {symbol}: {e}")
                continue
        
        return found_setups
    
    def run_continuous_scan(self, interval_minutes: int = 60):
        """Непрерывное сканирование рынков"""
        logger.info("Запуск непрерывного сканирования...")
        
        while True:
            try:
                logger.info("Начинаем новый цикл сканирования")
                setups = self.scan_markets()
                
                for setup in setups:
                    logger.info(f"Найден сетап: {setup.symbol} - {setup.setup_type}")
                    
                    # Отправляем уведомления
                    self.notification_manager.send_telegram_alert(setup)
                    self.notification_manager.save_to_file(setup)
                
                if not setups:
                    logger.info("Сетапы не найдены")
                
                logger.info(f"Ожидание {interval_minutes} минут до следующего сканирования...")
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                logger.info("Остановка системы пользователем")
                break
            except Exception as e:
                logger.error(f"Ошибка в основном цикле: {e}")
                time.sleep(60)  # Ждем минуту перед повтором

if __name__ == "__main__":
    # Настройки (заполнить реальными значениями)
    TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # Получить у @BotFather
    CHAT_ID = "YOUR_CHAT_ID"  # Ваш Telegram ID
    
    # Создаем и запускаем систему
    alert_system = TradingAlertSystem(TELEGRAM_TOKEN, CHAT_ID)
    
    # Для тестирования - одноразовое сканирование
    print("Запуск тестового сканирования...")
    test_setups = alert_system.scan_markets(['BTC/USDT', 'ETH/USDT', 'BNB/USDT'])
    
    for setup in test_setups:
        print(f"\nНайден сетап:")
        print(f"Символ: {setup.symbol}")
        print(f"Тип: {setup.setup_type}")
        print(f"Вход: {setup.entry_price}")
        print(f"Стоп: {setup.stop_loss}")
        print(f"Цель: {setup.take_profit}")
        print(f"Описание: {setup.description}")
    
    # Для запуска непрерывного мониторинга раскомментировать:
    # alert_system.run_continuous_scan(interval_minutes=30)