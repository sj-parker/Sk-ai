from config import get

def contains_trigger(text):
    triggers = get('TRIGGERS', {}).get('words', [])
    text = text.lower()
    return any(trigger in text for trigger in triggers)

def is_mention_required(source):
    require = get('TRIGGERS', {}).get('require_mention', {})
    return require.get(source, False) 