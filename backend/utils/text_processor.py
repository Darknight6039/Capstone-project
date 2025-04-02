import re
import string

def preprocess_text(text):
    """
    Preprocess resume text to make it more suitable for analysis
    Parameters:
    - text: Raw text extracted from resume
    Returns:
    - Preprocessed text
    """
    # Replace multiple newlines with a single newline
    text = re.sub(r'\n+', '\n', text)
    
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Handle bullet points and special characters
    text = text.replace('•', '\n- ')
    text = text.replace('●', '\n- ')
    text = text.replace('○', '\n- ')
    text = text.replace('■', '\n- ')
    
    # Fix common encoding issues
    text = text.replace('â€™', "'")
    text = text.replace('â€"', '-')
    text = text.replace('â€œ', '"')
    text = text.replace('â€', '"')
    
    # Handle section dividers
    text = re.sub(r'[-_=]{3,}', '\n', text)
    
    # Clean up any remaining issues
    text = text.strip()
    
    return text

def extract_keywords(text, keywords_list):
    """
    Extract keywords from text based on a predefined list
    Parameters:
    - text: Text to search for keywords
    - keywords_list: List of keywords to search for
    Returns:
    - List of found keywords
    """
    found_keywords = []
    
    # Convert text to lowercase for case-insensitive matching
    text_lower = text.lower()
    
    for keyword in keywords_list:
        # Create a regex pattern with word boundaries
        pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found_keywords.append(keyword)
            
    return found_keywords

def normalize_job_title(title):
    """
    Normalize job titles for better matching
    Parameters:
    - title: Job title to normalize
    Returns:
    - Normalized job title
    """
    # Convert to lowercase
    title = title.lower()
    
    # Replace specific terms with standardized versions
    replacements = {
        'sr.': 'senior',
        'jr.': 'junior',
        'dev': 'developer',
        'eng': 'engineer',
        'mgr': 'manager',
        'mgmt': 'management',
        'coord': 'coordinator',
        'admin': 'administrator'
    }
    
    for old, new in replacements.items():
        # Replace with word boundaries
        title = re.sub(r'\b' + re.escape(old) + r'\b', new, title)
        
    return title.strip()
