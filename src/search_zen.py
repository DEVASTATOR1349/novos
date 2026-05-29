#!/usr/bin/env python3
"""
Поиск строящихся новостроек через ZenSerp API
"""
import os
import json
import time
import requests
from urllib.parse import quote

ZENSERP_BASE = "https://app.zenserp.com/api/v2/search"
API_KEY = os.getenv("ZENSERP_API_KEY", "")

def search(query, num=10, page=1):
    """Поиск через ZenSerp"""
    params = {
        "q": query,
        "apikey": API_KEY,
        "num": min(num, 10),
        "start": (page - 1) * 10,
        "source": "web",
        "gl": "RU",
        "hl": "ru",
        "location": "Russia"
    }
    
    resp = requests.get(ZENSERP_BASE, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def parse_results(data):
    """Извлечь органические результаты"""
    results = []
    for item in data.get("organic", []):
        title = item.get("title", "")
        url = item.get("url", "")
        snippet = item.get("snippet", "")
        
        # Фильтр: нас интересуют только ЖК и новостройки
        skip_words = ["банк", "страхование", "отзывы", "ипотека", "ремонт"]
        if any(w in title.lower() for w in skip_words):
            continue
            
        results.append({
            "title": title,
            "url": url,
            "snippet": snippet,
            "source": "zenserp"
        })
    return results


def search_new_buildings(city, queries=None):
    """Искать строящиеся новостройки по городу"""
    if queries is None:
        queries = [
            f"строящиеся новостройки {city} купить квартиру",
            f"новостройки {city} строящиеся ЖК 2026 2027",
            f"ЖК {city} новостройки застройщик цены",
        ]
    
    all_results = []
    seen_urls = set()
    
    for q in queries:
        try:
            data = search(q, num=10)
            results = parse_results(data)
            
            for r in results:
                domain = r["url"].split("/")[2] if "//" in r["url"] else r["url"]
                if domain not in seen_urls:
                    seen_urls.add(domain)
                    all_results.append(r)
            
            print(f"  Запрос '{q}': {len(results)} результатов")
            time.sleep(1.5)  # rate limit
        except Exception as e:
            print(f"  Ошибка запроса '{q}': {e}")
    
    return all_results


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    API_KEY = os.getenv("ZENSERP_API_KEY", "")
    
    print("=== Тест поиска: Ставрополь ===")
    results = search_new_buildings("Ставрополь")
    print(f"\nНайдено уникальных: {len(results)}")
    for r in results[:5]:
        print(f"  • {r['title']}")
        print(f"    {r['url']}")
