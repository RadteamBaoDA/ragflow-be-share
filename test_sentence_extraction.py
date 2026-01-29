"""
Test script to verify extract_first_sentence_for_detection functionality
"""
from api.utils.language_utils import extract_first_sentence_for_detection, detect_language


def test_sentence_extraction():
    """Test various scenarios for sentence extraction"""
    
    test_cases = [
        {
            "input": "What is 'machine learning'? This is second sentence.",
            "description": "English with quoted text",
        },
        {
            "input": "Explain NDA concept. More details here.",
            "description": "English with acronym",
        },
        {
            "input": "機械学習とは何ですか？次の文。",
            "description": "Japanese question",
        },
        {
            "input": "Học máy là gì? Đây là câu thứ hai.",
            "description": "Vietnamese question",
        },
        {
            "input": "Tell me about NASA and 'space exploration'\nSecond line here",
            "description": "Multiple features: acronym, quotes, newline",
        },
        {
            "input": "This is a very long question that exceeds the fifty character limit and should be truncated at exactly fifty characters regardless of content",
            "description": "Long text exceeding 50 chars",
        },
        {
            "input": "「日本語」の「引用符」を使う文章です。",
            "description": "Japanese with CJK quotes",
        },
        {
            "input": "What is API, REST, and HTTP protocol?",
            "description": "Multiple acronyms",
        }
    ]
    
    print("=" * 80)
    print("Testing extract_first_sentence_for_detection()")
    print("=" * 80)
    
    for i, test in enumerate(test_cases, 1):
        input_text = test["input"]
        extracted = extract_first_sentence_for_detection(input_text)
        original_lang = detect_language(input_text)
        extracted_lang = detect_language(extracted if extracted else input_text)
        
        print(f"\n{i}. {test['description']}")
        print(f"   Input:     {input_text[:70]}{'...' if len(input_text) > 70 else ''}")
        print(f"   Extracted: {extracted}")
        print(f"   Original detection:  {original_lang}")
        print(f"   Improved detection:  {extracted_lang}")
        print(f"   Match: {'✓' if original_lang == extracted_lang else '⚠ Different'}")


if __name__ == "__main__":
    test_sentence_extraction()
