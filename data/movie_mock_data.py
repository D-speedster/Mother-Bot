"""
Mock Data برای Movie Bot UI Prototype

⚠️ این داده‌ها فقط برای نمایش UI هستند
هیچ فایل واقعی، دانلود، یا API خارجی وجود ندارد
"""

from typing import List, Dict, Any, Optional


# ========== Mock Movies Data ==========
MOCK_MOVIES: List[Dict[str, Any]] = [
    {
        "id": 1,
        "title": "Inception",
        "title_fa": "تلقین",
        "year": 2010,
        "country": "USA",
        "genre": ["Action", "Sci-Fi", "Thriller"],
        "rating": 8.8,
        "duration": "148 دقیقه",
        "director": "Christopher Nolan",
        "description": (
            "یک دزد ماهر که در هنر استخراج اسرار از ضمیر ناخودآگاه افراد "
            "در حین خواب تخصص دارد، فرصتی برای بازگشت به زندگی عادی پیدا می‌کند."
        ),
        "poster": "🎬"
    },
    {
        "id": 2,
        "title": "Interstellar",
        "title_fa": "در میان ستارگان",
        "year": 2014,
        "country": "USA",
        "genre": ["Sci-Fi", "Drama", "Adventure"],
        "rating": 8.7,
        "duration": "169 دقیقه",
        "director": "Christopher Nolan",
        "description": (
            "گروهی از کاوشگران از یک کرم‌چاله در فضا برای تضمین بقای بشریت استفاده می‌کنند."
        ),
        "poster": "🌌"
    },
    {
        "id": 3,
        "title": "The Dark Knight",
        "title_fa": "شوالیه تاریکی",
        "year": 2008,
        "country": "USA",
        "genre": ["Action", "Crime", "Drama"],
        "rating": 9.0,
        "duration": "152 دقیقه",
        "director": "Christopher Nolan",
        "description": (
            "وقتی جوکر، یک جنایتکار آنارشیست، شهر گاتهام را به هرج و مرج می‌کشاند، "
            "بتمن باید بزرگترین آزمون روانی خود را پشت سر بگذارد."
        ),
        "poster": "🦇"
    },
    {
        "id": 4,
        "title": "Dune",
        "title_fa": "تلماسه",
        "year": 2021,
        "country": "USA",
        "genre": ["Sci-Fi", "Adventure", "Drama"],
        "rating": 8.0,
        "duration": "155 دقیقه",
        "director": "Denis Villeneuve",
        "description": (
            "پسر یک خانواده اشرافی با وظیفه حفاظت از با ارزش‌ترین دارایی کهکشان بر عهده دارد."
        ),
        "poster": "🏜️"
    },
    {
        "id": 5,
        "title": "Oppenheimer",
        "title_fa": "اوپنهایمر",
        "year": 2023,
        "country": "USA",
        "genre": ["Biography", "Drama", "History"],
        "rating": 8.6,
        "duration": "180 دقیقه",
        "director": "Christopher Nolan",
        "description": (
            "داستان زندگی جی. رابرت اوپنهایمر، فیزیکدان نظری آمریکایی و نقش او در توسعه بمب اتم."
        ),
        "poster": "💣"
    }
]


# ========== Mock Series Data ==========
MOCK_SERIES: List[Dict[str, Any]] = [
    {
        "id": 101,
        "title": "Breaking Bad",
        "title_fa": "بریکینگ بد",
        "year": 2008,
        "country": "USA",
        "genre": ["Crime", "Drama", "Thriller"],
        "rating": 9.5,
        "seasons": 5,
        "episodes": 62,
        "status": "پایان یافته",
        "description": (
            "معلم شیمی دبیرستانی که به سرطان مبتلا شده، با یکی از شاگردان "
            "سابق خود شروع به تولید و فروش متامفتامین می‌کند."
        ),
        "poster": "🧪"
    },
    {
        "id": 102,
        "title": "Dark",
        "title_fa": "تاریکی",
        "year": 2017,
        "country": "Germany",
        "genre": ["Sci-Fi", "Mystery", "Thriller"],
        "rating": 8.8,
        "seasons": 3,
        "episodes": 26,
        "status": "پایان یافته",
        "description": (
            "داستان چهار خانواده و مسافرت در زمان آنها در یک شهر کوچک آلمانی."
        ),
        "poster": "🌑"
    },
    {
        "id": 103,
        "title": "Stranger Things",
        "title_fa": "چیزهای عجیب",
        "year": 2016,
        "country": "USA",
        "genre": ["Sci-Fi", "Horror", "Drama"],
        "rating": 8.7,
        "seasons": 4,
        "episodes": 42,
        "status": "در حال پخش",
        "description": (
            "وقتی یک پسر جوان ناپدید می‌شود، شهر کوچکش با آزمایش‌های محرمانه، "
            "نیروهای مافوق طبیعی و یک دختر عجیب روبرو می‌شود."
        ),
        "poster": "👾"
    },
    {
        "id": 104,
        "title": "The Last of Us",
        "title_fa": "آخرین از ما",
        "year": 2023,
        "country": "USA",
        "genre": ["Action", "Adventure", "Drama"],
        "rating": 8.9,
        "seasons": 1,
        "episodes": 9,
        "status": "در حال پخش",
        "description": (
            "بیست سال پس از ویرانی تمدن مدرن توسط یک قارچ، یک مرد باید "
            "دختر ۱۴ ساله‌ای را در سراسر ایالات متحده پس از آخرالزمان همراهی کند."
        ),
        "poster": "🍄"
    },
    {
        "id": 105,
        "title": "Game of Thrones",
        "title_fa": "بازی تاج و تخت",
        "year": 2011,
        "country": "USA",
        "genre": ["Fantasy", "Drama", "Adventure"],
        "rating": 9.2,
        "seasons": 8,
        "episodes": 73,
        "status": "پایان یافته",
        "description": (
            "نه خاندان اشرافی برای کنترل سرزمین‌های افسانه‌ای وستروس می‌جنگند، "
            "در حالی که یک دشمن قدیمی پس از قرن‌ها خاموشی بازمی‌گردد."
        ),
        "poster": "🐉"
    }
]


# ========== Mock Genres ==========
GENRES = [
    {"id": "action", "name": "اکشن", "emoji": "💥"},
    {"id": "comedy", "name": "کمدی", "emoji": "😂"},
    {"id": "horror", "name": "ترسناک", "emoji": "👻"},
    {"id": "scifi", "name": "علمی تخیلی", "emoji": "🚀"},
    {"id": "romance", "name": "عاشقانه", "emoji": "❤️"},
    {"id": "crime", "name": "جنایی", "emoji": "🔪"},
    {"id": "drama", "name": "درام", "emoji": "🎭"},
    {"id": "fantasy", "name": "فانتزی", "emoji": "🧙"}
]


# ========== Helper Functions ==========

def get_movie_by_id(movie_id: int) -> Optional[Dict[str, Any]]:
    """دریافت فیلم با ID"""
    for movie in MOCK_MOVIES:
        if movie["id"] == movie_id:
            return movie
    return None


def get_series_by_id(series_id: int) -> Optional[Dict[str, Any]]:
    """دریافت سریال با ID"""
    for series in MOCK_SERIES:
        if series["id"] == series_id:
            return series
    return None


def search_movies(query: str) -> List[Dict[str, Any]]:
    """جستجوی ساده در Mock Movies"""
    query_lower = query.lower()
    results = []
    
    for movie in MOCK_MOVIES:
        # جستجو در عنوان انگلیسی و فارسی
        if (query_lower in movie["title"].lower() or 
            query_lower in movie.get("title_fa", "").lower()):
            results.append(movie)
    
    return results


def search_series(query: str) -> List[Dict[str, Any]]:
    """جستجوی ساده در Mock Series"""
    query_lower = query.lower()
    results = []
    
    for series in MOCK_SERIES:
        # جستجو در عنوان انگلیسی و فارسی
        if (query_lower in series["title"].lower() or 
            query_lower in series.get("title_fa", "").lower()):
            results.append(series)
    
    return results


def search_all(query: str) -> Dict[str, List[Dict[str, Any]]]:
    """جستجو در همه محتوا"""
    return {
        "movies": search_movies(query),
        "series": search_series(query)
    }


def get_popular_movies(limit: int = 5) -> List[Dict[str, Any]]:
    """دریافت محبوب‌ترین فیلم‌ها (مرتب شده بر اساس rating)"""
    sorted_movies = sorted(MOCK_MOVIES, key=lambda x: x["rating"], reverse=True)
    return sorted_movies[:limit]


def get_popular_series(limit: int = 5) -> List[Dict[str, Any]]:
    """دریافت محبوب‌ترین سریال‌ها (مرتب شده بر اساس rating)"""
    sorted_series = sorted(MOCK_SERIES, key=lambda x: x["rating"], reverse=True)
    return sorted_series[:limit]


def get_latest_movies(limit: int = 5) -> List[Dict[str, Any]]:
    """دریافت جدیدترین فیلم‌ها (مرتب شده بر اساس year)"""
    sorted_movies = sorted(MOCK_MOVIES, key=lambda x: x["year"], reverse=True)
    return sorted_movies[:limit]


def get_latest_series(limit: int = 5) -> List[Dict[str, Any]]:
    """دریافت جدیدترین سریال‌ها (مرتب شده بر اساس year)"""
    sorted_series = sorted(MOCK_SERIES, key=lambda x: x["year"], reverse=True)
    return sorted_series[:limit]


def get_movies_by_genre(genre: str) -> List[Dict[str, Any]]:
    """دریافت فیلم‌ها بر اساس ژانر (Mock - فقط نمونه)"""
    # در نسخه واقعی باید genre را با دقت چک کرد
    # اینجا فقط یک نمونه ساده است
    results = []
    for movie in MOCK_MOVIES:
        if any(genre.lower() in g.lower() for g in movie["genre"]):
            results.append(movie)
    return results


def get_series_by_genre(genre: str) -> List[Dict[str, Any]]:
    """دریافت سریال‌ها بر اساس ژانر (Mock - فقط نمونه)"""
    results = []
    for series in MOCK_SERIES:
        if any(genre.lower() in g.lower() for g in series["genre"]):
            results.append(series)
    return results
