# db/Plot/story_manager.py
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
        location_keywords = [
            'город', 'деревня', 'замок', 'пещера', 'лес', 'гора', 'долина', 
            'таверна', 'храм', 'башня', 'подземелье', 'дворец', 'площадь',
            'село', 'поселение', 'крепость', 'руины', 'болото', 'пустыня',
            'озеро', 'река', 'море', 'океан', 'остров', 'портал'
        ]
        
        character_keywords = [
            'король', 'королева', 'принц', 'принцесса', 'лорд', 'леди', 
            'рыцарь', 'маг', 'волшебник', 'жрец', 'купец', 'крестьянин',
            'воин', 'лучник', 'разбойник', 'вор', 'паладин', 'друид',
            'колдун', 'чародей', 'алхимик', 'инквизитор', 'стражник'
        ]
        
        monster_keywords = [
            'дракон', 'гоблин', 'орк', 'тролль', 'скелет', 'зомби', 'вампир',
            'оборотень', 'гигант', 'демон', 'призрак', 'гарпия', 'минотавр',
            'кобольд', 'огр', 'химера', 'грифон', 'пегас', 'единорог',
            'василиск', 'медуза', 'циклоп', 'элементаль', 'лих'
        ]
        
        item_keywords = [
            'меч', 'щит', 'кольцо', 'амулет', 'зелье', 'свиток', 'артефакт',
            'книга', 'ключ', 'сундук', 'сокровище', 'золото', 'оружие', 'броня',
            'шлем', 'перчатки', 'сапоги', 'плащ', 'посох', 'кинжал', 'лук',
            'арбалет', 'топор', 'молот', 'копье', 'алебарда'
        ]
        
        extracted = {
            'locations': [],
            'characters': [],
            'monsters': [],
            'items': []
        }
        
        # Разбиваем на предложения
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            sentence_lower = sentence.lower()
            
            # Поиск локаций
            for kw in location_keywords:
                if kw in sentence_lower:
                    words = sentence.split()
                    for i, word in enumerate(words):
                        if kw in word.lower():
                            start = max(0, i-2)
                            end = min(len(words), i+3)
                            location_name = ' '.join(words[start:end])
                            extracted['locations'].append({
                                'name': location_name.strip(),
                                'context': sentence.strip(),
                                'keyword': kw,
                                'type': 'location'
                            })
                            break
            
            # Поиск персонажей
            for kw in character_keywords:
                if kw in sentence_lower:
                    words = sentence.split()
                    for i, word in enumerate(words):
                        if kw in word.lower():
                            start = max(0, i-2)
                            end = min(len(words), i+3)
                            char_name = ' '.join(words[start:end])
                            extracted['characters'].append({
                                'name': char_name.strip(),
                                'context': sentence.strip(),
                                'keyword': kw,
                                'type': 'character'
                            })
                            break
            
            # Поиск монстров
            for kw in monster_keywords:
                if kw in sentence_lower:
                    words = sentence.split()
                    for i, word in enumerate(words):
                        if kw in word.lower():
                            start = max(0, i-2)
                            end = min(len(words), i+3)
                            monster_name = ' '.join(words[start:end])
                            extracted['monsters'].append({
                                'name': monster_name.strip(),
                                'context': sentence.strip(),
                                'keyword': kw,
                                'type': 'monster'
                            })
                            break
            
            # Поиск предметов
            for kw in item_keywords:
                if kw in sentence_lower:
                    words = sentence.split()
                    for i, word in enumerate(words):
                        if kw in word.lower():
                            start = max(0, i-2)
                            end = min(len(words), i+3)
                            item_name = ' '.join(words[start:end])
                            extracted['items'].append({
                                'name': item_name.strip(),
                                'context': sentence.strip(),
                                'keyword': kw,
                                'type': 'item'
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
            f.write("=" * 60 + "
")
            f.write("СЮЖЕТ
")
            f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
")
            f.write("=" * 60 + "

")
            f.write(text)
            f.write("

" + "=" * 60 + "
")
            f.write("ВЫДЕЛЕННЫЕ ЭЛЕМЕНТЫ
")
            f.write("=" * 60 + "

")
            
            f.write("ЛОКАЦИИ:
")
            for loc in self.extracted_items['locations']:
                f.write(f"  • {loc['name']}
")
                if loc.get('context'):
                    f.write(f"    Контекст: {loc['context'][:100]}...
")
            f.write("
")
            
            f.write("ПЕРСОНАЖИ:
")
            for char in self.extracted_items['characters']:
                f.write(f"  • {char['name']}
")
                if char.get('context'):
                    f.write(f"    Контекст: {char['context'][:100]}...
")
            f.write("
")
            
            f.write("МОНСТРЫ/ПРОТИВНИКИ:
")
            for monster in self.extracted_items['monsters']:
                f.write(f"  • {monster['name']}
")
                if monster.get('context'):
                    f.write(f"    Контекст: {monster['context'][:100]}...
")
            f.write("
")
            
            f.write("ПРЕДМЕТЫ:
")
            for item in self.extracted_items['items']:
                f.write(f"  • {item['name']}
")
                if item.get('context'):
                    f.write(f"    Контекст: {item['context'][:100]}...
")
            f.write("
")
            
            f.write("=" * 60 + "
")
            f.write("Конец документа
")
        
        return filename
    
    def process_and_log(self, text: str, gamemaster_id: int, session_id: int = None):
        """Обрабатывает текст и логирует выделенные элементы"""
        self.extracted_items = self.parse_story_text(text)
        
        if self.logger:
            # Логируем создание сюжета
            self.logger.log_action(
                'create_story',
                session_id=session_id,
                details={
                    'text_length': len(text),
                    'locations_count': len(self.extracted_items['locations']),
                    'characters_count': len(self.extracted_items['characters']),
                    'monsters_count': len(self.extracted_items['monsters']),
                    'items_count': len(self.extracted_items['items'])
                }
            )
            
            # Логируем локации
            for loc in self.extracted_items['locations']:
                self.logger.log_action(
                    'story_location',
                    session_id=session_id,
                    details={'location': loc['name'], 'context': loc['context'][:200]}
                )
            
            # Логируем персонажей
            for char in self.extracted_items['characters']:
                self.logger.log_action(
                    'story_character',
                    session_id=session_id,
                    details={'character': char['name'], 'context': char['context'][:200]}
                )
            
            # Логируем монстров
            for monster in self.extracted_items['monsters']:
                self.logger.log_action(
                    'story_monster',
                    session_id=session_id,
                    details={'monster': monster['name'], 'context': monster['context'][:200]}
                )
            
            # Логируем предметы
            for item in self.extracted_items['items']:
                self.logger.log_action(
                    'story_item',
                    session_id=session_id,
                    details={'item': item['name'], 'context': item['context'][:200]}
                )
        
        return self.extracted_items
    
    def get_statistics(self) -> Dict[str, int]:
        """Получить статистику выделенных элементов"""
        return {
            'total_locations': len(self.extracted_items['locations']),
            'total_characters': len(self.extracted_items['characters']),
            'total_monsters': len(self.extracted_items['monsters']),
            'total_items': len(self.extracted_items['items']),
            'total_elements': (len(self.extracted_items['locations']) + 
                              len(self.extracted_items['characters']) + 
                              len(self.extracted_items['monsters']) + 
                              len(self.extracted_items['items']))
        }
