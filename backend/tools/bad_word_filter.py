import json
import os
import re


def load_bad_words():
    """
    Load bad words from the JSON file.
    
    Returns:
        list: List of bad words
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, 'bad_words.json')
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data.get('bad_words', [])


def contains_bad_word(input_string):
    """
    Check if the input string contains any bad words.
    
    Args:
        input_string (str): The string to check for bad words
    
    Returns:
        bool: True if a bad word is found, False otherwise
    """
    if not input_string:
        return False
    
    # Convert input to lowercase for case-insensitive matching
    input_lower = input_string.lower()
    
    # Load bad words
    bad_words = load_bad_words()
    
    # Check each bad word
    for bad_word in bad_words:
        # Use word boundaries to match whole words only
        pattern = r'\b' + re.escape(bad_word.lower()) + r'\b'
        if re.search(pattern, input_lower):
            return True
    
    return False


# Optional: Function to get which bad words were found
def find_bad_words(input_string):
    """
    Find all bad words in the input string.
    
    Args:
        input_string (str): The string to check for bad words
    
    Returns:
        list: List of bad words found in the input string
    """
    if not input_string:
        return []
    
    # Convert input to lowercase for case-insensitive matching
    input_lower = input_string.lower()
    
    # Load bad words
    bad_words = load_bad_words()
    
    found_words = []
    
    # Check each bad word
    for bad_word in bad_words:
        # Use word boundaries to match whole words only
        pattern = r'\b' + re.escape(bad_word.lower()) + r'\b'
        if re.search(pattern, input_lower):
            found_words.append(bad_word)
    
    return found_words
