import re

def is_tiktok_url(url: str) -> bool:
    pattern = r'(https?://)?(www\.)?(tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com)/.*'
    return bool(re.match(pattern, url))
