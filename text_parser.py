import re
from typing import Dict, Optional

class TextParser:
    def __init__(self):
        self.numbers_ua = {
            'нуль': 0, 'нульовий': 0,
            'один': 1, 'одна': 1, 'перший': 1, 'перша': 1,
            'два': 2, 'дві': 2, 'другий': 2, 'друга': 2,
            'три': 3, 'третій': 3, 'третя': 3,
            'чотири': 4, 'четвертий': 4, 'четверта': 4,
            'п\'ять': 5, 'пять': 5, 'п\'ятий': 5, 'пятий': 5,
            'шість': 6, 'шостий': 6,
            'сім': 7, 'сьомий': 7,
            'вісім': 8, 'восьмий': 8,
            'дев\'ять': 9, 'девять': 9, 'дев\'ятий': 9, 'девятий': 9,
            'десять': 10, 'десятий': 10,
            'одинадцять': 11, 'одинадцятий': 11,
            'дванадцять': 12, 'дванадцятий': 12,
            'тринадцять': 13, 'тринадцятий': 13,
            'чотирнадцять': 14, 'чотирнадцятий': 14,
            'п\'ятнадцять': 15, 'пятнадцять': 15, 'п\'ятнадцятий': 15,
            'шістнадцять': 16, 'шістнадцятий': 16,
            'сімнадцять': 17, 'сімнадцятий': 17,
            'вісімнадцять': 18, 'вісімнадцятий': 18,
            'дев\'ятнадцять': 19, 'девятнадцять': 19,
            'двадцять': 20, 'двадцятий': 20,
            'тридцять': 30, 'тридцятий': 30,
            'сорок': 40, 'сороковий': 40,
            'п\'ятдесят': 50, 'пятдесят': 50, 'п\'ятдесятий': 50,
            'шістдесят': 60, 'шістдесятий': 60,
            'сімдесят': 70, 'сімдесятий': 70,
            'вісімдесят': 80, 'вісімдесятий': 80,
            'дев\'яносто': 90, 'девяносто': 90,
            'сто': 100, 'сотий': 100
        }

        self.weight_synonyms = ['кг', 'кіло', 'кілограм', 'килограм', 'kg']
        self.reps_synonyms = ['раз', 'разів', 'повторень', 'повторення']
        self.set_synonyms = ['підхід', 'сета', 'сет', 'set']
        
        self.prefix_words = ['зробив', 'зробила', 'виконав', 'виконала']

    def convert_ua_number_to_int(self, text: str) -> Optional[int]:
        text = text.lower().strip().replace("’", "'")
        if text.isdigit():
            return int(text)

        words = text.split()
        total = 0
        for word in words:
            word = word.strip()
            if word in self.numbers_ua:
                total += self.numbers_ua[word]
            elif word.isdigit():
                total += int(word)

        return total if total > 0 else None

    def parse_exercise_input(self, text: str) -> Optional[Dict[str, any]]:
        text = text.lower().strip().replace("’", "'")

        words = text.split()
        if words and words[0] in self.prefix_words:
            text = ' '.join(words[1:])

        result = {
            'exercise': None,
            'reps': None,
            'weight': None,
            'set_number': None
        }

        exercise_match = re.match(r'^([а-яіїєґ\s\-]+?)(?:,|\s+\d|\s+[а-яіїєґ\-]+\s(?:раз|повторень|підхід|сет|кг))', text)
        if exercise_match:
            result['exercise'] = exercise_match.group(1).strip()
        else:
            words = text.split(',')  
            if words:
                result['exercise'] = words[0].strip()

        search_from = 0  

       
        reps_pattern = r'([\d\.,]+|\w+(?:\s\w+)*)\s*(?:' + '|'.join(self.reps_synonyms) + r')'
        reps_match = re.search(reps_pattern, text)
        if reps_match:
            reps_raw = reps_match.group(1).strip()
            reps = self.convert_ua_number_to_int(reps_raw)
            if reps is not None:
                result['reps'] = reps
                search_from = max(search_from, reps_match.end())

       
        set_pattern = r'([\d\.,]+|\w+(?:\s\w+)*)\s*(?:' + '|'.join(self.set_synonyms) + r')'
        set_match = re.search(set_pattern, text[search_from:])
        if set_match:
            set_raw = set_match.group(1).strip()
            set_num = self.convert_ua_number_to_int(set_raw)
            if set_num is not None:
                result['set_number'] = set_num
                search_from += set_match.end()

       
        weight_pattern = r'([\d\.,]+|\w+(?:\s\w+)*)\s*(?:' + '|'.join(self.weight_synonyms) + r')'
        weight_match = re.search(weight_pattern, text[search_from:])
        if weight_match:
            weight_raw = weight_match.group(1).strip().replace(',', '.')
            try:
                result['weight'] = float(weight_raw)
            except ValueError:
                weight = self.convert_ua_number_to_int(weight_raw)
                if weight is not None:
                    result['weight'] = float(weight)

        
        if result['exercise']:
            result['exercise'] = result['exercise'].strip().lower().rstrip(",. ")

        if result['exercise'] and result['reps'] is not None:
            return result


        
        if result['exercise']:
            result['exercise'] = result['exercise'].strip().lower().rstrip(",. ")

        
        if result['exercise'] and result['reps'] is not None:
            return result

        return None
