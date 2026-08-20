# 🚀 راهنمای مهاجرت به aiogram 3

## ✅ مهاجرت با موفقیت انجام شد!

---

## 📊 مقایسه قبل و بعد

### ساختار فایل‌ها

#### قبل (python-telegram-bot):
```
mother-bot/
└── bot.py (400+ خط کد در یک فایل)
```

#### بعد (aiogram 3):
```
mother-bot/
├── bot.py                 # نقطه شروع (40 خط)
├── config.py              # تنظیمات (20 خط)
├── .env                   # متغیرهای محیطی
├── requirements.txt       # وابستگی‌ها
└── handlers/              # پکیج handlerها
    ├── __init__.py       # صادرات routerها
    ├── start.py          # منوی اصلی (140 خط)
    └── bot_maker.py      # ساخت ربات با FSM (280 خط)
```

---

## 🔄 تغییرات کلیدی

### 1. Import ها

#### قبل:
```python
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters
```

#### بعد:
```python
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
```

---

### 2. ساخت کیبورد

#### قبل:
```python
keyboard = [
    [KeyboardButton("🤖 ساخت ربات")]
]
return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
```

#### بعد:
```python
keyboard = [
    [KeyboardButton(text="🤖 ساخت ربات")]
]
return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
```

**تفاوت:** پارامتر `text` برای KeyboardButton و `keyboard` برای ReplyKeyboardMarkup

---

### 3. Handler تعریف

#### قبل:
```python
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام")

application.add_handler(CommandHandler("start", start))
```

#### بعد:
```python
@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("سلام")

dp.include_router(router)
```

**تفاوت:** استفاده از decorator و Router

---

### 4. Inline Keyboard

#### قبل:
```python
keyboard = [
    [InlineKeyboardButton("متن", callback_data="data")]
]
reply_markup = InlineKeyboardMarkup(keyboard)
```

#### بعد:
```python
keyboard = [
    [InlineKeyboardButton(text="متن", callback_data="data")]
]
reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
```

**تفاوت:** پارامتر `inline_keyboard` اجباری است

---

### 5. Callback Query

#### قبل:
```python
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

application.add_handler(CallbackQueryHandler(button_callback))
```

#### بعد:
```python
@router.callback_query(F.data == "some_data")
async def callback_handler(callback: CallbackQuery):
    await callback.answer()
    data = callback.data
```

**تفاوت:** استفاده از Magic Filter (`F`)

---

### 6. State Management

#### قبل (context.user_data):
```python
context.user_data['waiting_for_token'] = True
is_waiting = context.user_data.get('waiting_for_token', False)
```

#### بعد (FSM):
```python
# تعریف State
class BotCreation(StatesGroup):
    waiting_for_token = State()

# تنظیم State
await state.set_state(BotCreation.waiting_for_token)

# دریافت State
@router.message(StateFilter(BotCreation.waiting_for_token))
async def handle_token(message: Message, state: FSMContext):
    pass
```

**تفاوت:** FSM رسمی و قدرتمند‌تر

---

### 7. Message Filter

#### قبل:
```python
async def handle_message(update: Update, context):
    text = update.message.text
    if text == "🤖 ساخت ربات":
        ...

application.add_handler(MessageHandler(filters.TEXT, handle_message))
```

#### بعد:
```python
@router.message(F.text == "🤖 ساخت ربات")
async def handle_create_bot(message: Message):
    ...
```

**تفاوت:** Filter مستقیم در decorator

---

### 8. راه‌اندازی ربات

#### قبل:
```python
application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.run_polling()
```

#### بعد:
```python
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)
await dp.start_polling(bot)
```

**تفاوت:** Dispatcher جداگانه و async

---

## 🎯 ویژگی‌های جدید در aiogram 3

### 1. Magic Filter (`F`)

```python
# Filter برای متن
@router.message(F.text == "سلام")

# Filter برای callback_data
@router.callback_query(F.data == "button")

# Filter ترکیبی
@router.message(F.text.startswith("bot_type_"))

# Filter برای عکس
@router.message(F.photo)
```

### 2. Router System

```python
# ساخت Router برای هر بخش
start_router = Router()
bot_maker_router = Router()

# ثبت در Dispatcher
dp.include_router(start_router)
dp.include_router(bot_maker_router)
```

### 3. FSM قدرتمند

```python
class OrderStates(StatesGroup):
    waiting_product = State()
    waiting_quantity = State()
    waiting_address = State()

@router.message(StateFilter(OrderStates.waiting_product))
async def process_product(message: Message, state: FSMContext):
    await state.update_data(product=message.text)
    await state.set_state(OrderStates.waiting_quantity)
```

### 4. Middleware

```python
from aiogram import BaseMiddleware

class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        logger.info(f"Event: {event}")
        return await handler(event, data)

dp.message.middleware(LoggingMiddleware())
```

---

## 🗂️ توضیح فایل‌ها

### 📄 `bot.py` (نقطه شروع)

```python
# وظایف:
1. ساخت Bot و Dispatcher
2. ثبت Routerها
3. شروع Polling
4. مدیریت Logging
```

### ⚙️ `config.py` (تنظیمات)

```python
# شامل:
1. توکن ربات (از .env یا hard-coded)
2. انواع ربات (BOT_TYPES)
3. تنظیمات عمومی پروژه
```

### 📁 `handlers/__init__.py`

```python
# وظایف:
1. Import کردن routerها
2. Export کردن برای استفاده در bot.py
```

### 🏠 `handlers/start.py`

```python
# شامل:
1. دستور /start
2. دکمه‌های منوی اصلی:
   - 👤 حساب کاربری
   - 💰 کسب درآمد
   - 🤖 مدیریت ربات‌ها
   - 💬 پشتیبانی
   - 📋 قوانین
```

### 🤖 `handlers/bot_maker.py`

```python
# شامل:
1. FSM برای ساخت ربات (BotCreation)
2. دکمه "🤖 ساخت ربات"
3. انتخاب 6 نوع ربات
4. دریافت و اعتبارسنجی توکن
5. ذخیره ربات
6. نمایش لیست ربات‌ها
```

---

## 🔧 تنظیمات پیشرفته

### استفاده از Redis برای State

```bash
pip install redis
```

```python
from aiogram.fsm.storage.redis import RedisStorage

storage = RedisStorage.from_url('redis://localhost:6379/0')
dp = Dispatcher(storage=storage)
```

### افزودن دیتابیس

```bash
pip install sqlalchemy asyncpg
```

```python
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine('postgresql+asyncpg://user:pass@localhost/db')
```

---

## 🎓 مفاهیم کلیدی

### Router
- یک گروه از handlerها
- قابل تفکیک بر اساس قابلیت
- قابل ثبت در Dispatcher

### FSM (Finite State Machine)
- مدیریت حالت‌های مختلف کاربر
- ذخیره داده‌های موقت
- جریان کاری مشخص

### Magic Filter (`F`)
- نوشتن filter به صورت pythonic
- عملیات منطقی (`&`, `|`, `~`)
- دسترسی به فیلدهای nested

### Dispatcher
- مرکز اصلی routing
- مدیریت update ها
- اتصال به Bot

---

## 📈 مزایای aiogram 3

✅ **سریع‌تر**: async native  
✅ **ماژولارتر**: Router system  
✅ **تمیزتر**: Magic filters  
✅ **قدرتمندتر**: FSM پیشرفته  
✅ **راحت‌تر**: کد کمتر  
✅ **مستندتر**: مستندات عالی  

---

## 🧪 تست

```bash
python bot.py
```

### چک‌لیست:
- [x] دستور /start کار می‌کند
- [x] دکمه "🤖 ساخت ربات" تک‌سطری است
- [x] 6 نوع ربات نمایش داده می‌شود
- [x] FSM برای دریافت توکن کار می‌کند
- [x] اعتبارسنجی توکن درست است
- [x] لیست ربات‌ها نمایش داده می‌شود
- [x] تمام دکمه‌های بازگشت کار می‌کنند

---

## 📚 منابع

- [مستندات aiogram 3](https://docs.aiogram.dev/en/latest/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [GitHub aiogram](https://github.com/aiogram/aiogram)

---

## 🎉 تبریک!

مهاجرت با موفقیت انجام شد! ربات شما حالا:
- معماری تمیز و ماژولار دارد
- از FSM استفاده می‌کند
- سریع‌تر و قدرتمندتر است
- قابل توسعه و نگهداری بهتر است

---

سوالی داری؟ 😊
