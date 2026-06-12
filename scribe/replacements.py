#replacements.py
import re
import logging

logger = logging.getLogger(__name__)


def load_replacements(settings_manager, lang=None):
    """Loads replacements and flags from settings for the current language.

    Returns: (replacements, replacements_enabled, partial_replacements_enabled, lang).
    """
    replacements_enabled = True
    partial_replacements_enabled = True
    replacements = []
    _lang = lang or 'en'
    if settings_manager:
        settings = settings_manager.all() if hasattr(settings_manager, 'all') else {}
        _lang = settings.get('language', _lang)
        replacements_enabled = settings.get('enable_replacements', True)
        partial_replacements_enabled = settings.get('enable_partial_replacements', True)
        replacements = settings.get('replaces', {}).get(_lang, [])
    return replacements, replacements_enabled, partial_replacements_enabled, _lang



def parse_replace_string(replace):
    """Parses the replace string into a list of actions: plain text and special commands in [square brackets].

    Returns a list: [{'type': 'text', 'value': ...}, {'type': 'key', 'value': ...}, ...]
    Example: 'abc[Backspace][Enter]d' -> [text 'abc', key 'Backspace', key 'Enter', text 'd']
    Only allowed special commands: Space, Backspace, Tab, Enter
    Others are ignored.
    """
    allowed_keys = {'Space', 'Backspace', 'Tab', 'Enter'}
    actions = []
    # New pattern: special command in square brackets, does NOT capture punctuation after the bracket
    # Example: '[Backspace].' -> key: Backspace, text: '.'
    pattern = re.compile(r'\[(.*?)\]')
    pos = 0
    for m in pattern.finditer(replace):
        if m.start() > pos:
            # Plain text between commands
            actions.append({'type': 'text', 'value': replace[pos:m.start()]})
        cmd = m.group(1).strip()
        if cmd in allowed_keys:
            actions.append({'type': 'key', 'value': cmd})
        pos = m.end()
    if pos < len(replace):
        actions.append({'type': 'text', 'value': replace[pos:]})
    # Additionally: split text fragments if they start with punctuation after a special command
    # Example: [{'type': 'key', ...}, {'type': 'text', 'value': '. '}] -> key, text '.', text ' '
    final_actions = []
    for act in actions:
        if act['type'] == 'text' and act['value']:
            # Split into groups: punctuation + the rest of the text
            parts = re.findall(r'[^\w\s]+|[\w\s]+', act['value'])
            for part in parts:
                if part:
                    final_actions.append({'type': 'text', 'value': part})
        else:
            final_actions.append(act)
    return final_actions



def get_word_declensions_pattern(word):
    """Generates a regular expression pattern matching standard declension endings for a Russian/Ukrainian noun."""
    if not word or not word.isalpha():
        return re.escape(word)
    
    w = word.lower()
    
    if w.endswith('а'):
        stem = w[:-1]
        pat = re.escape(stem) + r"(?:[аыиеуойамиахяівь]|ою|ої|ій|ям|ями|ях)?"
    elif w.endswith('я'):
        stem = w[:-1]
        pat = re.escape(stem) + r"(?:[яиіеюеямхяівь]|ею|ям|ями|ях)?"
    elif w.endswith('ь'):
        stem = w[:-1]
        pat = re.escape(stem) + r"(?:[ьяиюемхяів]|ей|ям|ями|ях)?"
    elif w.endswith('о'):
        stem = w[:-1]
        pat = re.escape(stem) + r"(?:[оаумеиамхяів]|ом|ов|ам|ами|ах)?"
    elif w.endswith('е'):
        stem = w[:-1]
        pat = re.escape(stem) + r"(?:[еяуимхяів]|ем|ей|ям|ями|ях)?"
    else:
        # Consonant ending (masculine)
        consonants = "бвгджзклмнпрстфхцчшщ"
        if w[-1] in consonants:
            pat = re.escape(w) + r"(?:[аыиуе]|ов|ів|ам|ами|ах|ом|ові)?"
        else:
            pat = re.escape(w)
    return pat


def get_wildcard_word_pattern(word):
    """Generates a regex pattern for a word containing '*' wildcards.

    Splits the word by '*' and joins parts using [^\W\d_]* which matches any letters.
    """
    parts = word.split('*')
    escaped_parts = [re.escape(p) for p in parts]
    return r"[^\W\d_]*".join(escaped_parts)


def apply_replacements_actions(text, replacements):
    """Applies replacements to the text and returns a list of actions (text/key) for the entire result.

    Supports phrase replacements (multiple consecutive words).
    Each replacement is parsed into actions via parse_replace_string.
    Supports comma-separated alternative phrases and wildcard '*' stem matching.
    """
    # Expand replacements with comma-separated variants in 'find'
    expanded_replacements = []
    for item in replacements:
        find = item.get('find', '')
        if not find:
            continue
        # Split by comma
        variants = [v.strip() for v in find.split(',') if v.strip()]
        for var in variants:
            expanded_replacements.append({
                'find': var,
                'replace': item.get('replace', ''),
                'original_item': item
            })

    # Sort replacements by descending length of 'find' (so longer phrases are replaced first)
    sorted_replacements = sorted(
        expanded_replacements,
        key=lambda x: len(x['find']), reverse=True
    )
    # Prepare pattern for searching all phrases
    patterns = []
    for item in sorted_replacements:
        find = item['find']
        words = find.split()
        if not words:
            continue
        
        word_patterns = []
        for w in words:
            if '*' in w:
                word_patterns.append(get_wildcard_word_pattern(w))
            else:
                word_patterns.append(get_word_declensions_pattern(w))
        pattern_str = r'\s+'.join(word_patterns)
        
        # Determine word boundaries:
        # Use start boundary \b if first word starts with alphanumeric char and isn't a wildcard
        start_boundary = r'\b' if (words[0][0].isalnum() and words[0][0] != '*') else ''
        # Use end boundary \b if last word ends with alphanumeric char or wildcard
        end_boundary = r'\b' if (words[-1][-1].isalnum() or words[-1][-1] == '*') else ''
        
        pat = re.compile(start_boundary + pattern_str + end_boundary, re.IGNORECASE)
        patterns.append((item, pat))
    # Main loop: search and replace all phrases
    pos = 0
    actions = []
    text_len = len(text)
    while pos < text_len:
        match = None
        matched_item = None
        for item, pat in patterns:
            m = pat.match(text, pos)
            if m:
                if (not match) or (m.end() - m.start() > match.end() - match.start()):
                    match = m
                    matched_item = item
        if match:
            # Add replacement (parse special commands)
            replace = matched_item.get('replace', '')
            logger.info(f"[REPLACE] Find: {match.group(0)} | Replace: {replace}")
            actions.extend(parse_replace_string(replace))
            pos = match.end()
        else:
            # No match — add current character as text
            actions.append({'type': 'text', 'value': text[pos]})
            pos += 1
    # Merge consecutive text actions
    final_actions = []
    for act in actions:
        if final_actions and act['type'] == 'text' and final_actions[-1]['type'] == 'text':
            final_actions[-1]['value'] += act['value']
        else:
            final_actions.append(act)
    return final_actions

# For backward compatibility: the old function returns a string
def apply_replacements(text, replacements):
    """Applies replacements to the text only by individual words (word boundaries).

    Returns the final text (with special commands as text).
    """
    actions = apply_replacements_actions(text, replacements)
    # Merge all actions back into a string (special commands as [Key])
    out = ''
    for act in actions:
        if act['type'] == 'text':
            out += act['value']
        elif act['type'] == 'key':
            out += f'[{act["value"]}]'
    return out


def parse_import_file(filepath):
    """Parses an external dictionary file.
    Supports JSON, AHK Hotstrings, OpenOffice/LibreOffice Autocorrect XML, TSV, CSV, or custom text lists.
    Returns: a list of dicts [{"find": "...", "replace": "..."}]
    """
    import json
    results = []
    
    # Try reading as JSON first
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        if content.startswith('{') or content.startswith('['):
            data = json.loads(content)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "find" in item and "replace" in item:
                        results.append({"find": str(item["find"]), "replace": str(item["replace"])})
            elif isinstance(data, dict):
                first_val = next(iter(data.values())) if data else None
                if isinstance(first_val, list):
                    # Nested by language
                    for lang, items in data.items():
                        if isinstance(items, list):
                            for item in items:
                                if isinstance(item, dict) and "find" in item and "replace" in item:
                                    results.append({"find": str(item["find"]), "replace": str(item["replace"])})
                elif isinstance(first_val, dict):
                    # Nested dict by language
                    for lang, dict_data in data.items():
                        if isinstance(dict_data, dict):
                            for k, v in dict_data.items():
                                results.append({"find": str(k), "replace": str(v)})
                else:
                    # Simple dict {"find": "replace"}
                    for k, v in data.items():
                        results.append({"find": str(k), "replace": str(v)})
            if results:
                return results
    except Exception:
        pass

    # Read line-by-line
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception:
        try:
            with open(filepath, 'r', encoding='ansi') as f:
                lines = f.readlines()
        except Exception:
            return []

    ahk_regex = re.compile(r'^:.*?:([^:]+)::(.*)$')
    # OpenOffice XML regex
    oo_regex = re.compile(r'block-list:abbreviation="([^"]+)"\s+block-list:name="([^"]+)"')
    oo_regex_rev = re.compile(r'block-list:name="([^"]+)"\s+block-list:abbreviation="([^"]+)"')

    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
            
        # 1. XML check
        m_oo = oo_regex.search(line_str)
        if m_oo:
            results.append({"find": m_oo.group(1), "replace": m_oo.group(2)})
            continue
        m_oo_rev = oo_regex_rev.search(line_str)
        if m_oo_rev:
            results.append({"find": m_oo_rev.group(2), "replace": m_oo_rev.group(1)})
            continue
            
        # 2. AHK check
        if line_str.startswith(';'):
            continue
        comment_split = line_str.split(' ;', 1)
        line_clean = comment_split[0].strip()
        
        m_ahk = ahk_regex.match(line_clean)
        if m_ahk:
            results.append({"find": m_ahk.group(1).strip(), "replace": m_ahk.group(2).strip()})
            continue
            
        # 3. CSV/Delimiter check
        delimiters = ['\t', ';', '=']
        split_success = False
        for delim in delimiters:
            parts = line_clean.split(delim)
            if len(parts) >= 2:
                find_part = parts[0].strip()
                replace_part = delim.join(parts[1:]).strip()
                if find_part and replace_part:
                    results.append({"find": find_part, "replace": replace_part})
                    split_success = True
                    break
        if split_success:
            continue
            
        # Comma check
        parts = line_clean.split(',')
        if len(parts) >= 2:
            find_part = parts[0].strip()
            replace_part = ','.join(parts[1:]).strip()
            if find_part and replace_part:
                results.append({"find": find_part, "replace": replace_part})
                
    return results
