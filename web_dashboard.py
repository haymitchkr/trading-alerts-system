#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Веб-дашборд для системы торговых алертов
Использует Streamlit для создания интерактивного интерфейса
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import time
from datetime import datetime, timedelta
import threading
from advanced_trading_system import AdvancedTradingAlertSystem
from config import Config
import logging

# Настройка страницы
st.set_page_config(
    page_title="Trading Alerts Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Стили CSS
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #1f77b4;
}
.alert-card {
    background-color: #fff;
    padding: 1rem;
    border-radius: 0.5rem;
    border: 1px solid #ddd;
    margin-bottom: 1rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.success-alert {
    border-left: 4px solid #28a745;
}
.warning-alert {
    border-left: 4px solid #ffc107;
}
.danger-alert {
    border-left: 4px solid #dc3545;
}
</style>
""", unsafe_allow_html=True)

class DashboardManager:
    """Менеджер дашборда"""
    
    def __init__(self):
        self.system = None
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Инициализация session state
        if 'alerts_history' not in st.session_state:
            st.session_state.alerts_history = []
        if 'system_status' not in st.session_state:
            st.session_state.system_status = 'Остановлена'
        if 'last_scan_time' not in st.session_state:
            st.session_state.last_scan_time = None
        if 'scan_results' not in st.session_state:
            st.session_state.scan_results = []
    
    def initialize_system(self):
        """Инициализация торговой системы"""
        try:
            if self.system is None:
                self.system = AdvancedTradingAlertSystem()
                st.session_state.system_status = 'Готова'
                return True
        except Exception as e:
            st.error(f"Ошибка инициализации системы: {e}")
            return False
        return True
    
    def load_alerts_from_file(self):
        """Загрузка алертов из файла"""
        try:
            with open(Config.ALERTS_FILE, 'r', encoding='utf-8') as f:
                alerts = json.load(f)
                st.session_state.alerts_history = alerts
        except FileNotFoundError:
            st.session_state.alerts_history = []
        except Exception as e:
            st.error(f"Ошибка загрузки алертов: {e}")
    
    def run_single_scan(self, symbols=None):
        """Запуск одноразового сканирования"""
        if not self.initialize_system():
            return []
        
        try:
            with st.spinner('Сканирование рынков...'):
                results = self.system.run_single_scan(symbols)
                st.session_state.scan_results = results
                st.session_state.last_scan_time = datetime.now()
                
                # Сохраняем найденные алерты
                if results:
                    for setup in results:
                        alert_data = {
                            'symbol': setup.symbol,
                            'setup_type': setup.setup_type,
                            'entry_price': setup.entry_price,
                            'stop_loss': setup.stop_loss,
                            'take_profit': setup.take_profit,
                            'risk_reward': setup.risk_reward,
                            'confidence': setup.confidence,
                            'timestamp': setup.timestamp.isoformat(),
                            'description': setup.description,
                            'leverage': setup.leverage,
                            'position_size': setup.position_size
                        }
                        st.session_state.alerts_history.append(alert_data)
                    
                    # Сохраняем в файл
                    self.save_alerts_to_file()
                    logging.info(f"Найдено и сохранено {len(results)} алертов")
                
                return results
        except Exception as e:
            st.error(f"Ошибка сканирования: {e}")
            return []
    
    def save_alerts_to_file(self):
        """Сохранение алертов в файл"""
        try:
            with open(Config.ALERTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(st.session_state.alerts_history, f, ensure_ascii=False, indent=2)
            logging.info(f"Сохранено {len(st.session_state.alerts_history)} алертов в файл")
        except Exception as e:
            logging.error(f"Ошибка сохранения алертов: {e}")
            st.error(f"Ошибка сохранения алертов: {e}")
    
    def start_monitoring(self):
        """Запуск мониторинга в отдельном потоке"""
        if not self.monitoring_active and self.initialize_system():
            self.monitoring_active = True
            st.session_state.system_status = 'Мониторинг активен'
            
            def monitoring_loop():
                while self.monitoring_active:
                    try:
                        results = self.system.run_single_scan()
                        if results:
                            # Добавляем новые алерты
                            for setup in results:
                                alert_data = {
                                    'symbol': setup.symbol,
                                    'setup_type': setup.setup_type,
                                    'entry_price': setup.entry_price,
                                    'stop_loss': setup.stop_loss,
                                    'take_profit': setup.take_profit,
                                    'risk_reward': setup.risk_reward,
                                    'confidence': setup.confidence,
                                    'timestamp': setup.timestamp.isoformat(),
                                    'description': setup.description,
                                    'leverage': setup.leverage,
                                    'position_size': setup.position_size
                                }
                                st.session_state.alerts_history.append(alert_data)
                            
                            # Сохраняем алерты в файл
                            self.save_alerts_to_file()
                            logging.info(f"Найдено и сохранено {len(results)} новых алертов")
                        
                        st.session_state.last_scan_time = datetime.now()
                        time.sleep(Config.SCAN_INTERVAL_MINUTES * 60)
                        
                    except Exception as e:
                        logging.error(f"Ошибка в мониторинге: {e}")
                        time.sleep(60)
            
            self.monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
            self.monitoring_thread.start()
    
    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.monitoring_active = False
        st.session_state.system_status = 'Остановлена'
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            logging.info("Остановка потока мониторинга...")
        # Сохраняем алерты при остановке
        if st.session_state.alerts_history:
            self.save_alerts_to_file()

def render_sidebar():
    """Отрисовка боковой панели"""
    st.sidebar.title("🎛️ Управление")
    
    # Статус системы
    status = st.session_state.system_status
    if status == 'Мониторинг активен':
        st.sidebar.success(f"Статус: {status}")
    elif status == 'Готова':
        st.sidebar.info(f"Статус: {status}")
    else:
        st.sidebar.warning(f"Статус: {status}")
    
    # Последнее сканирование
    if st.session_state.last_scan_time:
        time_diff = datetime.now() - st.session_state.last_scan_time
        st.sidebar.text(f"Последнее сканирование: {time_diff.seconds // 60} мин назад")
    
    st.sidebar.markdown("---")
    
    # Настройки
    st.sidebar.subheader("⚙️ Настройки")
    
    # Риск на сделку
    risk_pct = st.sidebar.slider(
        "Риск на сделку (%)",
        min_value=1,
        max_value=20,
        value=Config.RISK_PERCENTAGE,
        help="Процент от депозита, который вы готовы рисковать на одной сделке"
    )
    Config.RISK_PERCENTAGE = risk_pct
    
    # Минимальное R:R
    min_rr = st.sidebar.slider(
        "Минимальное R:R",
        min_value=1.0,
        max_value=5.0,
        value=float(Config.MIN_RISK_REWARD),
        step=0.1,
        help="Минимальное соотношение риск/прибыль"
    )
    Config.MIN_RISK_REWARD = min_rr
    
    # Интервал сканирования
    scan_interval = st.sidebar.selectbox(
        "Интервал сканирования",
        [15, 30, 60, 120],
        index=1,
        help="Интервал между сканированиями в минутах"
    )
    Config.SCAN_INTERVAL_MINUTES = scan_interval
    
    # Фильтры
    st.sidebar.subheader("🔍 Фильтры")
    
    enable_btc_filter = st.sidebar.checkbox(
        "Фильтр по доминации BTC",
        value=Config.ENABLE_BTC_DOMINANCE_FILTER,
        help="Учитывать доминацию Bitcoin при поиске сетапов"
    )
    Config.ENABLE_BTC_DOMINANCE_FILTER = enable_btc_filter
    
    min_volume = st.sidebar.number_input(
        "Минимальный объем (USD)",
        min_value=100000,
        max_value=10000000,
        value=Config.MIN_VOLUME_USD,
        step=100000,
        help="Минимальный 24-часовой объем торгов"
    )
    Config.MIN_VOLUME_USD = min_volume
    
    return {
        'risk_percentage': risk_pct,
        'min_risk_reward': min_rr,
        'scan_interval': scan_interval,
        'enable_btc_filter': enable_btc_filter,
        'min_volume': min_volume
    }

def render_main_dashboard(dashboard_manager):
    """Отрисовка основного дашборда"""
    st.title("📈 Trading Alerts Dashboard")
    st.markdown("Система автоматического поиска торговых возможностей")

    # Предупреждение о демо-режиме
    if Config.is_demo_mode():
        st.warning("""
        **⚠️ ВНИМАНИЕ: Приложение работает в ДЕМО-РЕЖИМЕ.**

        Данные генерируются случайным образом и не являются реальными рыночными данными.
        Для перехода в реальный режим, пожалуйста, настройте API ключи в вашем `.env` файле.
        """)

    # Статус системы
    status_color = {
        'Остановлена': '🔴',
        'Готова': '🟡', 
        'Мониторинг активен': '🟢'
    }
    current_status = st.session_state.system_status
    st.markdown(f"**Статус системы:** {status_color.get(current_status, '⚪')} {current_status}")
    
    if st.session_state.last_scan_time:
        st.markdown(f"**Последнее сканирование:** {st.session_state.last_scan_time.strftime('%H:%M:%S %d.%m.%Y')}")
    
    st.markdown("---")
    
    # Метрики
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_alerts = len(st.session_state.alerts_history)
        st.metric("Всего алертов", total_alerts)
    
    with col2:
        today_alerts = len([
            alert for alert in st.session_state.alerts_history
            if datetime.fromisoformat(alert['timestamp']).date() == datetime.now().date()
        ])
        st.metric("Алертов сегодня", today_alerts)
    
    with col3:
        if st.session_state.alerts_history:
            avg_confidence = sum(alert['confidence'] for alert in st.session_state.alerts_history) / len(st.session_state.alerts_history)
            st.metric("Средняя уверенность", f"{avg_confidence*100:.1f}%")
        else:
            st.metric("Средняя уверенность", "0%")
    
    with col4:
        balance = Config.ACCOUNT_BALANCE
        st.metric("Баланс", f"${balance}")
    
    st.markdown("---")
    
    # Кнопки управления
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔍 Быстрое сканирование", type="primary"):
            results = dashboard_manager.run_single_scan()
            if results:
                st.success(f"Найдено {len(results)} торговых возможностей!")
            else:
                st.info("Торговые возможности не найдены")
    
    with col2:
        if st.button("🎯 Сканировать топ монеты"):
            results = dashboard_manager.run_single_scan(Config.PRIORITY_SYMBOLS)
            if results:
                st.success(f"Найдено {len(results)} возможностей в топ монетах!")
            else:
                st.info("Возможности в топ монетах не найдены")
    
    with col3:
        if st.session_state.system_status != 'Мониторинг активен':
            if st.button("▶️ Запустить мониторинг"):
                dashboard_manager.start_monitoring()
                st.success("Мониторинг запущен!")
                st.rerun()
        else:
            if st.button("⏹️ Остановить мониторинг"):
                dashboard_manager.stop_monitoring()
                st.info("Мониторинг остановлен")
                st.rerun()
    
    with col4:
        if st.button("🔄 Обновить данные"):
            dashboard_manager.load_alerts_from_file()
            st.success("Данные обновлены!")
            st.rerun()
    
    # Дополнительные кнопки
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Сохранить алерты"):
            dashboard_manager.save_alerts_to_file()
            st.success("Алерты сохранены в файл!")
    
    with col2:
        if st.button("🗑️ Очистить историю"):
            if st.session_state.alerts_history:
                st.session_state.alerts_history = []
                dashboard_manager.save_alerts_to_file()
                st.success("История очищена!")
                st.rerun()
            else:
                st.info("История уже пуста")
    
    with col3:
        if st.button("📊 Показать статистику"):
            if st.session_state.alerts_history:
                total = len(st.session_state.alerts_history)
                high_conf = len([a for a in st.session_state.alerts_history if a['confidence'] >= 0.8])
                avg_rr = sum(a['risk_reward'] for a in st.session_state.alerts_history) / total
                st.info(f"Всего: {total} | Высокая уверенность: {high_conf} | Средний R:R: 1:{avg_rr:.1f}")
            else:
                st.info("Нет данных для статистики")

def render_scan_results():
    """Отрисовка результатов сканирования"""
    if st.session_state.scan_results:
        st.subheader("🎯 Результаты последнего сканирования")
        
        for i, setup in enumerate(st.session_state.scan_results):
            with st.expander(f"{setup.symbol} - {setup.setup_type} (Уверенность: {setup.confidence*100:.0f}%)"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**💵 Вход:** ${setup.entry_price:.4f}")
                    st.write(f"**🛑 Стоп:** ${setup.stop_loss:.4f}")
                    st.write(f"**🎯 Цель:** ${setup.take_profit:.4f}")
                    st.write(f"**📊 R:R:** 1:{setup.risk_reward:.1f}")
                
                with col2:
                    st.write(f"**⚡ Плечо:** {setup.leverage}x")
                    st.write(f"**💰 Размер:** ${setup.position_size:.0f}")
                    st.write(f"**💸 Риск:** ${setup.risk_amount:.0f}")
                    st.write(f"**🌍 Рынок:** {setup.market_condition}")
                
                st.write(f"**📝 Описание:** {setup.description}")
                
                # Кнопки действий
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"📋 Копировать сигнал {i+1}", key=f"copy_{i}"):
                        signal_text = f"""
🚨 ТОРГОВЫЙ СИГНАЛ
💰 {setup.symbol}
📈 {setup.setup_type}
💵 Вход: ${setup.entry_price:.4f}
🛑 Стоп: ${setup.stop_loss:.4f}
🎯 Цель: ${setup.take_profit:.4f}
📊 R:R: 1:{setup.risk_reward:.1f}
⚡ Плечо: {setup.leverage}x
⭐ Уверенность: {setup.confidence*100:.0f}%
                        """
                        st.code(signal_text)
                
                with col2:
                    if st.button(f"📊 Показать график {i+1}", key=f"chart_{i}"):
                        st.info("Функция графиков будет добавлена в следующей версии")
                
                with col3:
                    if st.button(f"💾 Сохранить в избранное {i+1}", key=f"save_{i}"):
                        st.success("Сохранено в избранное!")

def render_alerts_history():
    """Отрисовка истории алертов"""
    st.subheader("📋 История алертов")
    
    if not st.session_state.alerts_history:
        st.info("История алертов пуста. Запустите сканирование для получения алертов.")
        return
    
    # Фильтры
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Фильтр по дате
        date_filter = st.selectbox(
            "Период",
            ["Все время", "Сегодня", "Вчера", "Последние 7 дней", "Последние 30 дней"]
        )
    
    with col2:
        # Фильтр по типу сетапа
        setup_types = list(set(alert['setup_type'] for alert in st.session_state.alerts_history))
        setup_filter = st.selectbox(
            "Тип сетапа",
            ["Все"] + setup_types
        )
    
    with col3:
        # Фильтр по уверенности
        confidence_filter = st.slider(
            "Минимальная уверенность (%)",
            0, 100, 0
        )
    
    # Применяем фильтры
    filtered_alerts = st.session_state.alerts_history.copy()
    
    # Фильтр по дате
    if date_filter != "Все время":
        now = datetime.now()
        if date_filter == "Сегодня":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_filter == "Вчера":
            start_date = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_filter == "Последние 7 дней":
            start_date = now - timedelta(days=7)
        elif date_filter == "Последние 30 дней":
            start_date = now - timedelta(days=30)
        
        filtered_alerts = [
            alert for alert in filtered_alerts
            if datetime.fromisoformat(alert['timestamp']) >= start_date
        ]
    
    # Фильтр по типу сетапа
    if setup_filter != "Все":
        filtered_alerts = [
            alert for alert in filtered_alerts
            if alert['setup_type'] == setup_filter
        ]
    
    # Фильтр по уверенности
    filtered_alerts = [
        alert for alert in filtered_alerts
        if alert['confidence'] * 100 >= confidence_filter
    ]
    
    # Сортировка по времени (новые сверху)
    filtered_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
    
    st.write(f"Показано {len(filtered_alerts)} из {len(st.session_state.alerts_history)} алертов")
    
    # Отображение алертов
    for alert in filtered_alerts[:20]:  # Показываем только последние 20
        timestamp = datetime.fromisoformat(alert['timestamp'])
        
        # Определяем цвет карточки по уверенности
        if alert['confidence'] >= 0.8:
            card_class = "success-alert"
        elif alert['confidence'] >= 0.6:
            card_class = "warning-alert"
        else:
            card_class = "danger-alert"
        
        with st.container():
            st.markdown(f"""
            <div class="alert-card {card_class}">
                <h4>{alert['symbol']} - {alert['setup_type']}</h4>
                <p><strong>Время:</strong> {timestamp.strftime('%d.%m.%Y %H:%M:%S')}</p>
                <p><strong>Вход:</strong> ${alert['entry_price']:.4f} | 
                   <strong>Стоп:</strong> ${alert['stop_loss']:.4f} | 
                   <strong>Цель:</strong> ${alert['take_profit']:.4f}</p>
                <p><strong>R:R:</strong> 1:{alert['risk_reward']:.1f} | 
                   <strong>Уверенность:</strong> {alert['confidence']*100:.0f}%</p>
                <p><strong>Описание:</strong> {alert.get('description', 'Нет описания')}</p>
            </div>
            """, unsafe_allow_html=True)

def render_analytics():
    """Отрисовка аналитики"""
    st.subheader("📊 Аналитика")
    
    if not st.session_state.alerts_history:
        st.info("Недостаточно данных для аналитики")
        return
    
    # Подготовка данных
    df = pd.DataFrame(st.session_state.alerts_history)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    df['hour'] = df['timestamp'].dt.hour
    
    col1, col2 = st.columns(2)
    
    with col1:
        # График алертов по дням
        daily_alerts = df.groupby('date').size().reset_index(name='count')
        fig_daily = px.line(
            daily_alerts, 
            x='date', 
            y='count',
            title='Количество алертов по дням',
            labels={'date': 'Дата', 'count': 'Количество алертов'}
        )
        st.plotly_chart(fig_daily, use_container_width=True)
    
    with col2:
        # График по типам сетапов
        setup_counts = df['setup_type'].value_counts()
        fig_setups = px.pie(
            values=setup_counts.values,
            names=setup_counts.index,
            title='Распределение по типам сетапов'
        )
        st.plotly_chart(fig_setups, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Распределение уверенности
        fig_confidence = px.histogram(
            df,
            x='confidence',
            nbins=20,
            title='Распределение уверенности',
            labels={'confidence': 'Уверенность', 'count': 'Количество'}
        )
        st.plotly_chart(fig_confidence, use_container_width=True)
    
    with col2:
        # Топ символов
        symbol_counts = df['symbol'].value_counts().head(10)
        fig_symbols = px.bar(
            x=symbol_counts.values,
            y=symbol_counts.index,
            orientation='h',
            title='Топ-10 символов по количеству алертов',
            labels={'x': 'Количество алертов', 'y': 'Символ'}
        )
        st.plotly_chart(fig_symbols, use_container_width=True)
    
    # Статистика
    st.subheader("📈 Статистика")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_rr = df['risk_reward'].mean()
        st.metric("Среднее R:R", f"1:{avg_rr:.1f}")
    
    with col2:
        avg_confidence = df['confidence'].mean()
        st.metric("Средняя уверенность", f"{avg_confidence*100:.1f}%")
    
    with col3:
        high_confidence = len(df[df['confidence'] >= 0.8])
        st.metric("Высокая уверенность (≥80%)", high_confidence)
    
    with col4:
        unique_symbols = df['symbol'].nunique()
        st.metric("Уникальных символов", unique_symbols)

def main():
    """Главная функция приложения"""
    # Инициализация менеджера дашборда
    dashboard_manager = DashboardManager()
    
    # Загрузка данных при запуске
    dashboard_manager.load_alerts_from_file()
    
    # Боковая панель
    settings = render_sidebar()
    
    # Основной контент
    tab1, tab2, tab3, tab4 = st.tabs(["🏠 Главная", "🎯 Результаты", "📋 История", "📊 Аналитика"])
    
    with tab1:
        render_main_dashboard(dashboard_manager)
    
    with tab2:
        render_scan_results()
    
    with tab3:
        render_alerts_history()
    
    with tab4:
        render_analytics()
    
    # Автообновление если мониторинг активен
    if st.session_state.system_status == 'Мониторинг активен':
        # Показываем индикатор активного мониторинга
        st.sidebar.success("🔄 Мониторинг активен")
        st.sidebar.info("Страница автоматически обновляется")
        
        # Автообновление каждые 10 секунд
        time.sleep(10)
        st.rerun()
    else:
        st.sidebar.info("ℹ️ Мониторинг остановлен")

if __name__ == "__main__":
    main()