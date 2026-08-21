"""
Child Bot: Movie & Series Bot (UI Prototype)

⚠️ این یک Prototype UI است:
- هیچ فایل واقعی ارائه نمی‌شود
- هیچ دانلود واقعی وجود ندارد
- هیچ API خارجی استفاده نمی‌شود
- فقط Mock Data برای نمایش UI

این Bot از همان Runtime فعلی پروژه استفاده می‌کند
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from data.movie_mock_data import (
    MOCK_MOVIES,
    MOCK_SERIES,
    GENRES,
    get_movie_by_id,
    get_series_by_id,
    search_all,
    get_popular_movies,
    get_popular_series,
    get_latest_movies,
    get_latest_series,
    get_movies_by_genre,
    get_series_by_genre
)

from keyboards.movie_keyboards import (
    get_main_menu_keyboard,
    get_movies_list_keyboard,
    get_series_list_keyboard,
    get_movie_detail_keyboard,
    get_series_detail_keyboard,
    get_genres_keyboard,
    get_genre_results_keyboard,
    get_search_results_keyboard,
    get_profile_keyboard,
    get_favorites_keyboard,
    get_cancel_search_keyboard,
    get_back_to_home_keyboard
)

logger = logging.getLogger(__name__)


# ========== FSM States ==========
class MovieBotStates(StatesGroup):
    """State‌های FSM برای Movie Bot"""
    waiting_for_search = State()


# ========== Router Factory Function ==========
def get_router() -> Router:
    """
    ساخت و برگرداندن Router جدید برای Movie Bot
    
    ⚠️ CRITICAL: این تابع هر بار یک Router جدید می‌سازد
    - این از تداخل Router بین ربات‌های مختلف جلوگیری می‌کند
    - هر ربات فرزند Router اختصاصی خود را دارد
    
    Returns:
        Router جدید با تمام handler‌های ثبت‌شده
    """
    router = Router(name="movie_bot")
    
    # ثبت handler‌ها
    router.message.register(cmd_start, Command("start"))
    router.message.register(cmd_help, Command("help"))
    
    # Callback handlers
    router.callback_query.register(callback_home, F.data == "movie_home")
    router.callback_query.register(callback_movies_list, F.data == "movie_list")
    router.callback_query.register(callback_series_list, F.data == "series_list")
    router.callback_query.register(callback_popular, F.data == "movie_popular")
    router.callback_query.register(callback_latest, F.data == "movie_latest")
    router.callback_query.register(callback_genres, F.data == "movie_genres")
    router.callback_query.register(callback_profile, F.data == "movie_profile")
    router.callback_query.register(callback_favorites, F.data == "movie_favorites")
    router.callback_query.register(callback_search_start, F.data == "movie_search")
    
    # Movie detail callbacks
    router.callback_query.register(callback_movie_detail, F.data.startswith("movie_detail_"))
    router.callback_query.register(callback_movie_watch, F.data.startswith("movie_watch_"))
    router.callback_query.register(callback_movie_download, F.data.startswith("movie_download_"))
    router.callback_query.register(callback_movie_favorite, F.data.startswith("movie_favorite_"))
    
    # Series detail callbacks
    router.callback_query.register(callback_series_detail, F.data.startswith("series_detail_"))
    router.callback_query.register(callback_series_watch, F.data.startswith("series_watch_"))
    router.callback_query.register(callback_series_download, F.data.startswith("series_download_"))
    router.callback_query.register(callback_series_favorite, F.data.startswith("series_favorite_"))
    
    # Genre callbacks
    router.callback_query.register(callback_genre_detail, F.data.startswith("genre_"))
    
    # Search handler (FSM)
    router.message.register(handle_search_input, MovieBotStates.waiting_for_search)
    
    return router


# ⚠️ DEPRECATED: این router global دیگر استفاده نمی‌شود
# فقط برای backward compatibility نگه داشته شده
movie_router = Router(name="movie_legacy")


# ========== Helper Functions ==========

def format_movie_card(movie: dict) -> str:
    """فرمت کردن کارت اطلاعات فیلم"""
    genres_text = " • ".join(movie.get("genre", []))
    
    text = (
        f"{movie.get('poster', '🎬')} **{movie['title']}**\n"
        f"*{movie.get('title_fa', '')}*\n\n"
        f"⭐ امتیاز: **{movie['rating']}/10**\n"
        f"📅 سال: {movie['year']}\n"
        f"🌍 کشور: {movie['country']}\n"
        f"🎭 ژانر: {genres_text}\n"
        f"⏱️ مدت: {movie.get('duration', 'نامشخص')}\n"
        f"🎬 کارگردان: {movie.get('director', 'نامشخص')}\n\n"
        f"📝 **درباره فیلم:**\n{movie['description']}"
    )
    
    return text


def format_series_card(series: dict) -> str:
    """فرمت کردن کارت اطلاعات سریال"""
    genres_text = " • ".join(series.get("genre", []))
    
    text = (
        f"{series.get('poster', '📺')} **{series['title']}**\n"
        f"*{series.get('title_fa', '')}*\n\n"
        f"⭐ امتیاز: **{series['rating']}/10**\n"
        f"📅 سال: {series['year']}\n"
        f"🌍 کشور: {series['country']}\n"
        f"🎭 ژانر: {genres_text}\n"
        f"📺 فصل‌ها: {series.get('seasons', 0)}\n"
        f"🎬 قسمت‌ها: {series.get('episodes', 0)}\n"
        f"📊 وضعیت: {series.get('status', 'نامشخص')}\n\n"
        f"📝 **درباره سریال:**\n{series['description']}"
    )
    
    return text


# ========== Handler: /start ==========
async def cmd_start(message: Message, state: FSMContext):
    """
    Handler دستور /start
    نمایش صفحه اصلی با منوی Inline
    """
    # Clear کردن state قبلی (اگر وجود داشته باشد)
    await state.clear()
    
    # دریافت نام ربات
    try:
        bot_info = await message.bot.me()
        bot_name = bot_info.first_name or "ربات فیلم و سریال"
    except Exception:
        bot_name = "ربات فیلم و سریال"
    
    welcome_text = (
        f"🎬 **به {bot_name} خوش آمدید!**\n\n"
        f"🎥 آرشیو کامل فیلم و سریال\n"
        f"🔍 جستجوی آسان\n"
        f"⭐ به‌روزترین محتوا\n\n"
        f"از منوی زیر یک گزینه را انتخاب کنید:"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )
    
    logger.info(f"کاربر {message.from_user.id} Movie Bot را شروع کرد")


# ========== Handler: /help ==========
async def cmd_help(message: Message):
    """نمایش راهنمای استفاده از ربات"""
    help_text = (
        "📋 **راهنمای استفاده از ربات**\n\n"
        "🔎 **جستجو:**\n"
        "• روی دکمه «جستجو» کلیک کنید\n"
        "• نام فیلم یا سریال را بنویسید\n\n"
        "🎬 **فیلم‌ها / سریال‌ها:**\n"
        "• مشاهده لیست کامل\n"
        "• انتخاب و مشاهده جزئیات\n\n"
        "🎭 **ژانرها:**\n"
        "• مرور بر اساس دسته‌بندی\n\n"
        "💡 **نکته:** این ربات در حال توسعه است و "
        "فعلاً فقط UI نمایش داده می‌شود."
    )
    await message.answer(help_text, parse_mode="Markdown")
    logger.info(f"کاربر {message.from_user.id} راهنما را مشاهده کرد")


# ========== Callback: Home ==========
async def callback_home(callback: CallbackQuery, state: FSMContext):
    """بازگشت به صفحه اصلی"""
    await state.clear()
    
    text = (
        "🎬 **صفحه اصلی**\n\n"
        "به آرشیو فیلم و سریال خوش آمدید.\n"
        "از منوی زیر یک گزینه را انتخاب کنید:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


# ========== Callback: Movies List ==========
async def callback_movies_list(callback: CallbackQuery):
    """نمایش لیست فیلم‌ها"""
    text = (
        "🎬 **لیست فیلم‌ها**\n\n"
        f"تعداد: {len(MOCK_MOVIES)} فیلم\n\n"
        "برای مشاهده جزئیات، روی فیلم کلیک کنید:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_movies_list_keyboard(MOCK_MOVIES),
        parse_mode="Markdown"
    )
    await callback.answer()
    logger.info(f"کاربر {callback.from_user.id} لیست فیلم‌ها را مشاهده کرد")


# ========== Callback: Series List ==========
async def callback_series_list(callback: CallbackQuery):
    """نمایش لیست سریال‌ها"""
    text = (
        "📺 **لیست سریال‌ها**\n\n"
        f"تعداد: {len(MOCK_SERIES)} سریال\n\n"
        "برای مشاهده جزئیات، روی سریال کلیک کنید:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_series_list_keyboard(MOCK_SERIES),
        parse_mode="Markdown"
    )
    await callback.answer()
    logger.info(f"کاربر {callback.from_user.id} لیست سریال‌ها را مشاهده کرد")


# ========== Callback: Popular ==========
async def callback_popular(callback: CallbackQuery):
    """نمایش محبوب‌ترین‌ها"""
    popular_movies = get_popular_movies(5)
    popular_series = get_popular_series(5)
    
    text = (
        "🔥 **محبوب‌ترین‌ها**\n\n"
        "بر اساس امتیاز IMDB\n\n"
        "انتخاب کنید:"
    )
    
    # ترکیب فیلم و سریال
    combined = []
    combined.extend(popular_movies[:3])
    combined.extend(popular_series[:2])
    
    # ساخت کیبورد دستی
    keyboard = []
    for item in combined:
        if 'seasons' in item:  # سریال
            button_text = f"{item.get('poster', '📺')} {item['title']} ({item['year']}) ⭐ {item['rating']}"
            keyboard.append([
                {
                    "text": button_text,
                    "callback_data": f"series_detail_{item['id']}"
                }
            ])
        else:  # فیلم
            button_text = f"{item.get('poster', '🎬')} {item['title']} ({item['year']}) ⭐ {item['rating']}"
            keyboard.append([
                {
                    "text": button_text,
                    "callback_data": f"movie_detail_{item['id']}"
                }
            ])
    
    keyboard.append([{"text": "⬅️ بازگشت", "callback_data": "movie_home"}])
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(**btn) for btn in row] for row in keyboard]
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    await callback.answer()


# ========== Callback: Latest ==========
async def callback_latest(callback: CallbackQuery):
    """نمایش جدیدترین‌ها"""
    latest_movies = get_latest_movies(5)
    latest_series = get_latest_series(5)
    
    text = (
        "🆕 **جدیدترین‌ها**\n\n"
        "آخرین محتوای اضافه شده\n\n"
        "انتخاب کنید:"
    )
    
    # ترکیب فیلم و سریال
    combined = []
    combined.extend(latest_movies[:3])
    combined.extend(latest_series[:2])
    
    # ساخت کیبورد دستی
    keyboard = []
    for item in combined:
        if 'seasons' in item:  # سریال
            button_text = f"{item.get('poster', '📺')} {item['title']} ({item['year']})"
            keyboard.append([
                {
                    "text": button_text,
                    "callback_data": f"series_detail_{item['id']}"
                }
            ])
        else:  # فیلم
            button_text = f"{item.get('poster', '🎬')} {item['title']} ({item['year']})"
            keyboard.append([
                {
                    "text": button_text,
                    "callback_data": f"movie_detail_{item['id']}"
                }
            ])
    
    keyboard.append([{"text": "⬅️ بازگشت", "callback_data": "movie_home"}])
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(**btn) for btn in row] for row in keyboard]
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    await callback.answer()


# ========== Callback: Genres ==========
async def callback_genres(callback: CallbackQuery):
    """نمایش لیست ژانرها"""
    text = (
        "🎭 **ژانرها**\n\n"
        "یک دسته‌بندی را انتخاب کنید:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_genres_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


# ========== Callback: Genre Detail ==========
async def callback_genre_detail(callback: CallbackQuery):
    """نمایش محتوای یک ژانر"""
    genre_id = callback.data.replace("genre_", "")
    
    # پیدا کردن نام ژانر
    genre_name = "نامشخص"
    genre_emoji = "🎭"
    for g in GENRES:
        if g["id"] == genre_id:
            genre_name = g["name"]
            genre_emoji = g["emoji"]
            break
    
    # جستجوی ساده در mock data
    movies = get_movies_by_genre(genre_name)
    series = get_series_by_genre(genre_name)
    
    if not movies and not series:
        text = (
            f"{genre_emoji} **ژانر: {genre_name}**\n\n"
            f"❌ محتوایی در این دسته یافت نشد.\n\n"
            f"💡 این بخش در حال توسعه است."
        )
        await callback.message.edit_text(
            text,
            reply_markup=get_back_to_home_keyboard(),
            parse_mode="Markdown"
        )
    else:
        text = (
            f"{genre_emoji} **ژانر: {genre_name}**\n\n"
            f"🎬 {len(movies)} فیلم\n"
            f"📺 {len(series)} سریال\n\n"
            f"انتخاب کنید:"
        )
        await callback.message.edit_text(
            text,
            reply_markup=get_genre_results_keyboard(genre_id, movies, series),
            parse_mode="Markdown"
        )
    
    await callback.answer()


# ========== Callback: Movie Detail ==========
async def callback_movie_detail(callback: CallbackQuery):
    """نمایش جزئیات فیلم"""
    movie_id = int(callback.data.replace("movie_detail_", ""))
    movie = get_movie_by_id(movie_id)
    
    if not movie:
        await callback.answer("❌ فیلم یافت نشد", show_alert=True)
        return
    
    text = format_movie_card(movie)
    
    await callback.message.edit_text(
        text,
        reply_markup=get_movie_detail_keyboard(movie_id),
        parse_mode="Markdown"
    )
    await callback.answer()
    logger.info(f"کاربر {callback.from_user.id} جزئیات فیلم {movie_id} را مشاهده کرد")


# ========== Callback: Series Detail ==========
async def callback_series_detail(callback: CallbackQuery):
    """نمایش جزئیات سریال"""
    series_id = int(callback.data.replace("series_detail_", ""))
    series = get_series_by_id(series_id)
    
    if not series:
        await callback.answer("❌ سریال یافت نشد", show_alert=True)
        return
    
    text = format_series_card(series)
    
    await callback.message.edit_text(
        text,
        reply_markup=get_series_detail_keyboard(series_id),
        parse_mode="Markdown"
    )
    await callback.answer()
    logger.info(f"کاربر {callback.from_user.id} جزئیات سریال {series_id} را مشاهده کرد")


# ========== Callback: Movie Watch ==========
async def callback_movie_watch(callback: CallbackQuery):
    """دکمه تماشای فیلم (Prototype - فعال نیست)"""
    await callback.answer(
        "🚧 این قابلیت در نسخه Prototype فعال نیست",
        show_alert=True
    )


# ========== Callback: Movie Download ==========
async def callback_movie_download(callback: CallbackQuery):
    """دکمه دانلود فیلم (Prototype - فعال نیست)"""
    await callback.answer(
        "🚧 این قابلیت در نسخه Prototype فعال نیست",
        show_alert=True
    )


# ========== Callback: Movie Favorite ==========
async def callback_movie_favorite(callback: CallbackQuery):
    """افزودن فیلم به علاقه‌مندی‌ها (Prototype - فعال نیست)"""
    await callback.answer(
        "❤️ این فیلم به علاقه‌مندی‌های شما اضافه شد (Mock)",
        show_alert=False
    )


# ========== Callback: Series Watch ==========
async def callback_series_watch(callback: CallbackQuery):
    """دکمه تماشای سریال (Prototype - فعال نیست)"""
    await callback.answer(
        "🚧 این قابلیت در نسخه Prototype فعال نیست",
        show_alert=True
    )


# ========== Callback: Series Download ==========
async def callback_series_download(callback: CallbackQuery):
    """دکمه دانلود سریال (Prototype - فعال نیست)"""
    await callback.answer(
        "🚧 این قابلیت در نسخه Prototype فعال نیست",
        show_alert=True
    )


# ========== Callback: Series Favorite ==========
async def callback_series_favorite(callback: CallbackQuery):
    """افزودن سریال به علاقه‌مندی‌ها (Prototype - فعال نیست)"""
    await callback.answer(
        "❤️ این سریال به علاقه‌مندی‌های شما اضافه شد (Mock)",
        show_alert=False
    )


# ========== Callback: Profile ==========
async def callback_profile(callback: CallbackQuery):
    """نمایش پروفایل کاربر"""
    user = callback.from_user
    
    text = (
        "👤 **پروفایل کاربری**\n\n"
        f"نام: {user.first_name}\n"
        f"شناسه: `{user.id}`\n"
        f"یوزرنیم: @{user.username if user.username else 'ندارد'}\n\n"
        f"❤️ علاقه‌مندی‌ها: 0\n\n"
        f"💡 این بخش در حال توسعه است"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_profile_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


# ========== Callback: Favorites ==========
async def callback_favorites(callback: CallbackQuery):
    """نمایش لیست علاقه‌مندی‌ها"""
    text = (
        "❤️ **علاقه‌مندی‌های من**\n\n"
        "شما هنوز هیچ محتوایی به علاقه‌مندی‌ها اضافه نکرده‌اید.\n\n"
        "💡 برای افزودن، در صفحه جزئیات فیلم یا سریال روی دکمه ❤️ کلیک کنید."
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_favorites_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


# ========== Callback: Search Start ==========
async def callback_search_start(callback: CallbackQuery, state: FSMContext):
    """شروع فرآیند جستجو"""
    await state.set_state(MovieBotStates.waiting_for_search)
    
    text = (
        "🔎 **جستجو**\n\n"
        "نام فیلم یا سریال مورد نظر خود را بنویسید:\n\n"
        "مثال: Dark\n"
        "مثال: Inception"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_cancel_search_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()
    logger.info(f"کاربر {callback.from_user.id} وارد حالت جستجو شد")


# ========== Handler: Search Input ==========
async def handle_search_input(message: Message, state: FSMContext):
    """پردازش ورودی جستجو"""
    query = message.text.strip()
    
    if not query:
        await message.answer("⚠️ لطفاً یک نام معتبر وارد کنید")
        return
    
    # جستجو در Mock Data
    results = search_all(query)
    movies = results["movies"]
    series = results["series"]
    
    # Clear state
    await state.clear()
    
    if not movies and not series:
        text = (
            f"🔎 **نتایج جستجو برای:** `{query}`\n\n"
            f"❌ نتیجه‌ای یافت نشد.\n\n"
            f"💡 لطفاً کلمات دیگری را امتحان کنید."
        )
        await message.answer(
            text,
            reply_markup=get_back_to_home_keyboard(),
            parse_mode="Markdown"
        )
    else:
        text = (
            f"🔎 **نتایج جستجو برای:** `{query}`\n\n"
            f"🎬 {len(movies)} فیلم\n"
            f"📺 {len(series)} سریال\n\n"
            f"انتخاب کنید:"
        )
        await message.answer(
            text,
            reply_markup=get_search_results_keyboard(movies, series),
            parse_mode="Markdown"
        )
    
    logger.info(f"کاربر {message.from_user.id} جستجو کرد: {query}")
