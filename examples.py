#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Примеры использования системы торговых алертов
Демонстрирует различные способы запуска и настройки системы
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Импорты наших модулей
from advanced_trading_system import AdvancedTradingAlertSystem
from config import *
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/examples.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TradingSystemExamples:
    """Класс с примерами использования торговой системы"""
    
    def __init__(self):
        self.system = AdvancedTradingAlertSystem()
        
    def example_1_basic_scan(self):
        """Пример 1: Базовое сканирование рынка"""
        print("\n" + "="*50)
        print("ПРИМЕР 1: БАЗОВОЕ СКАНИРОВАНИЕ")
        print("="*50)
        
        try:
            # Запускаем одноразовое сканирование
            alerts = self.system.scan_market()
            
            print(f"\n📊 Найдено алертов: {len(alerts)}")
            
            for i, alert in enumerate(alerts[:3], 1):  # Показываем первые 3
                print(f"\n🚨 Алерт #{i}:")
                print(f"   Символ: {alert['symbol']}")
                print(f"   Тип: {alert['setup_type']}")
                print(f"   Вход: ${alert['entry_price']:.4f}")
                print(f"   Стоп: ${alert['stop_loss']:.4f}")
                print(f"   Цель: ${alert['take_profit']:.4f}")
                print(f"   R:R: 1:{alert['risk_reward']:.1f}")
                print(f"   Уверенность: {alert['confidence']:.1f}%")
                
        except Exception as e:
            logger.error(f"Ошибка в базовом сканировании: {e}")
            
    def example_2_filtered_scan(self):
        """Пример 2: Сканирование с кастомными фильтрами"""
        print("\n" + "="*50)
        print("ПРИМЕР 2: СКАНИРОВАНИЕ С ФИЛЬТРАМИ")
        print("="*50)
        
        # Кастомные настройки для более агрессивной торговли
        custom_config = {
            'risk_per_trade': 8.0,  # Повышенный риск
            'min_risk_reward': 2.5,  # Более низкий R:R
            'max_stop_loss': 3.0,    # Больший стоп
            'min_volume_24h': 5000000,  # Меньший объем
            'min_confidence': 60.0   # Пониженная уверенность
        }
        
        try:
            # Временно изменяем настройки
            original_config = {
                'risk_per_trade': TRADING_CONFIG['risk_per_trade'],
                'min_risk_reward': TRADING_CONFIG['min_risk_reward'],
                'max_stop_loss': TRADING_CONFIG['max_stop_loss']
            }
            
            # Применяем кастомные настройки
            TRADING_CONFIG.update(custom_config)
            MARKET_FILTERS.update({
                'min_volume_24h': custom_config['min_volume_24h']
            })
            
            alerts = self.system.scan_market()
            
            print(f"\n📊 Найдено алертов с кастомными фильтрами: {len(alerts)}")
            print(f"⚙️ Настройки: Риск {custom_config['risk_per_trade']}%, R:R 1:{custom_config['min_risk_reward']}")
            
            # Восстанавливаем оригинальные настройки
            TRADING_CONFIG.update(original_config)
            
        except Exception as e:
            logger.error(f"Ошибка в фильтрованном сканировании: {e}")
            
    def example_3_watchlist_scan(self):
        """Пример 3: Сканирование только watchlist"""
        print("\n" + "="*50)
        print("ПРИМЕР 3: СКАНИРОВАНИЕ WATCHLIST")
        print("="*50)
        
        # Кастомный watchlist
        custom_watchlist = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT']
        
        try:
            # Временно заменяем watchlist
            original_watchlist = WATCHLIST.copy()
            WATCHLIST.clear()
            WATCHLIST.extend(custom_watchlist)
            
            alerts = self.system.scan_market()
            
            print(f"\n📊 Сканирование watchlist: {custom_watchlist}")
            print(f"🎯 Найдено алертов: {len(alerts)}")
            
            for alert in alerts:
                print(f"   {alert['symbol']}: {alert['setup_type']} (уверенность: {alert['confidence']:.1f}%)")
            
            # Восстанавливаем оригинальный watchlist
            WATCHLIST.clear()
            WATCHLIST.extend(original_watchlist)
            
        except Exception as e:
            logger.error(f"Ошибка в сканировании watchlist: {e}")
            
    def example_4_setup_analysis(self):
        """Пример 4: Анализ конкретного сетапа"""
        print("\n" + "="*50)
        print("ПРИМЕР 4: АНАЛИЗ КОНКРЕТНОГО СЕТАПА")
        print("="*50)
        
        symbol = 'BTCUSDT'
        
        try:
            # Получаем данные для символа
            data_provider = self.system.data_provider
            market_data = data_provider.get_ohlcv_data(symbol, '1h', 100)
            
            if market_data is not None and not market_data.empty:
                # Добавляем технические индикаторы
                enhanced_data = data_provider.add_technical_indicators(market_data)
                
                # Анализируем сетапы
                setup_detector = self.system.setup_detector
                setups = setup_detector.detect_all_setups(symbol, enhanced_data)
                
                print(f"\n📈 Анализ {symbol}:")
                print(f"   Текущая цена: ${enhanced_data['close'].iloc[-1]:.2f}")
                print(f"   RSI: {enhanced_data['rsi'].iloc[-1]:.1f}")
                print(f"   Объем (24ч): {enhanced_data['volume'].iloc[-24:].sum():,.0f}")
                
                if setups:
                    print(f"\n🎯 Найденные сетапы:")
                    for setup in setups:
                        print(f"   • {setup.setup_type}: уверенность {setup.confidence:.1f}%")
                        print(f"     Вход: ${setup.entry_price:.4f}, Стоп: ${setup.stop_loss:.4f}")
                        print(f"     R:R: 1:{setup.risk_reward:.1f}")
                else:
                    print("   ❌ Сетапы не найдены")
            else:
                print(f"   ❌ Не удалось получить данные для {symbol}")
                
        except Exception as e:
            logger.error(f"Ошибка в анализе сетапа: {e}")
            
    def example_5_backtesting_simulation(self):
        """Пример 5: Симуляция бэктестинга"""
        print("\n" + "="*50)
        print("ПРИМЕР 5: СИМУЛЯЦИЯ БЭКТЕСТИНГА")
        print("="*50)
        
        try:
            # Симулируем торговлю за последние 7 дней
            start_balance = 220.0
            current_balance = start_balance
            trades_count = 0
            winning_trades = 0
            
            # Загружаем историю алертов (если есть)
            try:
                with open('data/alerts_history.json', 'r', encoding='utf-8') as f:
                    alerts_history = json.load(f)
            except FileNotFoundError:
                alerts_history = []
            
            # Фильтруем алерты за последние 7 дней
            week_ago = datetime.now() - timedelta(days=7)
            recent_alerts = [
                alert for alert in alerts_history 
                if datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00')) > week_ago
            ]
            
            print(f"\n📊 Анализ {len(recent_alerts)} алертов за последние 7 дней")
            
            for alert in recent_alerts[:10]:  # Анализируем первые 10
                # Симулируем результат сделки (случайный для примера)
                import random
                
                risk_amount = current_balance * (alert.get('risk_percentage', 5) / 100)
                
                # 70% шанс на успех (оптимистично)
                if random.random() < 0.7:
                    # Успешная сделка
                    profit = risk_amount * alert.get('risk_reward', 3)
                    current_balance += profit
                    winning_trades += 1
                    result = "✅ Прибыль"
                else:
                    # Убыточная сделка
                    current_balance -= risk_amount
                    result = "❌ Убыток"
                
                trades_count += 1
                
                print(f"   Сделка #{trades_count}: {alert['symbol']} - {result}")
                print(f"   Баланс: ${current_balance:.2f}")
            
            # Статистика
            total_return = ((current_balance - start_balance) / start_balance) * 100
            win_rate = (winning_trades / trades_count * 100) if trades_count > 0 else 0
            
            print(f"\n📈 РЕЗУЛЬТАТЫ СИМУЛЯЦИИ:")
            print(f"   Начальный баланс: ${start_balance:.2f}")
            print(f"   Конечный баланс: ${current_balance:.2f}")
            print(f"   Общая доходность: {total_return:+.1f}%")
            print(f"   Количество сделок: {trades_count}")
            print(f"   Процент прибыльных: {win_rate:.1f}%")
            
        except Exception as e:
            logger.error(f"Ошибка в симуляции бэктестинга: {e}")
            
    def example_6_market_conditions_analysis(self):
        """Пример 6: Анализ рыночных условий"""
        print("\n" + "="*50)
        print("ПРИМЕР 6: АНАЛИЗ РЫНОЧНЫХ УСЛОВИЙ")
        print("="*50)
        
        try:
            data_provider = self.system.data_provider
            
            # Анализируем BTC как индикатор рынка
            btc_data = data_provider.get_ohlcv_data('BTCUSDT', '1d', 30)
            
            if btc_data is not None and not btc_data.empty:
                # Добавляем индикаторы
                btc_enhanced = data_provider.add_technical_indicators(btc_data)
                
                # Анализируем тренд
                current_price = btc_enhanced['close'].iloc[-1]
                ema_21 = btc_enhanced['ema'].iloc[-1]
                rsi = btc_enhanced['rsi'].iloc[-1]
                
                # Изменение за последние дни
                change_7d = ((current_price - btc_enhanced['close'].iloc[-8]) / btc_enhanced['close'].iloc[-8]) * 100
                change_30d = ((current_price - btc_enhanced['close'].iloc[-31]) / btc_enhanced['close'].iloc[-31]) * 100
                
                # Определяем рыночные условия
                if current_price > ema_21 and rsi > 50 and change_7d > 0:
                    market_condition = "🟢 Бычий рынок"
                    recommendation = "Агрессивная торговля, лонговые сетапы"
                elif current_price < ema_21 and rsi < 50 and change_7d < -5:
                    market_condition = "🔴 Медвежий рынок"
                    recommendation = "Осторожная торговля, избегать лонгов"
                else:
                    market_condition = "🟡 Боковой рынок"
                    recommendation = "Умеренная торговля, скальпинг"
                
                print(f"\n📊 АНАЛИЗ РЫНОЧНЫХ УСЛОВИЙ (BTC):")
                print(f"   Текущая цена: ${current_price:,.2f}")
                print(f"   EMA(21): ${ema_21:,.2f}")
                print(f"   RSI: {rsi:.1f}")
                print(f"   Изменение за 7 дней: {change_7d:+.1f}%")
                print(f"   Изменение за 30 дней: {change_30d:+.1f}%")
                print(f"\n🎯 Состояние рынка: {market_condition}")
                print(f"💡 Рекомендация: {recommendation}")
                
                # Рекомендуемые настройки
                if "Бычий" in market_condition:
                    print(f"\n⚙️ РЕКОМЕНДУЕМЫЕ НАСТРОЙКИ:")
                    print(f"   Риск на сделку: 7-10%")
                    print(f"   Минимальный R:R: 1:2.5")
                    print(f"   Фокус на: пробои, импульсы")
                elif "Медвежий" in market_condition:
                    print(f"\n⚙️ РЕКОМЕНДУЕМЫЕ НАСТРОЙКИ:")
                    print(f"   Риск на сделку: 3-5%")
                    print(f"   Минимальный R:R: 1:4")
                    print(f"   Фокус на: отскоки от поддержек")
                else:
                    print(f"\n⚙️ РЕКОМЕНДУЕМЫЕ НАСТРОЙКИ:")
                    print(f"   Риск на сделку: 5-7%")
                    print(f"   Минимальный R:R: 1:3")
                    print(f"   Фокус на: диапазонная торговля")
                    
        except Exception as e:
            logger.error(f"Ошибка в анализе рыночных условий: {e}")
            
    def example_7_performance_monitoring(self):
        """Пример 7: Мониторинг производительности системы"""
        print("\n" + "="*50)
        print("ПРИМЕР 7: МОНИТОРИНГ ПРОИЗВОДИТЕЛЬНОСТИ")
        print("="*50)
        
        try:
            start_time = time.time()
            
            # Тестируем скорость различных операций
            print("\n⏱️ Тестирование производительности...")
            
            # 1. Скорость получения данных
            data_start = time.time()
            market_data = self.system.data_provider.get_ohlcv_data('BTCUSDT', '1h', 100)
            data_time = time.time() - data_start
            print(f"   Получение данных: {data_time:.2f}с")
            
            # 2. Скорость добавления индикаторов
            if market_data is not None:
                indicators_start = time.time()
                enhanced_data = self.system.data_provider.add_technical_indicators(market_data)
                indicators_time = time.time() - indicators_start
                print(f"   Расчет индикаторов: {indicators_time:.2f}с")
                
                # 3. Скорость детекции сетапов
                detection_start = time.time()
                setups = self.system.setup_detector.detect_all_setups('BTCUSDT', enhanced_data)
                detection_time = time.time() - detection_start
                print(f"   Детекция сетапов: {detection_time:.2f}с")
            
            # 4. Общее время сканирования
            scan_start = time.time()
            alerts = self.system.scan_market()
            scan_time = time.time() - scan_start
            print(f"   Полное сканирование: {scan_time:.2f}с")
            
            total_time = time.time() - start_time
            
            print(f"\n📊 РЕЗУЛЬТАТЫ ПРОИЗВОДИТЕЛЬНОСТИ:")
            print(f"   Общее время тестирования: {total_time:.2f}с")
            print(f"   Найдено алертов: {len(alerts)}")
            print(f"   Скорость обработки: {len(alerts)/scan_time:.1f} алертов/сек")
            
            # Рекомендации по оптимизации
            if scan_time > 30:
                print(f"\n⚠️ РЕКОМЕНДАЦИИ ПО ОПТИМИЗАЦИИ:")
                print(f"   • Увеличьте интервал сканирования")
                print(f"   • Уменьшите количество символов")
                print(f"   • Используйте более строгие фильтры")
            else:
                print(f"\n✅ Производительность в норме")
                
        except Exception as e:
            logger.error(f"Ошибка в мониторинге производительности: {e}")
            
    def run_all_examples(self):
        """Запуск всех примеров"""
        print("🚀 ЗАПУСК ВСЕХ ПРИМЕРОВ ИСПОЛЬЗОВАНИЯ")
        print("="*60)
        
        examples = [
            self.example_1_basic_scan,
            self.example_2_filtered_scan,
            self.example_3_watchlist_scan,
            self.example_4_setup_analysis,
            self.example_5_backtesting_simulation,
            self.example_6_market_conditions_analysis,
            self.example_7_performance_monitoring
        ]
        
        for i, example in enumerate(examples, 1):
            try:
                print(f"\n🔄 Выполнение примера {i}/7...")
                example()
                time.sleep(2)  # Пауза между примерами
            except Exception as e:
                logger.error(f"Ошибка в примере {i}: {e}")
                continue
        
        print("\n✅ Все примеры выполнены!")
        print("\n💡 Для запуска конкретного примера используйте:")
        print("   python examples.py --example 1")

def main():
    """Главная функция"""
    import sys
    
    examples = TradingSystemExamples()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--example':
        if len(sys.argv) > 2:
            example_num = int(sys.argv[2])
            if example_num == 1:
                examples.example_1_basic_scan()
            elif example_num == 2:
                examples.example_2_filtered_scan()
            elif example_num == 3:
                examples.example_3_watchlist_scan()
            elif example_num == 4:
                examples.example_4_setup_analysis()
            elif example_num == 5:
                examples.example_5_backtesting_simulation()
            elif example_num == 6:
                examples.example_6_market_conditions_analysis()
            elif example_num == 7:
                examples.example_7_performance_monitoring()
            else:
                print("Доступные примеры: 1-7")
        else:
            print("Укажите номер примера: python examples.py --example 1")
    else:
        examples.run_all_examples()

if __name__ == "__main__":
    main()