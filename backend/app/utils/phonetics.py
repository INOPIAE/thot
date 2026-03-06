"""
Phonetic utilities for keyword search
"""

from typing import Tuple, Optional


def cologne_phonetic(text: str) -> str:
    """
    Implementation of Cologne Phonetic algorithm
    
    Args:
        text: The text to encode
        
    Returns:
        Phonetic code string
    """
    if not text:
        return ""
    
    text = text.upper()
    
    # Mapping rules
    replacements = [
        # Before vowels
        (['C'], ['8'], lambda i, txt: i + 1 < len(txt) and txt[i + 1] in 'AHKLOQRUX'),
        # Standard replacements
        (['A', 'E', 'I', 'J', 'O', 'U', 'Y'], ['0'], None),
        (['B'], ['1'], None),
        (['P'], ['3'], lambda i, txt: i + 1 < len(txt) and txt[i + 1] != 'H'),
        (['D', 'T'], ['2'], lambda i, txt: i + 1 < len(txt) and txt[i + 1] not in 'CSZ'),
        (['F', 'V', 'W'], ['3'], None),
        (['P'], ['3'], None),
        (['G', 'K', 'Q'], ['4'], None),
        (['C'], ['4'], lambda i, txt: i == 0 or txt[i - 1] not in 'SZ'),
        (['X'], ['48'], None),
        (['L'], ['5'], None),
        (['M', 'N'], ['6'], None),
        (['R'], ['7'], None),
        (['S', 'Z'], ['8'], None),
    ]
    
    # Simple implementation
    result = []
    for char in text:
        if char == 'Ä': 
            result.append('0')
        elif char == 'Ö' or char == 'Ü':
            result.append('0')
        elif char in 'AEIOUJY':
            result.append('0')
        elif char == 'B':
            result.append('1')
        elif char in 'DT':
            result.append('2')
        elif char in 'FVWP':
            result.append('3')
        elif char in 'GKQ':
            result.append('4')
        elif char == 'C':
            result.append('4')
        elif char == 'X':
            result.append('48')
        elif char == 'L':
            result.append('5')
        elif char in 'MN':
            result.append('6')
        elif char == 'R':
            result.append('7')
        elif char in 'SZ':
            result.append('8')
    
    code = ''.join(result)
    
    # Remove consecutive duplicates
    if code:
        cleaned = [code[0]]
        for c in code[1:]:
            if c != cleaned[-1]:
                cleaned.append(c)
        code = ''.join(cleaned)
    
    # Remove leading zeros
    code = code.lstrip('0')
    
    return code if code else '0'


def double_metaphone(text: str) -> Tuple[str, str]:
    """
    Simplified implementation of Double Metaphone algorithm
    
    Args:
        text: The text to encode
        
    Returns:
        Tuple of (primary, secondary) codes
    """
    if not text:
        return "", ""
    
    text = text.upper()
    primary = []
    secondary = []
    
    i = 0
    while i < len(text):
        char = text[i]
        
        if char in 'AEIOU':
            if i == 0:
                primary.append('A')
                secondary.append('A')
            i += 1
        elif char == 'B':
            primary.append('P')
            secondary.append('P')
            if i + 1 < len(text) and text[i + 1] == 'B':
                i += 2
            else:
                i += 1
        elif char == 'C':
            if i + 1 < len(text) and text[i + 1] == 'H':
                primary.append('X')
                secondary.append('X')
                i += 2
            else:
                primary.append('K')
                secondary.append('K')
                i += 1
        elif char == 'D':
            primary.append('T')
            secondary.append('T')
            i += 1
        elif char == 'F':
            primary.append('F')
            secondary.append('F')
            i += 1
        elif char == 'G':
            primary.append('K')
            secondary.append('K')
            i += 1
        elif char == 'H':
            if i == 0 or text[i - 1] not in 'AEIOU':
                primary.append('H')
                secondary.append('H')
            i += 1
        elif char == 'J':
            primary.append('J')
            secondary.append('J')
            i += 1
        elif char == 'K':
            primary.append('K')
            secondary.append('K')
            i += 1
        elif char == 'L':
            primary.append('L')
            secondary.append('L')
            i += 1
        elif char == 'M':
            primary.append('M')
            secondary.append('M')
            i += 1
        elif char == 'N':
            primary.append('N')
            secondary.append('N')
            i += 1
        elif char == 'P':
            if i + 1 < len(text) and text[i + 1] == 'H':
                primary.append('F')
                secondary.append('F')
                i += 2
            else:
                primary.append('P')
                secondary.append('P')
                i += 1
        elif char == 'Q':
            primary.append('K')
            secondary.append('K')
            i += 1
        elif char == 'R':
            primary.append('R')
            secondary.append('R')
            i += 1
        elif char == 'S':
            if i + 1 < len(text) and text[i + 1] == 'H':
                primary.append('X')
                secondary.append('X')
                i += 2
            else:
                primary.append('S')
                secondary.append('S')
                i += 1
        elif char == 'T':
            if i + 1 < len(text) and text[i + 1] == 'H':
                primary.append('0')
                secondary.append('0')
                i += 2
            else:
                primary.append('T')
                secondary.append('T')
                i += 1
        elif char == 'V':
            primary.append('F')
            secondary.append('F')
            i += 1
        elif char == 'W':
            primary.append('W')
            secondary.append('W')
            i += 1
        elif char == 'X':
            primary.append('KS')
            secondary.append('KS')
            i += 1
        elif char == 'Y':
            primary.append('Y')
            secondary.append('Y')
            i += 1
        elif char == 'Z':
            primary.append('S')
            secondary.append('S')
            i += 1
        else:
            i += 1
    
    primary_str = ''.join(primary)[:4]  # Max 4 characters
    secondary_str = ''.join(secondary)[:4]
    
    return primary_str, secondary_str


def generate_phonetic_codes(text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Generate phonetic search codes for a given text
    
    Args:
        text: The text to generate codes for
        
    Returns:
        Tuple of (c_search, dblmeta_1, dblmeta_2)
    """
    if not text or not text.strip():
        return None, None, None
    
    text = text.strip()
    
    try:
        c_search = cologne_phonetic(text)
        c_search = c_search if c_search else None
    except Exception:
        c_search = None
    
    try:
        dblmeta_1, dblmeta_2 = double_metaphone(text)
        dblmeta_1 = dblmeta_1 if dblmeta_1 else None
        dblmeta_2 = dblmeta_2 if dblmeta_2 else None
    except Exception:
        dblmeta_1 = None
        dblmeta_2 = None
    
    return c_search, dblmeta_1, dblmeta_2
