#!/usr/bin/env python3
"""
Поиск и сбор данных по новостройкам через ZenSerp + парсинг агрегаторов
"""
import os
import re
import json
import time
import requests
from urllib.parse import urlparse, parse_qs, quote
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("ZENSERP_API_KEY", "")
ZENSERP_BASE = "https://app.zenserp.com/api/v2/search"

# Города КМВ для поиска
KMV_CITIES = [
    "Пятигорск",
    "Кисловодск",
    "Ессентуки",
    "Железноводск",
    "Минеральные Воды",
    "Лермонтов",
    "Георгиевск",
]

# Уже известные ЖК в Ставрополе (из таблицы)
KNOWN_STAVROPOL = [
    "Первый", "Кварталы 17/77", "Софи", "Фруктовый Сад",
    "Гармония", "АКСИС ПАТРИОТ", "Северный", "Крокус",
    "Крокус 2", "Суворов", "Красный металлист", "Дыхание",
    "Мельница", "Европейский-5", "КРЫЛЬЯ", "Южный Квартал",
    "Надежда", "Дубровский", "НАСТОЯЩИЙ", "Федерация",
    "Небо", "Комсомольская 26", "Суворов Парк", "Гагарин", "Основа"
]


def zenserp_search(query, num=10, page=1, location="Russia"):
    """Поиск через ZenSerp"""
    params = {
        "q": query,
        "apikey": API_KEY,
        "num": min(num, 10),
        "start": (page - 1) * 10,
        "gl": "RU",
        "hl": "ru",
        "location": location
    }
    try:
        resp = requests.get(ZENSERP_BASE, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  ❌ Ошибка ZenSerp: {e}")
        return {}


def extract_complexes(data, known_names=None):
    """
    Из результатов поиска извлечь названия ЖК
    Ищем в заголовках и сниппетах ссылки на конкретные ЖК
    """
    complexes = set()
    if known_names is None:
        known_names = []

    organic = data.get("organic", [])
    for item in organic:
        title = item.get("title", "")
        url = item.get("url", "")
        snippet = item.get("snippet", "")

        full_text = f"{title} {snippet}"

        # Ищем паттерны ЖК "Название"
        patterns = [
            r'ЖК[«"\s]+([А-Яа-яA-Za-z0-9\-\s]{2,40}?)[»"\s]',
            r'[Жж]илой комплекс[«"\s]+([А-Яа-яA-Za-z0-9\-\s]{2,40}?)[»"\s]',
            r'«([А-Яа-яA-Za-z0-9\-\s]{3,40})»\s*(?:,|\.|\s*(?:ЖК|жк))',
            r'([А-Я][а-я]+)\s*—\s*новостройка',
            r'квартиры\s+в\s+([А-Яа-яA-Za-z0-9\-\s]{3,30}?)\s+от\s+\d',
        ]
        for p in patterns:
            matches = re.findall(p, full_text)
            for m in matches:
                m = m.strip()
                # Исключаем слишком общие слова
                skip = ["Ставрополь", "Пятигорск", "Кисловодск", "Москва", "продаже",
                        "строящемся", "новостройке", "онлайн", "квартиру", "каталог",
                        "новостройки", "застройщика"]
                if len(m) > 2 and m not in skip and m not in known_names:
                    # Проверка что это похоже на название ЖК, а не мусор
                    if any(c.isupper() for c in m) or all(c in "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ" for c in m.replace(" ", "")):
                        complexes.add(m)

    return list(complexes)


def search_city_new_buildings(city):
    """Искать новостройки по городу"""
    print(f"\n🔍 {city}...")

    queries = [
        f"новостройки {city} строящиеся ЖК каталог",
        f"{city} строящиеся жилые комплексы застройщики",
        f"купить квартиру новостройка {city} от застройщика",
        f"Жилой комплекс {city} строящийся",
        f"новостройки {city} 2026 2027",
        f"застройщики {city} новостройки список",
    ]

    all_results = []
    seen_urls = set()
    found_complexes = set()

    for q in queries:
        try:
            data = zenserp_search(q, num=10)
            results = data.get("organic", [])

            for item in results:
                url = item.get("url", "")
                domain = urlparse(url).netloc
                if domain and domain not in seen_urls:
                    seen_urls.add(domain)
                    all_results.append(item)

            print(f"   • '{q[:40]}...': {len(results)} результ.")

            # Извлекаем названия ЖК
            complexes = extract_complexes(data, KNOWN_STAVROPOL)
            for c in complexes:
                found_complexes.add(c)

            time.sleep(1.2)
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            time.sleep(2)

    return all_results, list(found_complexes)


def search_domrf_register(city):
    """Поиск через наш.дом.рф — официальный реестр строящихся ЖК"""
    print(f"  Поиск наш.дом.рф для {city}...")
    query = f"site:наш.дом.рф новостройки {city}"
    data = zenserp_search(query, num=10)
    return extract_complexes(data, KNOWN_STAVROPOL)


def search_stavropol_missing():
    """Поиск строящихся ЖК в Ставрополе, которых нет в таблице"""
    print("\n🔍 ** Ставрополь — поиск пропущенных ЖК **")
    queries = [
        "строящиеся ЖК Ставрополь список 2026",
        "новые жилые комплексы Ставрополь строятся",
        "Ставрополь застройщики новостройки список жилых комплексов",
        "новостройки Ставрополь новый адрес",
        "Жилые комплексы Ставрополь строительство",
    ]
    found = set()
    for q in queries:
        data = zenserp_search(q, num=10)
        complexes = extract_complexes(data, KNOWN_STAVROPOL)
        for c in complexes:
            found.add(c)
        time.sleep(1.2)
    return list(found)


if __name__ == "__main__":
    print("🚀 ===== ПОИСК НОВОСТРОЕК =====")
    
    # 1. Проверяем, не пропустили ли ЖК в Ставрополе
    print("\n" + "="*60)
    print("ЭТАП 1: Поиск пропущенных ЖК в Ставрополе")
    print("="*60)
    stavropol_missing = search_stavropol_missing()
    if stavropol_missing:
        print(f"\n  Возможно пропущены: {stavropol_missing}")
    else:
        print("\n  ✅ Дополнительных ЖК не найдено (или все уже в таблице)")
    
    # 2. Поиск по КМВ
    print("\n" + "="*60)
    print("ЭТАП 2: Поиск новостроек в КМВ")
    print("="*60)
    
    all_kmv_complexes = {}
    
    for city in KMV_CITIES:
        results, complexes = search_city_new_buildings(city)
        all_kmv_complexes[city] = complexes
        if complexes:
            print(f"  🏗 Найдены ЖК: {complexes}")
        else:
            print(f"  ⚠️ Названия ЖК не извлечены (нужен разбор ссылок)")
        print(f"  📎 Источников: {len(results)}")
    
    print("\n" + "="*60)
    print("ЭТАП 3: Официальный реестр наш.дом.рф")
    print("="*60)
    for city in ["Ставрополь"] + KMV_CITIES:
        domrf = search_domrf_register(city)
        print(f"  {city}: {domrf}")
    
    print("\n✅ Поиск завершён")
