# story_manager.py
import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any

class StoryManager:
    """Менеджер для работы с сюжетом и выделением элементов"""
    
    def __init__(self, logger_client=None):
        self.logger = logger_client
        self.current_story = None
        self.extracted_items = {
            'locations': [],
            'characters': [],
            'monsters': [],
            'items': []
        }
    
    def parse_story_text(self, text: str) -> Dict[str, Any]:
        """Парсит текст и выделяет ключевые элементы"""
        
        # Словари ключевых слов для распознавания
        location_keywords = ['город', 'деревня', 'замок', 'пещера', 'лес', 'гора', 'долина', 
                            'таверна', 'храм', 'башня', 'подземелье', 'дворец', 'площадь']
        
        character_keywords = ['король', 'королева', 'принц', 'принцесса', 'лорд', 'леди', 
                             'рыцарь', 'маг', 'волшебник', 'жрец', 'купец', 'крестьянин']
        
        monster_keywords = ['дракон', 'гоблин', 'орк', 'тролль', 'скелет', 'зомби', 'вампир',
                           'оборотень', 'гигант', 'демон', 'призрак', 'гарпия', 'минотавр']
        
        item_keywords = ['меч', 'щит', 'кольцо', 'амулет', 'зелье', 'свиток', 'артефакт',
                        'книга', 'ключ', 'сундук', 'сокровище', 'золото', 'оружие', 'броня']
        
        extracted = {
            'locations': [],
            'characters': [],
            'monsters': [],
            'items': []
        }
        
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Поиск локаций
            for kw in location_keywords:
                if kw in sentence_lower:
                    # Извлекаем фразу с локацией
                    words = sentence.split()
                    for i, word in enumerate(words):
                        if kw in word.lower():
                            location_name = ' '.join(words[max(0, i-2):min(len(words), i+3)])
                            extracted['locations'].append({
                                'name': location_name.strip(),
                                'context': sentence.strip(),
                                'keyword': kw
                            })
                            break
            
            # Поиск персонажей
            for kw in character_keywords:
                if kw in sentence_lower:
                    words = sentence.split()
                    for i, word in enumerate(words):
                        if kw in word.lower():
                            char_name = ' '.join(words[max(0, i-2):min(len(words), i+3)])
                            extracted['characters'].append({
                                'name': char_name.strip(),
                                'context': sentence.strip(),
                                'keyword': kw
                            })
                            break
            
            # Поиск монстров
            for kw in monster_keywords:
                if kw in sentence_lower:
                    words = sentence.split()
                    for i, word in enumerate(words):
                        if kw in word.lower():
                            monster_name = ' '.join(words[max(0, i-2):min(len(words), i+3)])
                            extracted['monsters'].append({
                                'name': monster_name.strip(),
                                'context': sentence.strip(),
                                'keyword': kw
                            })
                            break
            
            # Поиск предметов
            for kw in item_keywords:
                if kw in sentence_lower:
                    words = sentence.split()
                    for i, word in enumerate(words):
                        if kw in word.lower():
                            item_name = ' '.join(words[max(0, i-2):min(len(words), i+3)])
                            extracted['items'].append({
                                'name': item_name.strip(),
                                'context': sentence.strip(),
                                'keyword': kw
                            })
                            break
        
        # Удаляем дубликаты
        for key in extracted:
            extracted[key] = self._remove_duplicates(extracted[key])
        
        return extracted
    
    def _remove_duplicates(self, items: List[Dict]) -> List[Dict]:
        """Удаляет дубликаты из списка"""
        seen = set()
        unique = []
        for item in items:
            name_key = item['name'].lower()
            if name_key not in seen:
                seen.add(name_key)
                unique.append(item)
        return unique
    
    def save_story_to_file(self, text: str, filename: str = None) -> str:
        """Сохраняет текст сюжета в файл"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"story_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"=== СЮЖЕТ ===\n")
            f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*50}\n\n")
            f.write(text)
            f.write(f"\n\n{'='*50}\n")
            f.write(f"=== ВЫДЕЛЕННЫЕ ЭЛЕМЕНТЫ ===\n\n")
            
            f.write("ЛОКАЦИИ:\n")
            for loc in self.extracted_items['locations']:
                f.write(f"  - {loc['name']}\n")
            
            f.write("\nПЕРСОНАЖИ:\n")
            for char in self.extracted_items['characters']:
                f.write(f"  - {char['name']}\n")
            
            f.write("\nМОНСТРЫ/ПРОТИВНИКИ:\n")
            for monster in self.extracted_items['monsters']:
                f.write(f"  - {monster['name']}\n")
            
            f.write("\nПРЕДМЕТЫ:\n")
            for item in self.extracted_items['items']:
                f.write(f"  - {item['name']}\n")
        
        return filename
    
    def process_and_log(self, text: str, gamemaster_id: int, session_id: int = None):
        """Обрабатывает текст и логирует выделенные элементы"""
        self.extracted_items = self.parse_story_text(text)
        
        if self.logger:
            # Логируем локации
            for loc in self.extracted_items['locations']:
                self.logger.log_action(
                    'story_location',
                    details={'location': loc['name'], 'context': loc['context']}
                )
            
            # Логируем персонажей
            for char in self.extracted_items['characters']:
                self.logger.log_action(
                    'story_character',
                    details={'character': char['name'], 'context': char['context']}
                )
            
            # Логируем монстров
            for monster in self.extracted_items['monsters']:
                self.logger.log_action(
                    'story_monster',
                    details={'monster': monster['name'], 'context': monster['context']}
                )
            
            # Логируем предметы
            for item in self.extracted_items['items']:
                self.logger.log_action(
                    'story_item',
                    details={'item': item['name'], 'context': item['context']}
                )
        
        return self.extracted_items