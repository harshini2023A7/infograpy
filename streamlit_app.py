from deep_translator import GoogleTranslator
from typing import Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Language code mapping
LANGUAGE_CODES = {
    'Hindi': 'hi',
    'Telugu': 'te', 
    'Tamil': 'ta',
    'Malayalam': 'ml',
    'Bengali': 'bn',
    'English': 'en'
}

# Reverse mapping for language detection
CODE_TO_LANGUAGE = {v: k for k, v in LANGUAGE_CODES.items()}

def get_language_code(language_name: str) -> str:
    """
    Get language code from language name
    
    Args:
        language_name: Full language name (e.g., 'Hindi')
        
    Returns:
        Language code (e.g., 'hi')
    """
    return LANGUAGE_CODES.get(language_name, 'en')

def get_language_name(language_code: str) -> str:
    """
    Get language name from language code
    
    Args:
        language_code: Language code (e.g., 'hi')
        
    Returns:
        Full language name (e.g., 'Hindi')
    """
    return CODE_TO_LANGUAGE.get(language_code, 'English')

def translate_text(text: str, target_language_code: str, source_language_code: str = 'auto') -> str:
    """
    Translate text to target language using Google Translator
    
    Args:
        text: Text to translate
        target_language_code: Target language code (e.g., 'hi' for Hindi)
        source_language_code: Source language code ('auto' for auto-detection)
        
    Returns:
        Translated text
    """
    try:
        # If target is English or same as source, return original
        if target_language_code == 'en' or target_language_code == source_language_code:
            return text
        
        # Initialize translator
        translator = GoogleTranslator(source=source_language_code, target=target_language_code)
        
        # Translate text
        translated = translator.translate(text)
        
        logger.info(f"Translation successful: {source_language_code} -> {target_language_code}")
        return translated if translated else text
        
    except Exception as e:
        logger.error(f"Translation failed: {str(e)}")
        # Return original text if translation fails
        return text

def batch_translate(texts: list, target_language_code: str, source_language_code: str = 'auto') -> list:
    """
    Translate multiple texts to target language
    
    Args:
        texts: List of texts to translate
        target_language_code: Target language code
        source_language_code: Source language code ('auto' for auto-detection)
        
    Returns:
        List of translated texts
    """
    translated_texts = []
    
    for text in texts:
        try:
            translated = translate_text(text, target_language_code, source_language_code)
            translated_texts.append(translated)
        except Exception as e:
            logger.error(f"Batch translation failed for text: {text[:50]}... Error: {str(e)}")
            translated_texts.append(text)  # Keep original if translation fails
    
    return translated_texts

def detect_language(text: str) -> Optional[str]:
    """
    Detect the language of given text
    
    Args:
        text: Text to analyze
        
    Returns:
        Detected language code or None if detection fails
    """
    try:
        from deep_translator import single_detection
        detected_lang = single_detection(text, api_key=None)
        return detected_lang
    except Exception as e:
        logger.error(f"Language detection failed: {str(e)}")
        return None

def is_supported_language(language_code: str) -> bool:
    """
    Check if language is supported by the app
    
    Args:
        language_code: Language code to check
        
    Returns:
        True if supported, False otherwise
    """
    return language_code in CODE_TO_LANGUAGE

def get_supported_languages() -> Dict[str, str]:
    """
    Get all supported languages
    
    Returns:
        Dictionary mapping language names to codes
    """
    return LANGUAGE_CODES.copy()

def validate_translation(original: str, translated: str, target_lang: str) -> bool:
    """
    Basic validation of translation quality
    
    Args:
        original: Original text
        translated: Translated text
        target_lang: Target language code
        
    Returns:
        True if translation seems valid, False otherwise
    """
    # Basic checks
    if not translated or len(translated.strip()) == 0:
        return False
    
    # Check if translation is significantly different from original
    # (unless target is English and original might be English)
    if target_lang != 'en' and original.lower() == translated.lower():
        return False
    
    # Check reasonable length ratio (translated shouldn't be too different in length)
    length_ratio = len(translated) / len(original) if len(original) > 0 else 1
    if length_ratio > 3.0 or length_ratio < 0.3:
        logger.warning(f"Translation length ratio unusual: {length_ratio}")
    
    return True

def transliterate_text(text: str, target_script: str) -> str:
    """
    Transliterate text to different script (basic implementation)
    
    Args:
        text: Text to transliterate
        target_script: Target script ('devanagari', 'bengali', etc.)
        
    Returns:
        Transliterated text (fallback to original if not supported)
    """
    try:
        # This is a placeholder for transliteration
        # You could integrate libraries like 'indic-transliteration' for better results
        logger.info(f"Transliteration requested for script: {target_script}")
        return text  # Return original for now
    except Exception as e:
        logger.error(f"Transliteration failed: {str(e)}")
        return text

def smart_translate(text: str, target_language: str) -> Dict[str, str]:
    """
    Smart translation with detection and validation
    
    Args:
        text: Text to translate
        target_language: Target language name (e.g., 'Hindi')
        
    Returns:
        Dictionary with translation results and metadata
    """
    result = {
        'original': text,
        'translated': text,
        'target_language': target_language,
        'target_code': get_language_code(target_language),
        'detected_source': None,
        'success': False,
        'error': None
    }
    
    try:
        # Detect source language
        detected = detect_language(text)
        result['detected_source'] = detected
        
        # Get target language code
        target_code = get_language_code(target_language)
        
        # Skip translation if target is same as detected source
        if detected and detected == target_code:
            result['translated'] = text
            result['success'] = True
            return result
        
        # Perform translation
        translated = translate_text(text, target_code)
        
        # Validate translation
        if validate_translation(text, translated, target_code):
            result['translated'] = translated
            result['success'] = True
        else:
            result['error'] = 'Translation validation failed'
            result['translated'] = text  # Keep original
            
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"Smart translation failed: {str(e)}")
    
    return result

# Test function
def test_translation():
    """Test translation functionality"""
    test_cases = [
        ("Hello world", "Hindi"),
        ("This is a beautiful day", "Telugu"),
        ("AI is amazing", "Tamil"),
        ("Thank you very much", "Malayalam"),
        ("Good morning", "Bengali")
    ]
    
    print("Testing translation functionality...")
    for text, target_lang in test_cases:
        result = smart_translate(text, target_lang)
        print(f"Original: {result['original']}")
        print(f"Target: {result['target_language']} ({result['target_code']})")
        print(f"Translated: {result['translated']}")
        print(f"Success: {result['success']}")
        if result['error']:
            print(f"Error: {result['error']}")
        print("-" * 50)

Export function__all__ = [
    'translate_text',
    'batch_translate',
    'detect_language',
    'get_language_code',
    'get_language_name',
    'is_supported_language',
    'get_supported_languages',
    'smart_translate',
    'test_translation'
]
