#!/usr/bin/env python3
"""
Test script to demonstrate language detection improvements.
Shows that the new implementation avoids false positives.
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.utils.language_utils import detect_language


if __name__ == "__main__":
    test_cases = [
        # English
        ("What is machine learning?", "English"),
        ("How does RAG work?", "English"),
        
        # Japanese - Basic (Original 3 tests)
        ("機械学習とは何ですか？", "Japanese"),
        ("こんにちは、元気ですか？", "Japanese"),
        ("カタカナのテスト", "Japanese"),
        
        # Japanese - Pure Hiragana (5 cases)
        ("ありがとうございます", "Japanese"),  # Thank you very much
        ("おはようございます", "Japanese"),  # Good morning
        ("すみません、わかりません", "Japanese"),  # Sorry, I don't understand
        ("これはなんですか", "Japanese"),  # What is this?
        ("いってきます", "Japanese"),  # I'm leaving
        
        # Japanese - Pure Katakana (3 cases)
        ("コンピュータ", "Japanese"),  # Computer
        ("プログラミング", "Japanese"),  # Programming
        ("データベース", "Japanese"),  # Database
        
        # Japanese - Pure Kanji (2 cases)
        ("日本語", "Japanese"),  # Japanese language
        ("人工知能", "Japanese"),  # Artificial Intelligence
        
        # Japanese - Hiragana + Kanji (5 cases)
        ("今日は良い天気ですね", "Japanese"),  # Today is nice weather
        ("私は学生です", "Japanese"),  # I am a student
        ("日本に行きたいです", "Japanese"),  # I want to go to Japan
        ("この本を読みました", "Japanese"),  # I read this book
        ("明日会社に行きます", "Japanese"),  # I will go to the company tomorrow
        
        # Japanese - Katakana + Kanji (2 cases)
        ("東京タワー", "Japanese"),  # Tokyo Tower
        ("新宿駅のカフェ", "Japanese"),  # Cafe at Shinjuku Station
        
        # Japanese - All Three Scripts Mixed (3 cases)
        ("私はコーヒーを飲みます", "Japanese"),  # I drink coffee (hiragana+kanji+katakana)
        ("日本のアニメが好きです", "Japanese"),  # I like Japanese anime
        ("データサイエンスを勉強しています", "Japanese"),  # I'm studying data science
        
        # Vietnamese
        ("Xin chào, bạn khỏe không?", "Vietnamese"),
        ("Học máy là gì?", "Vietnamese"),
        ("Tiếng Việt có dấu đặc biệt như ă, â, ơ, ư", "Vietnamese"),
        
        # Should NOT detect as Vietnamese (French)
        ("Bonjour, comment ça va?", "English"),  # French should be English (no Vietnamese chars)
        ("Le château est très beau", "English"),  # French with accents
        
        # Should NOT detect as Vietnamese (Spanish)
        ("¿Cómo estás? Mañana es lunes", "English"),  # Spanish
        ("El niño come comida española", "English"),  # Spanish with ñ
        
        # Should NOT detect as Vietnamese (German)
        ("Guten Tag, wie geht es Ihnen?", "English"),  # German
        ("Das Mädchen ist schön", "English"),  # German with ä, ö, ü
    ]
    
    print("Language Detection Test Results")
    print("=" * 70)
    
    all_passed = True
    for text, expected in test_cases:
        detected = detect_language(text)
        status = "✓ PASS" if detected == expected else "✗ FAIL"
        
        if detected != expected:
            all_passed = False
        
        print(f"{status} | Expected: {expected:10s} | Detected: {str(detected):10s}")
        print(f"       Text: {text[:60]}")
        print()
    
    print("=" * 70)
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
