import requests, json, os
from urllib.parse import quote

API_KEY = "7ffea110-5b63-11f1-9765-4bf76e2c02e1"
BASE = "https://app.zenserp.com/api/v2/search"

results_dir = "zenserp_results"
os.makedirs(results_dir, exist_ok=True)

def search(query, label=""):
    """Search via ZenSerp and save result"""
    params = {"apikey": API_KEY, "q": query, "num": 5, "gl": "ru", "hl": "ru"}
    r = requests.get(BASE, params=params, timeout=30)
    fname = f"{results_dir}/{label or quote(query[:40])}.json"
    with open(fname, "w") as f:
        json.dump(r.json(), f, ensure_ascii=False, indent=2)
    print(f"{label}: {r.status_code} -> {fname}")
    
    organic = r.json().get("organic", [])
    for o in organic[:5]:
        print(f"  {o['position']}. {o['title']}: {o.get('url','')[:80]}")
    print()
    return r.json()

# === 1. ЗАСТРОЙЩИКИ (developer names) ===
# Pятигорск
search("ЖК Алые паруса Пятигорск застройщик", "z_alyeparusa")
search("ЖК Новый Пятигорск застройщик", "z_novpyat")
search("ЖК Миленеум Пятигорск застройщик", "z_mileneum")
search("ЖК Курортный Пятигорск застройщик", "z_kurort")
search("ЖК ВОЛНА Пятигорск застройщик", "z_volna")

# Ессентуки
search("ЖК Кленовая роща Ессентуки застройщик", "z_klen")
search("ЖК Квартал Лета Ессентуки застройщик", "z_kvlet")
search("ЖК Николаевский Ессентуки застройщик", "z_nikol")
search("ЖК Кристалл Ессентуки застройщик", "z_kristall")

# Кисловодск
search("ЖК Печорин Кисловодск застройщик", "z_pechorin")
search("ЖК Реликт Кисловодск застройщик", "z_relikt")
search("Дом на Московской Кисловодск застройщик", "z_moscow")
search("ЖК Виноград Кисловодск застройщик", "z_vinograd")
search("ЖК Моя Легенда Кисловодск застройщик", "z_legenda")
search("MONE DOM у озера Кисловодск застройщик", "z_monedom")

# Железноводск
search("ЖК Нагория Железноводск застройщик", "z_nagoriya")
search("ЖК Живописный Железноводск застройщик", "z_zhivopis")

# Лермонтов, Георгиевск, Предгорный
search("ЖК Лермонтов Парк Джуца застройщик", "z_lermpark")
search("ЖК Резиденция Лермонтов застройщик", "z_rezid")
search("ЖК Кристалл Георгиевск застройщик", "z_kristgeor")

