#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Расширенная система торговых алертов
Включает дополнительные сетапы и фильтры
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
from dataclasses import dataclass, asdict
import ta
from config import Config, MarketConditions, AlertMessages
from firebase_manager import firebase_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MarketData:
    """Структура рыночных данных"""
    symbol: str
    price: float
    volume_24h: float
    price_change_24h: float
    market_cap_rank: int
    btc_dominance: float

@dataclass
class EnhancedTradingSetup:
    """Расширенная структура торгового сетапа"""
    symbol: str
    setup_type: str
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    confidence: float
    timestamp: datetime
    description: str
    leverage: int
    position_size: float
    risk_amount: float
    market_condition: str
    volume_confirmation: bool
    trend_confirmation: bool
    additional_data: Dict

class EnhancedBinanceProvider:
    """Расширенный провайдер данных Binance"""
    
    def __init__(self):
        self.demo_mode = Config.is_demo_mode()
        if not self.demo_mode:
            self.exchange = ccxt.binance({
                'apiKey': Config.BINANCE_API_KEY,
                'secret': Config.BINANCE_SECRET_KEY,
                'sandbox': Config.BINANCE_TESTNET,
                'rateLimit': 1200,
            })
        else:
            self.exchange = None
            logger.warning("EnhancedBinanceProvider работает в ДЕМО-РЕЖИМЕ.")

        self.btc_dominance = 50.0
        self.last_dominance_update = None
        self.update_btc_dominance()

    def _generate_fake_market_data(self, symbols: List[str]) -> List[MarketData]:
        """Генерация фейковых рыночных данных для демо-режима."""
        fake_data = []
        for symbol in symbols:
            fake_data.append(MarketData(
                symbol=symbol,
                price=np.random.uniform(20000, 70000) if 'BTC' in symbol else np.random.uniform(10, 500),
                volume_24h=np.random.uniform(10000000, 500000000),
                price_change_24h=np.random.uniform(-10, 10),
                market_cap_rank=np.random.randint(1, 100),
                btc_dominance=self.btc_dominance
            ))
        return fake_data

    def _generate_fake_ohlcv(self, symbol: str, limit: int) -> pd.DataFrame:
        """Генерация фейковых OHLCV данных для демо-режима."""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=limit)
        dates = pd.to_datetime(pd.date_range(start=start_time, end=end_time, periods=limit))

        base_price = np.random.uniform(20000, 70000) if 'BTC' in symbol else np.random.uniform(10, 500)
        prices = base_price * (1 + np.random.randn(limit).cumsum() * 0.005)

        data = {
            'timestamp': dates,
            'open': prices - np.random.uniform(0, 5, size=limit),
            'high': prices + np.random.uniform(0, 5, size=limit),
            'low': prices - np.random.uniform(5, 10, size=limit),
            'close': prices,
            'volume': np.random.uniform(100, 10000, size=limit)
        }
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df
    
    def update_btc_dominance(self) -> bool:
        """Обновить доминацию BTC через CoinGecko API"""
        if self.demo_mode:
            self.btc_dominance = np.random.uniform(48, 55)
            return True

        try:
            if (self.last_dominance_update and 
                datetime.now() - self.last_dominance_update < timedelta(minutes=10)):
                return True
            
            url = "https://api.coingecko.com/api/v3/global"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                dominance = data['data']['market_cap_percentage']['btc']
                self.btc_dominance = round(dominance, 1)
                self.last_dominance_update = datetime.now()
                logger.info(f"Доминация BTC обновлена: {self.btc_dominance}%")
                return True
            else:
                logger.warning(f"Не удалось получить доминацию BTC: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка обновления доминации BTC: {e}")
            return False
    
    def get_market_overview(self) -> Dict:
        """Получить общий обзор рынка"""
        try:
            # Обновляем доминацию BTC
            self.update_btc_dominance()
            
            # Получаем данные по BTC для определения тренда
            btc_data = self.get_ohlcv_data('BTC/USDT', '1d', 30)
            if not btc_data.empty:
                # Более точное определение тренда
                recent_closes = btc_data['close'].iloc[-7:]
                trend_slope = np.polyfit(range(len(recent_closes)), recent_closes, 1)[0]
                
                # Логируем данные для отладки
                current_price = recent_closes.iloc[-1]
                week_ago_price = recent_closes.iloc[0]
                price_change_7d = ((current_price - week_ago_price) / week_ago_price) * 100
                
                logger.info(f"BTC анализ: цена 7 дней назад: ${week_ago_price:.0f}, текущая: ${current_price:.0f}")
                logger.info(f"BTC изменение за 7 дней: {price_change_7d:.1f}%, наклон тренда: {trend_slope:.2f}")
                
                if trend_slope > 0:
                    btc_trend = 'bullish'
                elif trend_slope < 0:
                    btc_trend = 'bearish'
                else:
                    btc_trend = 'neutral'
                    
                logger.info(f"Определенный тренд BTC: {btc_trend}")
            else:
                btc_trend = 'neutral'
                logger.warning("Не удалось получить данные BTC для анализа тренда")
            
            return {
                'btc_dominance': self.btc_dominance,
                'market_trend': btc_trend,
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"Ошибка получения обзора рынка: {e}")
            return {'btc_dominance': self.btc_dominance, 'market_trend': 'neutral', 'timestamp': datetime.now()}
    
    def get_filtered_symbols(self, limit: int = 50) -> List[MarketData]:
        """Получить отфильтрованные символы с дополнительными данными"""
        if self.demo_mode:
            return self._generate_fake_market_data(Config.PRIORITY_SYMBOLS)[:limit]

        try:
            tickers = self.exchange.fetch_tickers()
            usdt_pairs = {k: v for k, v in tickers.items() if k.endswith('/USDT')}
            
            market_data = []
            for symbol, ticker in usdt_pairs.items():
                if not all(k in ticker and ticker[k] is not None for k in ['quoteVolume', 'percentage', 'last']):
                    continue

                data = MarketData(
                    symbol=symbol, price=ticker['last'], volume_24h=ticker['quoteVolume'],
                    price_change_24h=ticker['percentage'], market_cap_rank=0,
                    btc_dominance=self.btc_dominance
                )
                market_data.append(data)
            
            filtered_data = [
                data for data in market_data
                if (data.volume_24h >= Config.MIN_VOLUME_USD and
                    Config.MIN_PRICE_CHANGE_24H <= data.price_change_24h <= Config.MAX_PRICE_CHANGE_24H)
            ]
            
            filtered_data.sort(key=lambda x: x.volume_24h, reverse=True)
            return filtered_data[:limit]
            
        except Exception as e:
            logger.error(f"Ошибка получения отфильтрованных символов: {e}")
            return []
    
    def get_ohlcv_data(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> pd.DataFrame:
        """Получить OHLCV данные с дополнительными индикаторами"""
        if self.demo_mode:
            df = self._generate_fake_ohlcv(symbol, limit)
            return self._add_technical_indicators(df)

        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            if not ohlcv:
                return pd.DataFrame()
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return self._add_technical_indicators(df)
            
        except Exception as e:
            logger.error(f"Ошибка получения данных для {symbol}: {e}")
            return pd.DataFrame()
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Добавить технические индикаторы"""
        if len(df) < 50:
            return df
        
        # Скользящие средние
        df['sma_20'] = ta.trend.sma_indicator(df['close'], window=Config.SMA_FAST)
        df['sma_50'] = ta.trend.sma_indicator(df['close'], window=Config.SMA_SLOW)
        df['ema_21'] = ta.trend.ema_indicator(df['close'], window=Config.EMA_PERIOD)
        
        # RSI
        df['rsi'] = ta.momentum.rsi(df['close'], window=Config.RSI_PERIOD)
        
        # Объем
        df['volume_sma'] = df['volume'].rolling(window=Config.VOLUME_SMA_PERIOD).mean()
        # Заменяем возможные NaN и inf значения, которые могут возникнуть при делении на 0
        df['volume_ratio'] = (df['volume'] / df['volume_sma']).replace([np.inf, -np.inf], np.nan).fillna(1.0)
        
        # Волатильность
        df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)
        
        # Удаляем строки с любыми оставшимися NaN значениями после расчетов
        df.dropna(inplace=True)

        return df
    


class AdvancedSetupDetector:
    """Расширенный детектор торговых сетапов"""
    
    def __init__(self, market_overview: Dict):
        self.market_overview = market_overview
        self.alert_history = {}  # Для отслеживания кулдауна
    
    def detect_all_setups(self, df: pd.DataFrame, market_data: MarketData) -> List[EnhancedTradingSetup]:
        """Поиск всех типов сетапов"""
        setups = []
        
        if len(df) < 50:
            return setups
        
        # Проверяем кулдаун
        if self._is_in_cooldown(market_data.symbol):
            return setups
        
        # Базовые фильтры
        if not self._passes_basic_filters(df, market_data):
            return setups
        
        # Определяем рыночные условия
        market_condition = self._determine_market_condition(df)
        
        # Ищем различные сетапы
        breakout = self._detect_enhanced_breakout(df, market_data, market_condition)
        if breakout:
            setups.append(breakout)
        
        higher_lows = self._detect_enhanced_higher_lows(df, market_data, market_condition)
        if higher_lows:
            setups.append(higher_lows)
        
        impulse_pullback = self._detect_impulse_pullback(df, market_data, market_condition)
        if impulse_pullback:
            setups.append(impulse_pullback)
        
        squeeze_breakout = self._detect_squeeze_breakout(df, market_data, market_condition)
        if squeeze_breakout:
            setups.append(squeeze_breakout)
        
        return setups
    
    def _is_in_cooldown(self, symbol: str) -> bool:
        """Проверка кулдауна для символа"""
        if symbol in self.alert_history:
            last_alert = self.alert_history[symbol]
            cooldown_end = last_alert + timedelta(minutes=Config.COOLDOWN_MINUTES)
            return datetime.now() < cooldown_end
        return False
    
    def _passes_basic_filters(self, df: pd.DataFrame, market_data: MarketData) -> bool:
        """Базовые фильтры для проверки перед детальным анализом."""
        symbol = market_data.symbol

        # Проверяем, что DataFrame не пустой после обработки
        if df.empty:
            logger.warning(f"{symbol}: DataFrame пуст после добавления индикаторов. Пропуск.")
            return False

        # Фильтр по доминации BTC
        if Config.ENABLE_BTC_DOMINANCE_FILTER:
            if market_data.btc_dominance < Config.BTC_DOMINANCE_THRESHOLD:
                logger.info(f"{symbol}: Отклонен по доминации BTC ({market_data.btc_dominance:.1f}% < {Config.BTC_DOMINANCE_THRESHOLD}%)")
                return False
        
        # Фильтр по объему. Убедимся, что колонка существует.
        if 'volume_ratio' in df.columns:
            current_volume_ratio = df['volume_ratio'].iloc[-1]
            # ЛОГИЧЕСКАЯ ОШИБКА: VOLUME_MULTIPLIER в конфиге (0.1) скорее всего должен быть > 1.0.
            # Например, 1.5, чтобы объем был в 1.5 раза выше среднего.
            # Оставляем как есть, но это потенциальная проблема в стратегии.
            if current_volume_ratio < Config.VOLUME_MULTIPLIER:
                logger.info(f"{symbol}: Отклонен по объему (коэф. {current_volume_ratio:.2f} < {Config.VOLUME_MULTIPLIER})")
                return False
            logger.info(f"{symbol}: Объем коэф. {current_volume_ratio:.2f} - прошел фильтр")
        
        # Фильтр по тренду. Убедимся, что колонки существуют.
        if 'close' in df.columns and 'ema_21' in df.columns:
            current_price = df['close'].iloc[-1]
            ema_21 = df['ema_21'].iloc[-1]
            if current_price < ema_21 * 0.995: # Допуск 0.5% ниже EMA
                logger.info(f"{symbol}: Отклонен по тренду (цена ${current_price:.4f} < EMA21*0.995 ${ema_21*0.995:.4f})")
                return False
            logger.info(f"{symbol}: Тренд - цена ${current_price:.4f}, EMA21 ${ema_21:.4f} - прошел фильтр")
        
        logger.info(f"{symbol}: Прошел базовые фильтры")
        return True
    
    def _determine_market_condition(self, df: pd.DataFrame) -> str:
        """Определение рыночных условий"""
        if len(df) < 20:
            return 'neutral'
        
        # Анализ тренда
        recent_closes = df['close'].iloc[-10:]
        trend_slope = np.polyfit(range(len(recent_closes)), recent_closes, 1)[0]
        
        # Анализ волатильности
        volatility = df['close'].pct_change().std() * 100
        
        if trend_slope > 0 and volatility < 5:
            return 'bullish'
        elif trend_slope < 0 and volatility < 5:
            return 'bearish'
        else:
            return 'sideways'
    
    def _detect_enhanced_breakout(self, df: pd.DataFrame, market_data: MarketData, market_condition: str) -> Optional[EnhancedTradingSetup]:
        """Улучшенный детектор пробоя"""
        required_cols = ['close', 'volume_ratio', 'rsi', 'sma_20', 'ema_21']
        if not all(col in df.columns for col in required_cols):
            return None

        resistance_levels = self._find_resistance_levels(df)
        if not resistance_levels:
            return None
        
        current_price = df['close'].iloc[-1]
        current_volume_ratio = df['volume_ratio'].iloc[-1]
        current_rsi = df['rsi'].iloc[-1]
        
        nearest_resistance = min((r for r in resistance_levels if r > current_price * 0.995), key=lambda x: abs(x - current_price), default=None)
        if not nearest_resistance:
            return None
        
        distance_to_resistance = abs(current_price - nearest_resistance) / current_price
        
        if not (distance_to_resistance < 0.02 and current_volume_ratio > Config.VOLUME_MULTIPLIER * 0.8 and 30 < current_rsi < 80 and current_price > df['sma_20'].iloc[-1]):
            return None
        
        entry_price = nearest_resistance * (1 + Config.BREAKOUT_CONFIRMATION_PERCENTAGE / 100)
        stop_loss = current_price * (1 - Config.STOP_LOSS_PERCENTAGE / 100)
        if entry_price <= stop_loss: return None

        risk_reward = Config.MIN_RISK_REWARD
        take_profit = entry_price + (entry_price - stop_loss) * risk_reward
        
        position_size = Config.get_position_size(entry_price, stop_loss)
        leverage = Config.get_leverage_for_position(position_size, entry_price)
        risk_amount = Config.ACCOUNT_BALANCE * (Config.RISK_PERCENTAGE / 100)
        
        confidence = 0.6 + (0.1 if current_volume_ratio > 2.0 else 0) + (0.1 if market_condition == 'bullish' else 0) + (0.1 if distance_to_resistance < 0.01 else 0)
        self.alert_history[market_data.symbol] = datetime.now()
        
        return EnhancedTradingSetup(
            symbol=market_data.symbol, setup_type="Enhanced Breakout", entry_price=entry_price,
            stop_loss=stop_loss, take_profit=take_profit, risk_reward=risk_reward,
            confidence=min(confidence, 0.95), timestamp=datetime.now(),
            description=f"Пробой сопротивления {nearest_resistance:.4f} с подтверждением объема",
            leverage=leverage, position_size=position_size, risk_amount=risk_amount,
            market_condition=market_condition, volume_confirmation=current_volume_ratio > Config.VOLUME_MULTIPLIER,
            trend_confirmation=current_price > df['ema_21'].iloc[-1],
            additional_data={'resistance_level': nearest_resistance, 'volume_ratio': current_volume_ratio, 'rsi': current_rsi, 'distance_to_resistance': distance_to_resistance}
        )
    
    def _detect_enhanced_higher_lows(self, df: pd.DataFrame, market_data: MarketData, market_condition: str) -> Optional[EnhancedTradingSetup]:
        """Улучшенный детектор Higher Lows"""
        if len(df) < 50 or not all(col in df.columns for col in ['low', 'close', 'rsi']):
            return None
        
        lows = [(i, df['low'].iloc[i]) for i in range(10, len(df) - 10) if df['low'].iloc[i] <= df['low'].iloc[i-10:i].min() and df['low'].iloc[i] <= df['low'].iloc[i+1:i+11].min()]
        if len(lows) < Config.HIGHER_LOWS_MIN_COUNT:
            return None
        
        recent_lows = lows[-Config.HIGHER_LOWS_MIN_COUNT:]
        if not all(recent_lows[i][1] > recent_lows[i-1][1] for i in range(1, len(recent_lows))):
            return None
        
        current_price = df['close'].iloc[-1]
        resistance_levels = self._find_resistance_levels(df)
        if not resistance_levels: return None
        
        nearest_resistance = min((r for r in resistance_levels if r > current_price), key=lambda x: abs(x - current_price), default=None)
        if not nearest_resistance or current_price >= nearest_resistance * 0.98:
            return None
        
        entry_price = nearest_resistance * 1.002
        stop_loss = recent_lows[-1][1] * 0.995
        if entry_price <= stop_loss: return None

        risk_percentage = abs(entry_price - stop_loss) / entry_price * 100
        if risk_percentage > Config.STOP_LOSS_PERCENTAGE:
            return None
        
        risk_reward = Config.MIN_RISK_REWARD
        take_profit = entry_price + (entry_price - stop_loss) * risk_reward
        position_size = Config.get_position_size(entry_price, stop_loss)
        leverage = Config.get_leverage_for_position(position_size, entry_price)
        risk_amount = Config.ACCOUNT_BALANCE * (Config.RISK_PERCENTAGE / 100)
        confidence = 0.75 + (0.1 if market_condition == 'bullish' else 0) + (0.05 if len(recent_lows) > 3 else 0)
        self.alert_history[market_data.symbol] = datetime.now()
        
        return EnhancedTradingSetup(
            symbol=market_data.symbol, setup_type="Enhanced Higher Lows", entry_price=entry_price,
            stop_loss=stop_loss, take_profit=take_profit, risk_reward=risk_reward,
            confidence=min(confidence, 0.95), timestamp=datetime.now(),
            description=f"Higher Lows паттерн с {len(recent_lows)} восходящими минимумами",
            leverage=leverage, position_size=position_size, risk_amount=risk_amount,
            market_condition=market_condition, volume_confirmation=True, trend_confirmation=True,
            additional_data={'lows_count': len(recent_lows), 'resistance_level': nearest_resistance, 'last_low': recent_lows[-1][1], 'rsi': df['rsi'].iloc[-1]}
        )
    
    def _detect_impulse_pullback(self, df: pd.DataFrame, market_data: MarketData, market_condition: str) -> Optional[EnhancedTradingSetup]:
        """Детектор импульс → откат → повторный вход"""
        if len(df) < 30 or not all(col in df.columns for col in ['close', 'high', 'volume']):
            return None
        
        impulse_period = 8
        if len(df) < impulse_period + 1: return None

        current_price = df['close'].iloc[-1]
        impulse_start_price = df['close'].iloc[-impulse_period]
        if impulse_start_price == 0: return None
        
        impulse_percentage = (current_price - impulse_start_price) / impulse_start_price * 100
        if impulse_percentage < 5: return None
        
        recent_high = df['high'].iloc[-impulse_period:].max()
        if recent_high == 0: return None
        
        pullback_percentage = (recent_high - current_price) / recent_high * 100
        if not (20 <= pullback_percentage <= 50): return None
        
        if len(df) < 30 + impulse_period: return None
        impulse_volume = df['volume'].iloc[-impulse_period:].mean()
        avg_volume = df['volume'].iloc[-30:-impulse_period].mean()
        if avg_volume == 0 or impulse_volume < avg_volume * 1.5: return None
        
        entry_price = current_price * 1.01
        stop_loss = current_price * (1 - Config.STOP_LOSS_PERCENTAGE / 100)
        if entry_price <= stop_loss: return None

        risk_reward = Config.MIN_RISK_REWARD
        take_profit = entry_price + (entry_price - stop_loss) * risk_reward
        position_size = Config.get_position_size(entry_price, stop_loss)
        leverage = Config.get_leverage_for_position(position_size, entry_price)
        risk_amount = Config.ACCOUNT_BALANCE * (Config.RISK_PERCENTAGE / 100)
        confidence = 0.7 + (0.1 if impulse_percentage > 10 else 0) + (0.1 if market_condition == 'bullish' else 0)
        self.alert_history[market_data.symbol] = datetime.now()
        
        return EnhancedTradingSetup(
            symbol=market_data.symbol, setup_type="Impulse Pullback", entry_price=entry_price,
            stop_loss=stop_loss, take_profit=take_profit, risk_reward=risk_reward,
            confidence=min(confidence, 0.95), timestamp=datetime.now(),
            description=f"Импульс +{impulse_percentage:.1f}% → откат -{pullback_percentage:.1f}%",
            leverage=leverage, position_size=position_size, risk_amount=risk_amount,
            market_condition=market_condition, volume_confirmation=True, trend_confirmation=True,
            additional_data={'impulse_percentage': impulse_percentage, 'pullback_percentage': pullback_percentage, 'impulse_period': impulse_period, 'recent_high': recent_high}
        )
    
    def _detect_squeeze_breakout(self, df: pd.DataFrame, market_data: MarketData, market_condition: str) -> Optional[EnhancedTradingSetup]:
        """Детектор пробоя после сжатия (поджатие к уровню)"""
        if len(df) < 40 or not all(col in df.columns for col in ['atr', 'close', 'high', 'low']):
            return None
        
        current_price = df['close'].iloc[-1]
        if current_price == 0: return None

        current_atr = df['atr'].iloc[-1]
        avg_atr = df['atr'].iloc[-20:].mean()
        if avg_atr == 0 or current_atr > avg_atr * 0.7: return None
        
        resistance_levels = self._find_resistance_levels(df)
        support_levels = self._find_support_levels(df)
        all_levels = resistance_levels + support_levels
        if not all_levels: return None
        
        nearest_level = min(all_levels, key=lambda x: abs(x - current_price))
        distance_to_level = abs(current_price - nearest_level) / current_price
        if distance_to_level > 0.015: return None
        
        recent_range = df['high'].iloc[-10:].max() - df['low'].iloc[-10:].min()
        price_range_percentage = recent_range / current_price * 100
        if price_range_percentage > 5: return None
        
        if nearest_level <= current_price: return None # Только лонг от сопротивления

        entry_price = nearest_level * 1.005
        stop_loss = current_price * (1 - Config.STOP_LOSS_PERCENTAGE / 100)
        if entry_price <= stop_loss: return None
        
        risk_reward = Config.MIN_RISK_REWARD
        take_profit = entry_price + (entry_price - stop_loss) * risk_reward
        position_size = Config.get_position_size(entry_price, stop_loss)
        leverage = Config.get_leverage_for_position(position_size, entry_price)
        risk_amount = Config.ACCOUNT_BALANCE * (Config.RISK_PERCENTAGE / 100)
        confidence = 0.8 + (0.1 if price_range_percentage < 3 else 0)
        self.alert_history[market_data.symbol] = datetime.now()
        
        return EnhancedTradingSetup(
            symbol=market_data.symbol, setup_type="Squeeze Breakout", entry_price=entry_price,
            stop_loss=stop_loss, take_profit=take_profit, risk_reward=risk_reward,
            confidence=min(confidence, 0.95), timestamp=datetime.now(),
            description=f"Поджатие к уровню {nearest_level:.4f}, диапазон {price_range_percentage:.1f}%",
            leverage=leverage, position_size=position_size, risk_amount=risk_amount,
            market_condition=market_condition, volume_confirmation=True, trend_confirmation=True,
            additional_data={'squeeze_level': nearest_level, 'range_percentage': price_range_percentage, 'atr_ratio': current_atr / avg_atr, 'distance_to_level': distance_to_level}
        )
    
    def _find_resistance_levels(self, df: pd.DataFrame, window: int = 20) -> List[float]:
        """Поиск уровней сопротивления"""
        highs = df['high'].rolling(window=window, center=True).max()
        resistance_levels = []
        
        for i in range(window, len(df) - window):
            if df['high'].iloc[i] == highs.iloc[i]:
                resistance_levels.append(df['high'].iloc[i])
        
        # Убираем дубликаты и близкие уровни
        unique_levels = []
        for level in sorted(resistance_levels):
            if not unique_levels or abs(level - unique_levels[-1]) / level > 0.01:
                unique_levels.append(level)
        
        return unique_levels
    
    def _find_support_levels(self, df: pd.DataFrame, window: int = 20) -> List[float]:
        """Поиск уровней поддержки"""
        lows = df['low'].rolling(window=window, center=True).min()
        support_levels = []
        
        for i in range(window, len(df) - window):
            if df['low'].iloc[i] == lows.iloc[i]:
                support_levels.append(df['low'].iloc[i])
        
        # Убираем дубликаты и близкие уровни
        unique_levels = []
        for level in sorted(support_levels):
            if not unique_levels or abs(level - unique_levels[-1]) / level > 0.01:
                unique_levels.append(level)
        
        return unique_levels

class EnhancedNotificationManager:
    """Расширенный менеджер уведомлений"""
    
    def __init__(self):
        self.telegram_token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.alerts_sent_today = 0
        self.last_reset_date = datetime.now().date()
    
    def send_enhanced_alert(self, setup: EnhancedTradingSetup) -> bool:
        """Отправка расширенного уведомления"""
        # Проверяем лимит алертов
        if not self._check_alert_limit():
            logger.warning("Достигнут лимит алертов на сегодня")
            return False
        
        success = False
        
        if Config.ENABLE_TELEGRAM and self.telegram_token and self.chat_id:
            success = self._send_telegram_alert(setup)
        
        if Config.ENABLE_FILE_LOGGING:
            self._save_to_file(setup)
        
        if Config.ENABLE_CONSOLE_OUTPUT:
            self._print_alert(setup)
            
        # Сохранение в Firebase
        if firebase_manager.is_connected():
            try:
                # Конвертируем dataclass в словарь для сохранения
                alert_data = asdict(setup)
                # Datetime нужно конвертировать в строку, так как Firestore не принимает его напрямую
                alert_data['timestamp'] = setup.timestamp.isoformat()
                
                # Конвертируем numpy типы в стандартные Python типы
                def convert_numpy_types(obj):
                    if isinstance(obj, dict):
                        return {k: convert_numpy_types(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [convert_numpy_types(v) for v in obj]
                    elif hasattr(obj, 'item'):  # numpy types
                        return obj.item()
                    elif isinstance(obj, (np.bool_, bool)):
                        return bool(obj)
                    elif isinstance(obj, (np.integer, int)):
                        return int(obj)
                    elif isinstance(obj, (np.floating, float)):
                        return float(obj)
                    else:
                        return obj
                
                alert_data = convert_numpy_types(alert_data)
                firebase_manager.save_alert(alert_data)
                logger.info(f"Алерт для {setup.symbol} успешно сохранен в Firebase.")
            except Exception as e:
                logger.error(f"Ошибка сохранения алерта в Firebase: {e}")
        
        if success:
            self.alerts_sent_today += 1
        
        return success
    
    def _check_alert_limit(self) -> bool:
        """Проверка лимита алертов"""
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.alerts_sent_today = 0
            self.last_reset_date = today
        
        return self.alerts_sent_today < Config.MAX_ALERTS_PER_HOUR
    
    def _send_telegram_alert(self, setup: EnhancedTradingSetup) -> bool:
        """Отправка в Telegram с форматированием"""
        try:
            # Выбираем шаблон сообщения
            if setup.setup_type == "Enhanced Breakout":
                template = AlertMessages.BREAKOUT_TEMPLATE
            elif setup.setup_type == "Enhanced Higher Lows":
                template = AlertMessages.HIGHER_LOWS_TEMPLATE
            elif setup.setup_type == "Impulse Pullback":
                template = AlertMessages.IMPULSE_PULLBACK_TEMPLATE
            else:
                template = AlertMessages.BREAKOUT_TEMPLATE  # По умолчанию
            
            # Подготавливаем данные для форматирования
            format_data = {
                'symbol': setup.symbol,
                'current_price': setup.entry_price * 0.995,  # Примерная текущая цена
                'entry_price': setup.entry_price,
                'stop_loss': setup.stop_loss,
                'take_profit': setup.take_profit,
                'risk_reward': setup.risk_reward,
                'leverage': setup.leverage,
                'position_size': setup.position_size,
                'confidence': setup.confidence * 100,
                'timestamp': setup.timestamp.strftime('%H:%M:%S %d.%m.%Y'),
                'stop_percentage': abs(setup.entry_price - setup.stop_loss) / setup.entry_price * 100,
                'profit_percentage': abs(setup.take_profit - setup.entry_price) / setup.entry_price * 100
            }
            
            # Добавляем специфичные данные
            if 'resistance_level' in setup.additional_data:
                format_data['resistance_level'] = setup.additional_data['resistance_level']
            if 'volume_ratio' in setup.additional_data:
                format_data['volume_increase'] = setup.additional_data['volume_ratio']
            if 'lows_count' in setup.additional_data:
                format_data['lows_count'] = setup.additional_data['lows_count']
            if 'impulse_percentage' in setup.additional_data:
                format_data['impulse_percentage'] = setup.additional_data['impulse_percentage']
                format_data['pullback_percentage'] = setup.additional_data['pullback_percentage']
                format_data['impulse_period'] = setup.additional_data['impulse_period']
            
            message = template.format(**format_data)
            
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Ошибка отправки в Telegram: {e}")
            return False
    
    def _save_to_file(self, setup: EnhancedTradingSetup):
        """Сохранение в файл"""
        try:
            # Читаем существующие данные
            try:
                with open(Config.ALERTS_FILE, 'r', encoding='utf-8') as f:
                    alerts = json.load(f)
            except FileNotFoundError:
                alerts = []
            
            # Конвертируем setup в словарь
            alert_data = asdict(setup)
            alert_data['timestamp'] = setup.timestamp.isoformat()
            
            alerts.append(alert_data)
            
            # Сохраняем
            with open(Config.ALERTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(alerts, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Ошибка сохранения в файл: {e}")
    
    def _print_alert(self, setup: EnhancedTradingSetup):
        """Вывод в консоль"""
        print(f"\n{'='*60}")
        print(f"🚨 ТОРГОВЫЙ СИГНАЛ: {setup.setup_type}")
        print(f"{'='*60}")
        print(f"💰 Символ: {setup.symbol}")
        print(f"💵 Вход: ${setup.entry_price:.4f}")
        print(f"🛑 Стоп: ${setup.stop_loss:.4f} (-{abs(setup.entry_price - setup.stop_loss) / setup.entry_price * 100:.1f}%)")
        print(f"🎯 Цель: ${setup.take_profit:.4f} (+{abs(setup.take_profit - setup.entry_price) / setup.entry_price * 100:.1f}%)")
        print(f"📊 R:R: 1:{setup.risk_reward:.1f}")
        print(f"⚡ Плечо: {setup.leverage}x")
        print(f"💰 Размер: ${setup.position_size:.0f}")
        print(f"⭐ Уверенность: {setup.confidence*100:.0f}%")
        print(f"🌍 Рынок: {setup.market_condition}")
        print(f"📝 Описание: {setup.description}")
        print(f"⏰ Время: {setup.timestamp.strftime('%H:%M:%S %d.%m.%Y')}")
        print(f"{'='*60}\n")

class AdvancedTradingAlertSystem:
    """Расширенная система торговых алертов"""
    
    def __init__(self):
        if Config.is_demo_mode():
            logger.warning("Система работает в ДЕМО-РЕЖИМЕ. Для реальной работы настройте API ключи в .env файле.")
        else:
            config_errors = Config.validate_config()
            if config_errors:
                logger.error("Обнаружены ошибки конфигурации:")
                for error in config_errors:
                    logger.error(f"  - {error}")
            else:
                logger.info("Конфигурация в порядке. Система работает в реальном режиме.")
        
        self.data_provider = EnhancedBinanceProvider()
        self.notification_manager = EnhancedNotificationManager()
        self.processed_setups = set()
        
        # Обновляем доминацию BTC при инициализации
        try:
            self.data_provider.update_btc_dominance()
            logger.info(f"Доминация BTC обновлена: {self.data_provider.btc_dominance:.1f}%")
        except Exception as e:
            logger.warning(f"Не удалось обновить доминацию BTC: {e}")
        
        logger.info("Расширенная система торговых алертов инициализирована")
    
    def run_single_scan(self, symbols: List[str] = None) -> List[EnhancedTradingSetup]:
        """Одноразовое сканирование"""
        logger.info("Запуск сканирования рынков...")
        
        market_overview = self.data_provider.get_market_overview()
        logger.info(f"Обзор рынка: {market_overview.get('market_trend', 'N/A')}, BTC доминация: {market_overview.get('btc_dominance', 0.0):.1f}%")
        
        if self.data_provider.demo_mode:
            # В демо-режиме используем либо переданные символы, либо приоритетные
            scan_symbols = symbols if symbols is not None else Config.PRIORITY_SYMBOLS
            market_symbols = self.data_provider.get_filtered_symbols(len(scan_symbols))
            # Убедимся, что get_filtered_symbols в демо-режиме вернет данные для нужных символов
            market_symbols = [s for s in market_symbols if s.symbol in scan_symbols]
        else:
            # В реальном режиме, если символы переданы, получаем их данные, иначе - фильтруем топ-50
            if symbols:
                market_symbols = []
                for symbol in symbols:
                    try:
                        ticker = self.data_provider.exchange.fetch_ticker(symbol)
                        if all(k in ticker and ticker[k] is not None for k in ['last', 'quoteVolume', 'percentage']):
                             market_symbols.append(MarketData(
                                symbol=symbol, price=ticker['last'], volume_24h=ticker['quoteVolume'],
                                price_change_24h=ticker['percentage'], market_cap_rank=0,
                                btc_dominance=market_overview.get('btc_dominance', 50.0)
                            ))
                    except Exception as e:
                        logger.error(f"Ошибка получения тикера для {symbol}: {e}")
            else:
                market_symbols = self.data_provider.get_filtered_symbols(50)
        
        if not market_symbols:
            logger.warning("Не найдено символов для анализа")
            return []
        
        logger.info(f"Анализируем {len(market_symbols)} символов...")
        
        # Создаем детектор
        detector = AdvancedSetupDetector(market_overview)
        
        all_setups = []
        
        for market_data in market_symbols:
            try:
                logger.info(f"Анализ {market_data.symbol}...")
                
                # Получаем данные
                df = self.data_provider.get_ohlcv_data(market_data.symbol, Config.MAIN_TIMEFRAME, 100)
                if df.empty:
                    continue
                
                # Ищем сетапы
                setups = detector.detect_all_setups(df, market_data)
                
                for setup in setups:
                    setup_id = f"{setup.symbol}_{setup.setup_type}_{setup.timestamp.date()}"
                    if setup_id not in self.processed_setups:
                        all_setups.append(setup)
                        self.processed_setups.add(setup_id)
                        logger.info(f"Найден сетап: {setup.symbol} - {setup.setup_type} (уверенность: {setup.confidence*100:.0f}%)")
                
                time.sleep(0.1)  # Задержка для API
                
            except Exception as e:
                logger.error(f"Ошибка анализа {market_data.symbol}: {e}")
                continue
        
        # Сортируем по уверенности
        all_setups.sort(key=lambda x: x.confidence, reverse=True)
        
        logger.info(f"Найдено {len(all_setups)} торговых возможностей")
        return all_setups
    
    def run_continuous_monitoring(self):
        """Непрерывный мониторинг"""
        logger.info(f"Запуск непрерывного мониторинга (интервал: {Config.SCAN_INTERVAL_MINUTES} мин)")
        
        while True:
            try:
                setups = self.run_single_scan()
                
                # Отправляем уведомления
                for setup in setups:
                    self.notification_manager.send_enhanced_alert(setup)
                
                if not setups:
                    logger.info("Торговые возможности не найдены")
                
                logger.info(f"Ожидание {Config.SCAN_INTERVAL_MINUTES} минут до следующего сканирования...")
                time.sleep(Config.SCAN_INTERVAL_MINUTES * 60)
                
            except KeyboardInterrupt:
                logger.info("Остановка системы пользователем")
                break
            except Exception as e:
                logger.error(f"Ошибка в основном цикле: {e}")
                time.sleep(60)

if __name__ == "__main__":
    # Создаем систему
    system = AdvancedTradingAlertSystem()
    
    # Тестовое сканирование
    print("\n🔍 Запуск тестового сканирования...")
    test_symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT']
    setups = system.run_single_scan(test_symbols)
    
    if setups:
        print(f"\n✅ Найдено {len(setups)} торговых возможностей:")
        for i, setup in enumerate(setups, 1):
            print(f"\n{i}. {setup.symbol} - {setup.setup_type}")
            print(f"   Вход: ${setup.entry_price:.4f} | Стоп: ${setup.stop_loss:.4f} | Цель: ${setup.take_profit:.4f}")
            print(f"   R:R: 1:{setup.risk_reward:.1f} | Плечо: {setup.leverage}x | Уверенность: {setup.confidence*100:.0f}%")
            
            # Тестируем отправку уведомлений (включая Firebase)
            print(f"\n📤 Тестируем отправку уведомления для {setup.symbol}...")
            success = system.notification_manager.send_enhanced_alert(setup)
            if success:
                print(f"✅ Уведомление для {setup.symbol} отправлено успешно")
            else:
                print(f"❌ Ошибка отправки уведомления для {setup.symbol}")
    else:
        print("\n❌ Торговые возможности не найдены")
    
    # Для запуска непрерывного мониторинга раскомментировать:
    # print("\n🚀 Запуск непрерывного мониторинга...")
    # system.run_continuous_monitoring()