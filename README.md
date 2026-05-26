# ServiceDesk Telegram Bot

Telegram-бот для створення заявок у [ManageEngine ServiceDesk Plus](https://www.manageengine.com/products/service-desk/) через REST API v3.

## Можливості

- Покрокова форма створення заявки (email, тема, опис, пріоритет)
- Пріоритети завантажуються динамічно з вашого екземпляра SDP
- Прикріплення кількох фото до заявки
- Два режими доступу: **відкритий** (`general`) та **з паролем** (`restricted`)
- Автентифіковані користувачі зберігаються між перезапусками бота
- Готовий `systemd`-юніт для розгортання на Linux VPS

## Стек

| Компонент | Технологія |
|---|---|
| Мова | Python 3.11+ |
| Telegram | [aiogram](https://github.com/aiogram/aiogram) v3 |
| HTTP-клієнт | aiohttp |
| Конфігурація | python-dotenv |
| Розгортання | systemd |

## Структура проєкту

```
servicedesk-chat-bot/
├── bot.py                        # Точка входу
├── config.py                     # Конфігурація з .env
├── states.py                     # FSM-стани (aiogram)
├── keyboards.py                  # Inline-клавіатури
├── handlers/
│   ├── start.py                  # /start, /cancel, перевірка пароля
│   └── ticket.py                 # FSM-форма створення заявки
├── services/
│   └── sdp_api.py                # Клієнт ManageEngine SDP API v3
├── storage/
│   └── auth.py                   # Збереження авторизованих користувачів
├── systemd/
│   └── servicedesk-bot.service   # Шаблон systemd-юніта
├── .env.example
└── requirements.txt
```

## Вимоги

- Python 3.11 або новіший
- Доступ до ManageEngine ServiceDesk Plus з увімкненим REST API
- Technician Key (API-ключ) у SDP
- Telegram Bot Token від [@BotFather](https://t.me/BotFather)

## Встановлення

### 1. Клонування репозиторію

```bash
git clone https://github.com/gkfs-it/servicedesk-chat-bot.git
cd servicedesk-chat-bot
```

### 2. Віртуальне середовище та залежності

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Конфігурація

```bash
cp .env.example .env
nano .env
```

Заповніть усі змінні (опис нижче).

## Конфігурація (.env)

| Змінна | Обов'язкова | Опис |
|---|---|---|
| `BOT_TOKEN` | ✅ | Telegram Bot Token від @BotFather |
| `SDP_URL` | ✅ | URL вашого ServiceDesk Plus |
| `SDP_API_KEY` | ✅ | Technician Key з налаштувань SDP |
| `SDP_SSL_VERIFY` | — | `false` якщо самопідписаний SSL-сертифікат (за замовчуванням `true`) |
| `ACCESS_MODE` | — | `general` (відкритий) або `restricted` (з паролем, за замовчуванням `general`) |
| `ACCESS_PASSWORD` | — | Пароль доступу (тільки для `restricted`-режиму) |
| `MAX_PHOTOS` | — | Максимальна кількість фото на заявку (за замовчуванням `5`) |

### Отримання Telegram Bot Token

1. Відкрийте [@BotFather](https://t.me/BotFather) у Telegram
2. Надішліть команду `/newbot` і дотримуйтесь інструкцій
3. Скопіюйте отриманий токен у `BOT_TOKEN`

### Отримання Technician Key у ManageEngine SDP

1. Увійдіть у SDP як адміністратор
2. Перейдіть до **Admin → Technicians**
3. Відкрийте профіль технічного спеціаліста
4. Знайдіть розділ **API Key** → натисніть **Generate** (або скопіюйте наявний)

## Запуск

### Локально (для тестування)

```bash
source venv/bin/activate
python bot.py
```

### Продакшн — через systemd

1. Відредагуйте шаблон юніта:

```bash
nano systemd/servicedesk-bot.service
```

Замініть `YOUR_LINUX_USER` та шляхи `/path/to/servicedesk-chat-bot` на реальні значення.

2. Встановіть і запустіть сервіс:

```bash
sudo cp systemd/servicedesk-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable servicedesk-bot
sudo systemctl start servicedesk-bot
```

3. Перевірте статус:

```bash
sudo systemctl status servicedesk-bot
sudo journalctl -u servicedesk-bot -f
```

## Режими доступу

### `general` — відкритий

Будь-який Telegram-користувач може одразу створювати заявки.

```env
ACCESS_MODE=general
```

### `restricted` — з паролем

При першому `/start` бот запитає код доступу. Після успішного введення Telegram ID зберігається у `authenticated_users.json` — повторно вводити пароль після перезапуску бота не потрібно.

```env
ACCESS_MODE=restricted
ACCESS_PASSWORD=your_secret_code
```

## Процес створення заявки

```
/start
  └── [restricted] Введіть пароль
        └── ✅ Доступ надано
  
📝 Створити заявку
  ├── Крок 1 — Email користувача (як у ServiceDesk)
  ├── Крок 2 — Тема заявки
  ├── Крок 3 — Опис проблеми
  ├── Крок 4 — Пріоритет (завантажується з SDP)
  ├── Фото   — До MAX_PHOTOS фото (опціонально)
  └── Підтвердження → ✅ Заявку #N створено
```

## Команди бота

| Команда | Дія |
|---|---|
| `/start` | Початок роботи / перевірка пароля |
| `/cancel` | Скасування поточної дії |

## Вирішення проблем

**Помилка `4001` на полі `requester`** — переконайтесь, що введений email точно збігається з email у профілі користувача в SDP (`Admin → Requesters`).

**Помилка `4001` на полі `priority`** — бот завантажує пріоритети динамічно з SDP. Якщо список порожній, перевірте що API-ключ має права на читання (`GET /api/v3/priorities`).

**`SDP_SSL_VERIFY=false`** — використовуйте лише якщо SDP працює з самопідписаним сертифікатом у внутрішній мережі.

**Бот не відповідає після перезапуску** — перевірте логи: `sudo journalctl -u servicedesk-bot -n 50`

## Автор

Цей проєкт написано за допомогою **[Claude Code](https://claude.ai/code)** — AI-інструменту від [Anthropic](https://www.anthropic.com).

Весь код — від архітектури до інтеграції з ManageEngine API — створено у діалозі з Claude безпосередньо в терміналі, без жодного рядка написаного вручну.

Окрема подяка команді **Anthropic** за Claude Code — інструмент, який перетворює ідею на працюючий продукт швидше, ніж встигаєш випити каву. Це не просто автодоповнення — це повноцінний інженер поруч, який розуміє контекст, ловить помилки та пропонує рішення.

> *Built with Claude Code — [claude.ai/code](https://claude.ai/code)*

## Ліцензія

MIT
