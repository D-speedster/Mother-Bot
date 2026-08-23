# Owner-Based Authorization Architecture

## 🏗️ معماری کلی

```
┌─────────────────────────────────────────────────────────────────┐
│                         Mother Bot                               │
│                                                                   │
│  User 79049016 → /newbot → bot_type: ai_image                   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Database: bots table                                     │   │
│  │  ─────────────────────────────────────────────────────────   │
│  │  id: 17                                                   │   │
│  │  owner_id: 79049016          ← ✅ مالکیت ذخیره شد        │   │
│  │  bot_telegram_id: 987654321                              │   │
│  │  username: my_ai_bot                                      │   │
│  │  bot_type: ai_image                                       │   │
│  │  token_encrypted: [encrypted]                            │   │
│  │  status: active                                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  BotRunner.start_bot(bot_id=17, owner_id=79049016)              │
│           ↓                                                       │
└───────────┼───────────────────────────────────────────────────────┘
            │
            ↓ Token + Context
┌───────────────────────────────────────────────────────────────────┐
│                    Child Bot Instance (Bot #17)                   │
│                                                                    │
│  Bot Instance:                                                    │
│  ├─ Token: [decrypted]                                           │
│  └─ bot["bot_context"] = {          ← ✅ Context ذخیره شد        │
│      "bot_id": 17,                                               │
│      "owner_id": 79049016,                                       │
│      "bot_type": "ai_image"                                      │
│    }                                                              │
│                                                                    │
│  Dispatcher:                                                      │
│  ├─ User Router (ai_image)                                       │
│  └─ Admin Router (ai_image_admin)                                │
│                                                                    │
│  Running State: POLLING                                           │
└───────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Authorization Flow

### Scenario 1: Owner Access ✅

```
┌─────────────────┐
│  User 79049016  │ (Owner)
└────────┬────────┘
         │
         │ /admin
         ↓
┌──────────────────────────────────────────────┐
│  Bot #17                                     │
│  Handler: cmd_admin()                        │
│                                              │
│  1. bot_context = message.bot.get(...)      │
│     → bot_id: 17                            │
│     → owner_id: 79049016                    │
│                                              │
│  2. user_id = message.from_user.id          │
│     → 79049016                              │
│                                              │
│  3. Check: user_id == owner_id?             │
│     → 79049016 == 79049016? YES ✅          │
│                                              │
│  4. Show Admin Panel                        │
└──────────────────────────────────────────────┘
         │
         │ Admin Panel
         ↓
┌─────────────────┐
│  User 79049016  │ ✅ Panel نمایش داده شد
└─────────────────┘
```

### Scenario 2: Non-Owner Access ⛔

```
┌─────────────────┐
│  User 12345678  │ (غیرمجاز)
└────────┬────────┘
         │
         │ /admin
         ↓
┌──────────────────────────────────────────────┐
│  Bot #17                                     │
│  Handler: cmd_admin()                        │
│                                              │
│  1. bot_context = message.bot.get(...)      │
│     → bot_id: 17                            │
│     → owner_id: 79049016                    │
│                                              │
│  2. user_id = message.from_user.id          │
│     → 12345678                              │
│                                              │
│  3. Check: user_id == owner_id?             │
│     → 12345678 == 79049016? NO ❌           │
│                                              │
│  4. Silent Return                           │
│     logger.warning("Unauthorized...")        │
│     return  ← هیچ پاسخی ارسال نمی‌شود      │
└──────────────────────────────────────────────┘
         │
         │ (Nothing)
         ↓
┌─────────────────┐
│  User 12345678  │ ⚠️ هیچ اتفاقی نیفتاد
└─────────────────┘  (Silent Failure)
```

---

## 🔄 Bot Context Propagation

### Runtime Initialization

```python
# services/runner.py
┌───────────────────────────────────────────────────────────┐
│  BotRunner._run_bot_task()                                │
│  ─────────────────────────────────────────────────────────│
│                                                            │
│  Input Parameters:                                        │
│  ├─ bot_id: 17                                           │
│  ├─ owner_id: 79049016                                   │
│  ├─ token: "123456789:ABC..."                           │
│  └─ bot_type: "ai_image"                                 │
│                                                            │
│  1. bot = Bot(token=token)                               │
│                                                            │
│  2. bot["bot_context"] = {                ← ✅ Store     │
│       "bot_id": 17,                                       │
│       "owner_id": 79049016,                              │
│       "bot_type": "ai_image"                             │
│     }                                                      │
│                                                            │
│  3. dp = Dispatcher(...)                                 │
│  4. dp.include_router(router)                            │
│  5. await dp.start_polling(bot)           ← Context      │
│                                              goes with    │
└───────────────────────────────────────────────────────────┘
                                                  │
                                                  ↓
┌───────────────────────────────────────────────────────────┐
│  Handler: cmd_admin(message, state)                       │
│  ─────────────────────────────────────────────────────────│
│                                                            │
│  1. bot_context = message.bot.get("bot_context", {})     │
│     ↓                                                      │
│     {                                       ← ✅ Retrieve │
│       "bot_id": 17,                                       │
│       "owner_id": 79049016,                              │
│       "bot_type": "ai_image"                             │
│     }                                                      │
│                                                            │
│  2. owner_id = bot_context.get("owner_id")               │
│  3. user_id = message.from_user.id                       │
│  4. if user_id != owner_id: return                       │
│                                                            │
└───────────────────────────────────────────────────────────┘
```

---

## 🎭 Multiple Bots Isolation

```
┌──────────────────────────────────────────────────────────────────┐
│                         Mother Bot                                │
│                                                                    │
│  ┌────────────────────┐         ┌────────────────────┐           │
│  │  Database Record   │         │  Database Record   │           │
│  │  ─────────────────│         │  ─────────────────│           │
│  │  id: 17            │         │  id: 18            │           │
│  │  owner_id: 79049016│         │  owner_id: 12345678│           │
│  │  bot_type: ai_image│         │  bot_type: ai_image│           │
│  └────────────────────┘         └────────────────────┘           │
│          │                               │                         │
└──────────┼───────────────────────────────┼─────────────────────────┘
           │                               │
           ↓                               ↓
┌──────────────────────┐       ┌──────────────────────┐
│   Bot Instance #17   │       │   Bot Instance #18   │
│   ─────────────────  │       │   ─────────────────  │
│   bot_context:       │       │   bot_context:       │
│   ├─ bot_id: 17      │       │   ├─ bot_id: 18      │
│   ├─ owner_id:       │       │   ├─ owner_id:       │
│   │   79049016       │       │   │   12345678       │
│   └─ bot_type:       │       │   └─ bot_type:       │
│      ai_image        │       │      ai_image        │
└──────────────────────┘       └──────────────────────┘
         │                               │
         │                               │
    User Access:                    User Access:
         │                               │
┌────────┴────────┐           ┌─────────┴────────┐
│  User 79049016  │           │  User 12345678   │
│  /admin         │           │  /admin          │
│  → ✅ Panel 17  │           │  → ✅ Panel 18   │
└─────────────────┘           └──────────────────┘
         ↓                               ↓
┌────────────────┐           ┌──────────────────┐
│  User 12345678 │           │  User 79049016   │
│  /admin        │           │  /admin          │
│  → ⛔ Silent   │           │  → ⛔ Silent     │
└────────────────┘           └──────────────────┘

✅ هر Bot فقط Owner خودش را می‌شناسد
⛔ Cross-Bot Access امکان‌پذیر نیست
```

---

## 🛡️ Security Layers

```
┌─────────────────────────────────────────────────────────┐
│              User Request: /admin                        │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Handler Entry                                  │
│  ─────────────────────────────────────────────────────── │
│  async def cmd_admin(message, state):                   │
│      # Handler registered in router                     │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 2: Context Retrieval                              │
│  ─────────────────────────────────────────────────────── │
│  bot_context = message.bot.get("bot_context", {})      │
│  owner_id = bot_context.get("owner_id")                 │
│  user_id = message.from_user.id                         │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 3: Ownership Check                                │
│  ─────────────────────────────────────────────────────── │
│  if user_id != owner_id:                                │
│      logger.warning("Unauthorized access")               │
│      return  ← ⛔ STOP HERE (Silent)                    │
└──────────────────────┬──────────────────────────────────┘
                       │ ✅ Authorized
                       ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 4: Business Logic                                 │
│  ─────────────────────────────────────────────────────── │
│  await state.clear()                                    │
│  await message.answer(text, reply_markup=...)           │
└─────────────────────────────────────────────────────────┘

⚠️ Security Properties:
1. ❌ No error message to user
2. ❌ No information disclosure
3. ✅ Logged for audit
4. ✅ Early return (minimal processing)
```

---

## 📊 Data Flow Comparison

### ❌ Old Approach (Admin IDs)

```
.env file
  ├─ AI_IMAGE_ADMIN_IDS=79049016,12345
  │
  ↓ Global Variable (shared across ALL bots)
  │
Handlers
  ├─ get_admin_ids() → [79049016, 12345]
  ├─ is_admin(user_id) → user_id in admin_ids
  │
  └─ ❌ Problem: همه AI Image Bot‌ها Admin IDs یکسانی دارند
     ❌ Problem: Owner یک Bot = Admin همه Bot‌ها
     ❌ Problem: Environment-based نه Database-based
```

### ✅ New Approach (Ownership)

```
Database (bots table)
  ├─ Bot #17: owner_id = 79049016
  ├─ Bot #18: owner_id = 12345678
  │
  ↓ Per-Bot Context (isolated)
  │
BotRunner
  ├─ Bot Instance #17: bot_context = {owner_id: 79049016}
  ├─ Bot Instance #18: bot_context = {owner_id: 12345678}
  │
  ↓ Runtime Context
  │
Handlers
  ├─ get bot_context from message.bot
  ├─ extract owner_id from context
  ├─ compare with message.from_user.id
  │
  └─ ✅ Advantage: هر Bot مالک خاص خودش را دارد
     ✅ Advantage: Isolation کامل بین Bot‌ها
     ✅ Advantage: Database-based نه ENV-based
```

---

## 🔄 Future Permission System

### Phase 1 (فعلی): Owner Only

```
┌────────────────────────────────┐
│  Bot #17                       │
│  owner_id: 79049016            │
│                                │
│  Access:                       │
│  ✅ User 79049016 → Full Admin│
│  ❌ All Others → No Access     │
└────────────────────────────────┘
```

### Phase 2 (آینده): Multi-Role

```
┌─────────────────────────────────────────┐
│  Bot #17                                │
│  ────────────────────────────────────── │
│  Permissions Table:                     │
│  ├─ User 79049016: OWNER                │
│  ├─ User 11111111: ADMIN                │
│  └─ User 22222222: MODERATOR            │
│                                          │
│  Access Matrix:                         │
│  ┌───────────┬───────┬───────┬─────────┐│
│  │ Action    │ Owner │ Admin │ Mod     ││
│  ├───────────┼───────┼───────┼─────────┤│
│  │ Delete Bot│  ✅   │  ❌   │  ❌     ││
│  │ Broadcast │  ✅   │  ✅   │  ❌     ││
│  │ View Stats│  ✅   │  ✅   │  ✅     ││
│  └───────────┴───────┴───────┴─────────┘│
└─────────────────────────────────────────┘
```

---

## 🚀 Implementation Order

```
1. Runner Context Setup
   ├─ Modify _run_bot_task() signature
   ├─ Add bot["bot_context"] = {...}
   └─ Pass owner_id from start methods
            │
            ↓
2. Authorization Functions
   ├─ Remove get_admin_ids()
   ├─ Remove is_admin()
   ├─ Add is_owner()
   └─ Rewrite check_access()
            │
            ↓
3. Handler Updates
   ├─ Update cmd_admin
   ├─ Update all Reply Keyboard handlers
   ├─ Update all Callback handlers
   └─ Update all FSM handlers
            │
            ↓
4. Service Integration
   ├─ Update MotherBotGateway
   └─ Pass bot_context to services (if needed)
            │
            ↓
5. Cleanup & Testing
   ├─ Remove AI_IMAGE_ADMIN_IDS
   ├─ Rewrite tests
   ├─ Integration testing
   └─ Regression testing
```

---

## 📝 Code Examples

### Runner Context Setup

```python
# services/runner.py
async def _run_bot_task(
    self, 
    bot_id: int, 
    token: str, 
    bot_type: str,
    owner_id: int  # ← ✅ اضافه شد
) -> None:
    bot = Bot(token=token)
    
    # ✅ Store context
    bot["bot_context"] = {
        "bot_id": bot_id,
        "owner_id": owner_id,
        "bot_type": bot_type
    }
    
    dp = Dispatcher(storage=MemoryStorage())
    # ... rest of code
```

### Handler Authorization

```python
# handlers/child_bots/ai_image_admin.py

def is_owner(user_id: int, bot_context: dict) -> bool:
    """بررسی Owner بودن کاربر"""
    owner_id = bot_context.get("owner_id")
    return user_id == owner_id


async def cmd_admin(message: Message, state: FSMContext):
    """Handler دستور /admin"""
    
    # ✅ Get context
    bot_context = message.bot.get("bot_context", {})
    
    # ✅ Check ownership
    if not is_owner(message.from_user.id, bot_context):
        logger.warning(
            f"Unauthorized admin access: user {message.from_user.id} "
            f"tried to access bot owned by {bot_context.get('owner_id')}"
        )
        return  # ⛔ Silent failure
    
    # ✅ Authorized - show panel
    await state.clear()
    text = "🛠 **پنل مدیریت AI Image**\n\n..."
    await message.answer(
        text,
        reply_markup=get_admin_main_keyboard(),
        parse_mode="Markdown"
    )
```

---

## ✅ Validation Checklist

- [x] Database schema supports ownership (فیلد owner_id موجود است)
- [x] Repository methods ownership-aware هستند
- [x] Bot creation flow owner_id را ذخیره می‌کند
- [x] Bot runtime می‌تواند context ذخیره کند (bot.set)
- [x] Handlers می‌توانند context بخوانند (message.bot.get)
- [x] Silent failure approach امنیت کافی دارد
- [x] Multiple bots isolation ممکن است
- [x] Rollback plan وجود دارد

**✅ طراحی تأیید شده و آماده Implementation است.**
