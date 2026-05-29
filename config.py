import os
from dotenv import load_dotenv

load_dotenv()

ZENSERP_API_KEY = os.getenv("ZENSERP_API_KEY", "")

# Регионы поиска
REGIONS = {
    "stavropol": "Ставропольский край",
    "kmv": "Кавказские Минеральные Воды"
}

# Города КМВ для поиска
KMV_CITIES = [
    "Пятигорск", "Кисловодск", "Ессентуки", "Железноводск",
    "Минеральные Воды", "Лермонтов", "Георгиевск"
]
