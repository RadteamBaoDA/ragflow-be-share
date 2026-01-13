#
#  Copyright 2024 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
"""
Language detection utilities for multi-language support.
Detects English, Japanese, and Vietnamese without external dependencies.
"""


def detect_language(text: str) -> str:
    """
    Detect language of text with support for English, Japanese, and Vietnamese only.
    Uses character-based detection with specific Unicode ranges to avoid false positives.
    
    Args:
        text: Input text to detect language
        
    Returns:
        Language name: "English", "Japanese", "Vietnamese", or None if undetermined
        
    Examples:
        >>> detect_language("What is machine learning?")
        'English'
        >>> detect_language("機械学習とは？")
        'Japanese'
        >>> detect_language("Học máy là gì?")
        'Vietnamese'
    """
    if not text or not text.strip():
        return None
    
    # Count characters by type for confidence scoring
    char_counts = {
        'hiragana': 0,
        'katakana': 0,
        'kanji': 0,  # CJK Unified Ideographs (shared with Chinese, but in context indicates Japanese)
        'vietnamese_unique': 0,  # Truly unique Vietnamese characters
        'vietnamese_common': 0,   # Vietnamese tone marks that might appear in other languages
        'ascii': 0,
        'total': 0
    }
    
    # Tier 1: Absolutely unique to Vietnamese (ă, đ, ơ, ư and their combinations with tones)
    vietnamese_unique = set(
        'ăđơưĂĐƠƯ'  # Unique Vietnamese base letters
        'ặẳẵắằậẩẫấầ'  # ă with tone marks
        'ợởỡớờộổỗốồ'  # ơ, ô with Vietnamese-specific tones
        'ựửữứừ'  # ư with tone marks
        'ẶẲẴẮẰẬẨẪẤẦ'  # Uppercase Ă with tone marks
        'ỢỞỠỚỜỘỔỖỐỒ'  # Uppercase Ơ, Ô with Vietnamese-specific tones
        'ỰỬỮỨỪ'  # Uppercase Ư with tone marks
    )
    
    # Tier 2: Common in Vietnamese but also in French/Spanish (need multiple occurrences)
    vietnamese_common = set(
        'ạảẹẻịỉọỏụủỵỷ'  # Dot below, hook above (lowercase)
        'ẠẢẸẺỊỈỌỎỤỦỴỶ'  # Dot below, hook above (uppercase)
    )
    
    for char in text:
        char_counts['total'] += 1
        
        # Japanese detection (Hiragana, Katakana, and Kanji)
        if '\u3040' <= char <= '\u309F':  # Hiragana
            char_counts['hiragana'] += 1
        elif '\u30A0' <= char <= '\u30FF':  # Katakana
            char_counts['katakana'] += 1
        elif '\u4E00' <= char <= '\u9FFF':  # CJK Unified Ideographs (Kanji/Hanzi)
            char_counts['kanji'] += 1
        
        # Vietnamese character detection (two-tier)
        elif char in vietnamese_unique:
            char_counts['vietnamese_unique'] += 1
        elif char in vietnamese_common:
            char_counts['vietnamese_common'] += 1
        
        # ASCII (English)
        elif ord(char) < 128 and char.isalpha():
            char_counts['ascii'] += 1
    
    # Calculate confidence percentages
    total_chars = char_counts['total']
    if total_chars == 0:
        return None
    
    japanese_kana_ratio = (char_counts['hiragana'] + char_counts['katakana']) / total_chars
    kanji_ratio = char_counts['kanji'] / total_chars
    ascii_ratio = char_counts['ascii'] / total_chars
    
    # Decision logic with thresholds to avoid false positives
    # Japanese: Even a small percentage of hiragana/katakana is highly indicative
    if japanese_kana_ratio > 0.05:  # 5% hiragana/katakana = definitely Japanese
        return "Japanese"
    
    # Pure kanji text: likely Japanese if mostly kanji (though could be Chinese)
    # Since we only support EN/JA/VI, treat high kanji content as Japanese
    if kanji_ratio > 0.5:  # More than 50% kanji characters
        return "Japanese"
    
    # Vietnamese: Two-tier detection to avoid French/Spanish false positives
    # Tier 1: Any truly unique Vietnamese character (ă, đ, ơ, ư) = Vietnamese
    if char_counts['vietnamese_unique'] >= 1:
        return "Vietnamese"
    
    # Tier 2: Multiple common Vietnamese tone marks (but not French/Spanish single accents)
    if char_counts['vietnamese_common'] >= 1:  # Even 1 dot-below/hook-above is fairly specific to Vietnamese
        return "Vietnamese"
    
    # English: Majority ASCII letters
    if ascii_ratio > 0.5:  # 50% ASCII letters
        return "English"
    
    # If can't confidently detect, default to English if any ASCII present
    if char_counts['ascii'] > 0:
        return "English"
    
    return None
