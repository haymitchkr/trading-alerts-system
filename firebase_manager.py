#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Менеджер для работы с Firebase Firestore
"""

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import os
from config import Config

class FirebaseManager:
    """Класс для работы с Firebase Firestore"""
    
    def __init__(self):
        self.db = None
        self.app = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Инициализация Firebase"""
        try:
            # Проверяем, что путь к ключу указан
            if not Config.FIREBASE_SERVICE_ACCOUNT_KEY:
                print("⚠️ Firebase ключ не настроен. Firestore будет недоступен.")
                return
            
            # Проверяем, что файл существует
            if not os.path.exists(Config.FIREBASE_SERVICE_ACCOUNT_KEY):
                print(f"⚠️ Файл Firebase ключа не найден: {Config.FIREBASE_SERVICE_ACCOUNT_KEY}")
                return
            
            # Инициализируем Firebase только если еще не инициализирован
            if not firebase_admin._apps:
                cred = credentials.Certificate(Config.FIREBASE_SERVICE_ACCOUNT_KEY)
                self.app = firebase_admin.initialize_app(cred)
            else:
                self.app = firebase_admin.get_app()
            
            # Получаем клиент Firestore
            self.db = firestore.client()
            print("✅ Firebase Firestore успешно подключен")
            
        except Exception as e:
            print(f"❌ Ошибка инициализации Firebase: {e}")
            self.db = None
    
    def is_connected(self) -> bool:
        """Проверка подключения к Firebase"""
        return self.db is not None
    
    def save_alert(self, alert_data: Dict[str, Any]) -> Optional[str]:
        """Сохранение алерта в Firestore"""
        if not self.is_connected():
            return None
        
        try:
            # Добавляем timestamp
            alert_data['created_at'] = firestore.SERVER_TIMESTAMP
            alert_data['date'] = datetime.now().isoformat()
            
            # Сохраняем в коллекцию 'alerts'
            doc_ref = self.db.collection('alerts').add(alert_data)
            doc_id = doc_ref[1].id
            
            print(f"✅ Алерт сохранен в Firebase: {doc_id}")
            return doc_id
            
        except Exception as e:
            print(f"❌ Ошибка сохранения алерта в Firebase: {e}")
            return None
    
    def get_alerts(self, limit: int = 50, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Получение алертов из Firestore"""
        if not self.is_connected():
            return []
        
        try:
            query = self.db.collection('alerts')
            
            # Фильтр по символу если указан
            if symbol:
                query = query.where('symbol', '==', symbol)
            
            # Сортировка по дате создания (новые первыми)
            query = query.order_by('created_at', direction=firestore.Query.DESCENDING)
            
            # Лимит
            query = query.limit(limit)
            
            docs = query.stream()
            alerts = []
            
            for doc in docs:
                alert_data = doc.to_dict()
                alert_data['id'] = doc.id
                alerts.append(alert_data)
            
            return alerts
            
        except Exception as e:
            print(f"❌ Ошибка получения алертов из Firebase: {e}")
            return []
    
    def save_performance_data(self, performance_data: Dict[str, Any]) -> Optional[str]:
        """Сохранение данных производительности"""
        if not self.is_connected():
            return None
        
        try:
            performance_data['timestamp'] = firestore.SERVER_TIMESTAMP
            performance_data['date'] = datetime.now().isoformat()
            
            doc_ref = self.db.collection('performance').add(performance_data)
            doc_id = doc_ref[1].id
            
            print(f"✅ Данные производительности сохранены: {doc_id}")
            return doc_id
            
        except Exception as e:
            print(f"❌ Ошибка сохранения данных производительности: {e}")
            return None
    
    def get_performance_stats(self, days: int = 30) -> Dict[str, Any]:
        """Получение статистики производительности за период"""
        if not self.is_connected():
            return {}
        
        try:
            # Получаем данные за последние N дней
            from datetime import timedelta
            start_date = datetime.now() - timedelta(days=days)
            
            alerts = self.db.collection('alerts')\
                .where('created_at', '>=', start_date)\
                .stream()
            
            total_alerts = 0
            symbols = set()
            patterns = {}
            
            for doc in alerts:
                data = doc.to_dict()
                total_alerts += 1
                
                if 'symbol' in data:
                    symbols.add(data['symbol'])
                
                if 'pattern' in data:
                    pattern = data['pattern']
                    patterns[pattern] = patterns.get(pattern, 0) + 1
            
            return {
                'period_days': days,
                'total_alerts': total_alerts,
                'unique_symbols': len(symbols),
                'patterns_distribution': patterns,
                'symbols_list': list(symbols)
            }
            
        except Exception as e:
            print(f"❌ Ошибка получения статистики: {e}")
            return {}
    
    def delete_old_alerts(self, days_old: int = 90) -> int:
        """Удаление старых алертов"""
        if not self.is_connected():
            return 0
        
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # Получаем старые документы
            old_docs = self.db.collection('alerts')\
                .where('created_at', '<', cutoff_date)\
                .stream()
            
            deleted_count = 0
            batch = self.db.batch()
            
            for doc in old_docs:
                batch.delete(doc.reference)
                deleted_count += 1
                
                # Выполняем batch каждые 500 документов
                if deleted_count % 500 == 0:
                    batch.commit()
                    batch = self.db.batch()
            
            # Выполняем оставшиеся операции
            if deleted_count % 500 != 0:
                batch.commit()
            
            print(f"✅ Удалено {deleted_count} старых алертов")
            return deleted_count
            
        except Exception as e:
            print(f"❌ Ошибка удаления старых алертов: {e}")
            return 0

# Глобальный экземпляр менеджера
firebase_manager = FirebaseManager()