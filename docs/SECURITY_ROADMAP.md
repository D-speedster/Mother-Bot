# 🔒 Security Roadmap - نقشه راه امنیتی

این سند شامل موارد امنیتی است که در نسخه‌های آینده باید پیاده‌سازی شوند.

## ⚠️ مسائل فعلی و راه‌حل‌های آینده

### 1. Key Rotation (چرخش کلید رمزنگاری)

#### **مشکل فعلی:**
اگر کلید `FERNET_KEY` تغییر کند، تمام توکن‌های رمزشده در دیتابیس غیرقابل رمزگشایی می‌شوند.

#### **تأثیر:**
- از دست رفتن دسترسی به تمام ربات‌های ثبت‌شده
- نیاز به ثبت مجدد تمام ربات‌ها توسط کاربران

#### **راه‌حل پیشنهادی:**

##### **مرحله ۱: افزودن Key Version به Schema**

```sql
ALTER TABLE bots ADD COLUMN key_version INTEGER NOT NULL DEFAULT 1;
CREATE INDEX idx_bots_key_version ON bots(key_version);
```

##### **مرحله ۲: پشتیبانی از چند کلید همزمان**

```python
# config.py
ENCRYPTION_KEYS = {
    1: os.getenv('FERNET_KEY_V1'),  # کلید قدیمی (retired)
    2: os.getenv('FERNET_KEY_V2'),  # کلید فعال (active)
}
ACTIVE_KEY_VERSION = 2
```

##### **مرحله ۳: رمزگشایی با Try Multiple Keys**

```python
def decrypt_with_rotation(self, encrypted: str, key_version: int) -> str:
    """
    رمزگشایی با پشتیبانی از key rotation
    
    اگر key_version قدیمی باشد، ابتدا با کلید قدیمی رمزگشایی می‌کند،
    سپس با کلید جدید رمزنگاری می‌کند و در دیتابیس به‌روزرسانی می‌شود.
    """
    # 1. رمزگشایی با کلید مربوطه
    fernet = self._get_fernet(key_version)
    plaintext = fernet.decrypt(encrypted)
    
    # 2. اگر کلید قدیمی است، با کلید جدید رمزنگاری کن
    if key_version < ACTIVE_KEY_VERSION:
        new_encrypted = self.encrypt(plaintext)
        # به‌روزرسانی در دیتابیس (باید از repository فراخوانی شود)
        return plaintext, new_encrypted, ACTIVE_KEY_VERSION
    
    return plaintext, None, key_version
```

##### **مرحله ۴: Migration تدریجی (Lazy Migration)**

```python
async def get_bot_token(self, bot_telegram_id: int) -> str:
    """
    دریافت توکن با migration خودکار
    """
    bot = await self.repository.get_bot_by_telegram_id(bot_telegram_id)
    
    if not bot:
        raise ValueError(f"ربات یافت نشد")
    
    # رمزگشایی با key rotation
    plaintext, new_encrypted, new_version = self.encryption.decrypt_with_rotation(
        bot['token_encrypted'],
        bot['key_version']
    )
    
    # اگر migrate شد، دیتابیس را به‌روز کن
    if new_encrypted:
        await self.repository.update_token_and_key_version(
            bot['id'],
            new_encrypted,
            new_version
        )
    
    return plaintext
```

##### **مرحله ۵: Background Migration Task**

```python
async def migrate_all_tokens_to_new_key():
    """
    Migration دسته‌ای (برای production)
    """
    old_version = 1
    bots = await repository.get_bots_by_key_version(old_version)
    
    for bot in bots:
        try:
            # رمزگشایی با کلید قدیمی
            plaintext = old_fernet.decrypt(bot['token_encrypted'])
            
            # رمزنگاری با کلید جدید
            new_encrypted = new_fernet.encrypt(plaintext)
            
            # به‌روزرسانی
            await repository.update_token_and_key_version(
                bot['id'],
                new_encrypted,
                ACTIVE_KEY_VERSION
            )
            
            print(f"✅ Migrated bot {bot['id']}")
        except Exception as e:
            print(f"❌ Failed to migrate bot {bot['id']}: {e}")
```

#### **زمان‌بندی پیشنهادی:**
- **v2.0**: پشتیبانی از key_version در schema
- **v2.1**: پیاده‌سازی multi-key support
- **v2.2**: lazy migration
- **v2.3**: background migration task

---

### 2. Timing Attack Prevention

#### **وضعیت فعلی:**
Fernet خود در برابر timing attack مقاوم است، اما اگر در آینده چندین کلید را check کنیم، باید مراقب باشیم.

#### **راه‌حل:**
```python
import hmac

def constant_time_compare(a: str, b: str) -> bool:
    """مقایسه با زمان ثابت"""
    return hmac.compare_digest(a, b)
```

#### **زمان‌بندی:**
- **v2.1**: پیاده‌سازی همزمان با key rotation

---

### 3. Audit Logging برای دسترسی به توکن‌ها

#### **مشکل:**
هیچ log یا audit trail برای دسترسی به توکن‌های رمزگشایی‌شده وجود ندارد.

#### **راه‌حل:**
```sql
CREATE TABLE token_access_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bot_id INTEGER NOT NULL,
    accessed_by INTEGER NOT NULL,  -- user_id
    access_reason TEXT,
    accessed_at DATETIME NOT NULL,
    FOREIGN KEY (bot_id) REFERENCES bots(id)
);
```

```python
async def get_bot_token_with_audit(
    self,
    bot_telegram_id: int,
    accessed_by: int,
    reason: str
) -> str:
    """دریافت توکن با ثبت audit log"""
    token = await self.get_bot_token(bot_telegram_id)
    
    # ثبت در audit log
    await self.audit_repository.log_token_access(
        bot_telegram_id=bot_telegram_id,
        accessed_by=accessed_by,
        reason=reason
    )
    
    return token
```

#### **زمان‌بندی:**
- **v2.2**: پیاده‌سازی audit logging

---

### 4. Rate Limiting برای Decrypt Operations

#### **مشکل:**
هیچ محدودیتی برای تعداد تلاش‌های رمزگشایی وجود ندارد.

#### **راه‌حل:**
```python
from collections import defaultdict
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_attempts: int = 10, window: int = 60):
        self.max_attempts = max_attempts
        self.window = timedelta(seconds=window)
        self.attempts = defaultdict(list)
    
    def check_rate_limit(self, key: str) -> bool:
        now = datetime.utcnow()
        
        # حذف تلاش‌های قدیمی
        self.attempts[key] = [
            t for t in self.attempts[key]
            if now - t < self.window
        ]
        
        # بررسی محدودیت
        if len(self.attempts[key]) >= self.max_attempts:
            return False
        
        self.attempts[key].append(now)
        return True
```

#### **زمان‌بندی:**
- **v2.3**: پیاده‌سازی rate limiting

---

### 5. Secure Key Storage (Production)

#### **مشکل فعلی:**
کلید در `.env` ذخیره می‌شود که برای development مناسب است، اما برای production کافی نیست.

#### **راه‌حل‌های Production:**

1. **AWS Secrets Manager**
```python
import boto3

def get_encryption_key() -> str:
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='mother-bot/fernet-key')
    return response['SecretString']
```

2. **HashiCorp Vault**
```python
import hvac

def get_encryption_key() -> str:
    client = hvac.Client(url='https://vault.example.com')
    secret = client.secrets.kv.v2.read_secret_version(
        path='mother-bot/fernet-key'
    )
    return secret['data']['data']['key']
```

3. **Azure Key Vault**
```python
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

def get_encryption_key() -> str:
    credential = DefaultAzureCredential()
    client = SecretClient(
        vault_url="https://my-vault.vault.azure.net/",
        credential=credential
    )
    secret = client.get_secret("fernet-key")
    return secret.value
```

#### **زمان‌بندی:**
- **v3.0**: پشتیبانی از Cloud Key Management Systems

---

### 6. توکن‌های با Expiration

#### **مشکل:**
توکن‌ها بی‌نهایت معتبر هستند.

#### **راه‌حل:**
```python
from cryptography.fernet import Fernet
import time

def encrypt_with_ttl(self, plaintext: str, ttl: int = 86400) -> str:
    """
    رمزنگاری با TTL (Time To Live)
    
    Args:
        plaintext: متن خام
        ttl: مدت اعتبار به ثانیه (پیش‌فرض: 24 ساعت)
    """
    plaintext_bytes = plaintext.encode('utf-8')
    encrypted_bytes = self._fernet.encrypt_at_time(
        plaintext_bytes,
        current_time=int(time.time())
    )
    return encrypted_bytes.decode('utf-8')

def decrypt_with_ttl(self, encrypted: str, ttl: int = 86400) -> str:
    """رمزگشایی با بررسی TTL"""
    encrypted_bytes = encrypted.encode('utf-8')
    decrypted_bytes = self._fernet.decrypt(
        encrypted_bytes,
        ttl=ttl
    )
    return decrypted_bytes.decode('utf-8')
```

#### **زمان‌بندی:**
- **v2.4**: پیاده‌سازی TTL (اختیاری)

---

## 📊 اولویت‌بندی

| اولویت | مورد | نسخه هدف | تأثیر امنیتی |
|--------|------|----------|--------------|
| 🔴 بالا | Key Rotation | v2.0-v2.3 | Critical |
| 🟡 متوسط | Audit Logging | v2.2 | High |
| 🟡 متوسط | Rate Limiting | v2.3 | Medium |
| 🟢 پایین | TTL Support | v2.4 | Low |
| 🔴 بالا | Cloud KMS (Production) | v3.0 | Critical |

---

## 🧪 تست‌های امنیتی پیشنهادی

```python
# tests/security/test_encryption.py

async def test_key_rotation():
    """تست migration توکن‌ها به کلید جدید"""
    old_service = TokenEncryptionService(key=OLD_KEY)
    new_service = TokenEncryptionService(key=NEW_KEY)
    
    # رمزنگاری با کلید قدیمی
    encrypted = old_service.encrypt("test_token")
    
    # رمزگشایی و re-encryption
    plaintext = old_service.decrypt(encrypted)
    new_encrypted = new_service.encrypt(plaintext)
    
    # اطمینان از عملکرد صحیح
    assert new_service.decrypt(new_encrypted) == "test_token"

async def test_timing_attack_resistance():
    """تست مقاومت در برابر timing attack"""
    # این تست باید timing analysis انجام دهد
    pass

async def test_rate_limiting():
    """تست محدودیت تعداد تلاش"""
    # باید بعد از N تلاش، block کند
    pass
```

---

**آخرین به‌روزرسانی:** 2024  
**نسخه سند:** 1.0.0
