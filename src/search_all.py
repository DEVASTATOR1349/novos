#!/usr/bin/env python3
"""
Сбор данных по новостройкам КМВ и Ставрополя через ZenSerp
"""
import os, re, json, time, requests
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("ZENSERP_API_KEY", "")
BASE = "https://app.zenserp.com/api/v2/search"

# Города для поиска
CITIES = [
    "Пятигорск", "Кисловодск", "Ессентуки", "Железноводск",
    "Минеральные Воды", "Лермонтов", "Георгиевск",
    "Ставрополь", "Михайловск",
]

# Уже известные ЖК в Ставрополе (чтобы не дублировать)
KNOWN = [
    "Первый", "Кварталы 17/77", "Софи", "Фруктовый Сад",
    "Гармония", "АКСИС ПАТРИОТ", "Северный", "Крокус",
    "Крокус 2", "Суворов", "Красный металлист", "Дыхание",
    "Мельница", "Европейский-5", "КРЫЛЬЯ", "Южный Квартал",
    "Надежда", "Дубровский", "НАСТОЯЩИЙ", "Федерация",
    "Небо", "Комсомольская 26", "Суворов Парк", "Гагарин", "Основа"
]


def zs(q, num=10):
    """ZenSerp search"""
    try:
        r = requests.get(BASE, params={"q": q, "apikey": API_KEY, "num": num, "gl": "RU", "hl": "ru"}, timeout=12)
        if r.status_code == 200:
            return r.json()
        return {}
    except:
        return {}


def extract_names(text, city):
    """Извлечь названия ЖК из текста"""
    names = set()
    # Паттерны: ЖК "Название", «Название», жилой комплекс "Название"
    pats = [
        r'Ж[Кк][»"\s]*([А-ЯЁ][а-яёA-Za-z0-9\-]{2,40}?)',
        r'«([А-ЯЁ][а-яёA-Za-z0-9\- ]{2,40}?)»',
        r'"([А-ЯЁ][а-яёA-Za-z0-9\- ]{2,40}?)"\s*(?:,|\.|$)',
        r'([А-ЯЁ][а-яёA-Za-z0-9\- ]{3,30}?)\s+(?:от застройщика|строящийся)',
    ]
    for p in pats:
        for m in re.findall(p, text):
            m = m.strip().rstrip(',').rstrip('.')
            skip = ["Ставрополь", "Пятигорск", "Кисловодск", "Ессентуки",
                    "Минеральные Воды", "Железноводск", "Лермонтов", "Георгиевск",
                    "Москва", "Россия", "продаже", "строящемся", "новостройке",
                    "квартиру", "квартиры", "каталог", "новостройки", "застройщика",
                    "доме", "жилья", "просторные", "уютные", "срок", "снос", "дом",
                    "кирпичный", "монолитный", "панельный", "район", "центре"]
            if len(m) > 2 and m not in skip and m.upper() != m:
                skip_triggers = ["банк", "ипотек", "ремонт", "дизайн", "страх"]
                if not any(s in m.lower() for s in skip_triggers):
                    names.add(m)
    return names


def search_city(city):
    """Поиск новостроек по городу"""
    print(f"\n🔍 {city}...")

    queries = [
        f"новостройки {city} строящиеся ЖК",
        f"купить квартиру {city} новостройка застройщик",
        f"жилой комплекс {city} строящийся",
        f"{city} застройщики новостройки список",
        f"'ЖК' '{city}' строящийся",
        f"{city} строительство жилого комплекса 2026",
    ]

    all_links = []
    seen_domains = set()
    all_names = set()

    for q in queries:
        data = zs(q)
        for item in data.get("organic", []):
            url = item.get("url", "")
            domain = urlparse(url).netloc
            if domain and domain not in seen_domains:
                seen_domains.add(domain)
                all_links.append(item)
            # Ищем названия в заголовке и сниппете
            for text in [item.get("title", ""), item.get("snippet", "")]:
                names = extract_names(text, city)
                for n in names:
                    if n not in KNOWN:
                        all_names.add(n)
        time.sleep(1.0)

    print(f"  📎 Источников: {len(all_links)}")
    
    # Фильтруем только реальные агрегаторы/застройщиков
    real_links = [l for l in all_links if any(k in urlparse(l["url"]).netloc for k in
        ["domclick", "cian", "наш.дом", "xn--80az8a", "etagi", "krasdom", "avito",
         "realty.yandex", "domrf", "m2.ru", "vbr.ru", "новостройки" ])]
    
    # Если есть наш.дом.рф — идём туда за списком
    for link in all_links:
        u = link.get("url", "")
        if "xn--80az8a" in u or "наш.дом" in u or "дом.рф" in u:
            print(f"  🏛 Есть наш.дом.рф: {u[:80]}...")

    if all_names:
        print(f"  🏗 Найдены названия: {', '.join(sorted(all_names)[:10])}")
    
    return all_links, list(all_names)


def get_domrf_list(city):
    """Получить список ЖК с наш.дом.рф"""
    print(f"  🔎 наш.дом.рф / {city}...")
    q = f"site:xn--80az8a.xn--d1aqf.xn--p1ai/новостройки {city}"
    data = zs(q, num=10)
    names = set()
    for item in data.get("organic", []):
        t = item.get("title", "")
        s = item.get("snippet", "")
        # Собираем все найденные названия
        for text in [t, s]:
            for n in extract_names(text, city):
                if n not in KNOWN:
                    names.add(n)
    time.sleep(1.0)
    return list(names)


if __name__ == "__main__":
    print("🚀 ПОИСК НОВОСТРОЕК СТАВРОПОЛЬСКИЙ КРАЙ + КМВ")
    print("="*60)
    
    all_data = {}

    for city in CITIES:
        links, names = search_city(city)
        
        # Дополнительно ищем на наш.дом.рф
        domrf_names = get_domrf_list(city)
        names.extend([n for n in domrf_names if n not in names])
        
        all_data[city] = {"links": links, "names": names}
        
        # Сохраняем промежуточные результаты
        with open(f"results_{city.replace(' ','_')}.json", "w") as f:
            json.dump({"names": names, "links_count": len(links)}, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*60)
    print("📊 ИТОГИ")
    print("="*60)
    for city, data in all_data.items():
        names = data["names"]
        print(f"\n{city}:")
        if names:
            for n in sorted(names)[:15]:
                print(f"  🏗 {n}")
        else:
            print(f"  ⚠️ Названия не извлечены (буду парсить агрегаторы)")
        print(f"  Источников: {len(data['links'])}")
    
    print("\n✅ Готово!")
