"""
Inline Keyboards برای Movie Bot

تمام کیبوردهای Movie Bot در این فایل مدیریت می‌شوند
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any


# ========== Main Menu Keyboard ==========
def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """کیبورد منوی اصلی Movie Bot"""
    keyboard = [
        [InlineKeyboardButton(text="🔎 جستجو", callback_data="movie_search")],
        [
            InlineKeyboardButton(text="🎬 فیلم‌ها", callback_data="movie_list"),
            InlineKeyboardButton(text="📺 سریال‌ها", callback_data="series_list")
        ],
        [
            InlineKeyboardButton(text="🔥 محبوب‌ترین‌ها", callback_data="movie_popular"),
            InlineKeyboardButton(text="🆕 جدیدترین‌ها", callback_data="movie_latest")
        ],
        [InlineKeyboardButton(text="🎭 ژانرها", callback_data="movie_genres")],
        [InlineKeyboardButton(text="👤 پروفایل", callback_data="movie_profile")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ========== Movies List Keyboard ==========
def get_movies_list_keyboard(movies: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """کیبورد لیست فیلم‌ها"""
    keyboard = []
    
    for movie in movies:
        button_text = f"{movie.get('poster', '🎬')} {movie['title']} ({movie['year']}) ⭐ {movie['rating']}"
        keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"movie_detail_{movie['id']}"
            )
        ])
    
    # دکمه بازگشت
    keyboard.append([
        InlineKeyboardButton(text="⬅️ بازگشت", callback_data="movie_home")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ========== Series List Keyboard ==========
def get_series_list_keyboard(series_list: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """کیبورد لیست سریال‌ها"""
    keyboard = []
    
    for series in series_list:
        button_text = f"{series.get('poster', '📺')} {series['title']} ({series['year']}) ⭐ {series['rating']}"
        keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"series_detail_{series['id']}"
            )
        ])
    
    # دکمه بازگشت
    keyboard.append([
        InlineKeyboardButton(text="⬅️ بازگشت", callback_data="movie_home")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ========== Movie Detail Keyboard ==========
def get_movie_detail_keyboard(movie_id: int) -> InlineKeyboardMarkup:
    """کیبورد جزئیات فیلم"""
    keyboard = [
        [
            InlineKeyboardButton(text="▶️ تماشا", callback_data=f"movie_watch_{movie_id}"),
            InlineKeyboardButton(text="⬇️ دانلود", callback_data=f"movie_download_{movie_id}")
        ],
        [InlineKeyboardButton(text="❤️ افزودن به علاقه‌مندی‌ها", callback_data=f"movie_favorite_{movie_id}")],
        [InlineKeyboardButton(text="⬅️ بازگشت به لیست", callback_data="movie_list")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ========== Series Detail Keyboard ==========
def get_series_detail_keyboard(series_id: int) -> InlineKeyboardMarkup:
    """کیبورد جزئیات سریال"""
    keyboard = [
        [
            InlineKeyboardButton(text="▶️ تماشا", callback_data=f"series_watch_{series_id}"),
            InlineKeyboardButton(text="⬇️ دانلود", callback_data=f"series_download_{series_id}")
        ],
        [InlineKeyboardButton(text="❤️ افزودن به علاقه‌مندی‌ها", callback_data=f"series_favorite_{series_id}")],
        [InlineKeyboardButton(text="⬅️ بازگشت به لیست", callback_data="series_list")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ========== Genres Keyboard ==========
def get_genres_keyboard() -> InlineKeyboardMarkup:
    """کیبورد ژانرها"""
    from data.movie_mock_data import GENRES
    
    keyboard = []
    
    # دو ژانر در هر ردیف
    for i in range(0, len(GENRES), 2):
        row = []
        for j in range(2):
            if i + j < len(GENRES):
                genre = GENRES[i + j]
                row.append(
                    InlineKeyboardButton(
                        text=f"{genre['emoji']} {genre['name']}",
                        callback_data=f"genre_{genre['id']}"
                    )
                )
        keyboard.append(row)
    
    # دکمه بازگشت
    keyboard.append([
        InlineKeyboardButton(text="⬅️ بازگشت", callback_data="movie_home")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ========== Genre Results Keyboard ==========
def get_genre_results_keyboard(genre_id: str, movies: List[Dict[str, Any]], series: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """کیبورد نتایج یک ژانر"""
    keyboard = []
    
    # فیلم‌ها
    if movies:
        for movie in movies[:3]:  # نمایش حداکثر 3 نتیجه
            button_text = f"🎬 {movie['title']} ({movie['year']})"
            keyboard.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"movie_detail_{movie['id']}"
                )
            ])
    
    # سریال‌ها
    if series:
        for s in series[:3]:  # نمایش حداکثر 3 نتیجه
            button_text = f"📺 {s['title']} ({s['year']})"
            keyboard.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"series_detail_{s['id']}"
                )
            ])
    
    # دکمه بازگشت
    keyboard.append([
        InlineKeyboardButton(text="⬅️ بازگشت به ژانرها", callback_data="movie_genres")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ========== Search Results Keyboard ==========
def get_search_results_keyboard(movies: List[Dict[str, Any]], series: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """کیبورد نتایج جستجو"""
    keyboard = []
    
    # فیلم‌ها
    if movies:
        keyboard.append([InlineKeyboardButton(text="📽️ فیلم‌ها:", callback_data="noop")])
        for movie in movies:
            button_text = f"{movie.get('poster', '🎬')} {movie['title']} ({movie['year']})"
            keyboard.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"movie_detail_{movie['id']}"
                )
            ])
    
    # سریال‌ها
    if series:
        keyboard.append([InlineKeyboardButton(text="📺 سریال‌ها:", callback_data="noop")])
        for s in series:
            button_text = f"{s.get('poster', '📺')} {s['title']} ({s['year']})"
            keyboard.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"series_detail_{s['id']}"
                )
            ])
    
    # دکمه بازگشت
    keyboard.append([
        InlineKeyboardButton(text="⬅️ بازگشت", callback_data="movie_home")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ========== Profile Keyboard ==========
def get_profile_keyboard() -> InlineKeyboardMarkup:
    """کیبورد پروفایل کاربر"""
    keyboard = [
        [InlineKeyboardButton(text="❤️ علاقه‌مندی‌های من", callback_data="movie_favorites")],
        [InlineKeyboardButton(text="⬅️ بازگشت", callback_data="movie_home")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ========== Favorites Keyboard ==========
def get_favorites_keyboard() -> InlineKeyboardMarkup:
    """کیبورد لیست علاقه‌مندی‌ها (فعلاً خالی)"""
    keyboard = [
        [InlineKeyboardButton(text="⬅️ بازگشت به پروفایل", callback_data="movie_profile")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ========== Cancel Search Keyboard ==========
def get_cancel_search_keyboard() -> InlineKeyboardMarkup:
    """کیبورد لغو جستجو"""
    keyboard = [
        [InlineKeyboardButton(text="❌ لغو جستجو", callback_data="movie_home")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ========== Back to Home Keyboard ==========
def get_back_to_home_keyboard() -> InlineKeyboardMarkup:
    """کیبورد ساده بازگشت به خانه"""
    keyboard = [
        [InlineKeyboardButton(text="⬅️ بازگشت به منوی اصلی", callback_data="movie_home")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
