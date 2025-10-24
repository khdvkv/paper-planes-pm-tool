# ✈️ Paper Planes PM Tool

**Система управления проектами для Paper Planes консалтингового агентства**

Построено с использованием **"vibe-coding"** подхода — весь код сгенерирован с помощью Claude Code (Anthropic).

---

## 🎯 Возможности MVP

- ✅ **Создание проектов** с AI генерацией project code
- ✅ **Таблица всех проектов** с фильтрами и поиском
- ✅ **База данных** (SQLite) с 4 таблицами
- ✅ **36 методологий** БПМ/БПА импортированы
- ✅ **Claude API интеграция** для AI обработки
- ✅ **Streamlit UI** — простой и быстрый интерфейс

---

## 🚀 Быстрый старт (5 минут)

### Шаг 1: Клонировать репозиторий (или перейти в папку)

```bash
cd paper-planes-pm-tool
```

### Шаг 2: Создать виртуальное окружение

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### Шаг 3: Установить зависимости

```bash
pip install -r requirements.txt
```

### Шаг 4: Настроить переменные окружения

```bash
# Копировать .env.example в .env
cp .env.example .env

# Отредактировать .env и добавить ваш Anthropic API key
# ANTHROPIC_API_KEY=sk-ant-api03-ваш-ключ-здесь
```

**Где получить Anthropic API key:**
1. Перейти на https://console.anthropic.com
2. API Keys → Create Key
3. Скопировать ключ (начинается с `sk-ant-api03-`)

### Шаг 5: Инициализировать базу данных

```bash
python database/init_data.py
```

**Вы должны увидеть:**
```
✅ Database initialized successfully!
✅ Imported 36 methodologies (11 БПМ + 25 БПА)
🎉 Database setup complete!
```

### Шаг 6: Запустить приложение

```bash
streamlit run app.py
```

**Приложение откроется в браузере:** `http://localhost:8501`

---

## 📦 Структура проекта

```
paper-planes-pm-tool/
├── app.py                  # Главный Streamlit файл
├── requirements.txt        # Зависимости Python
├── .env.example           # Пример конфигурации
├── .env                   # Ваша конфигурация (не в git)
├── pm_tool.db            # SQLite база данных (создается автоматически)
│
├── api/
│   ├── __init__.py
│   └── claude_client.py   # Claude API клиент
│
├── database/
│   ├── __init__.py
│   ├── models.py          # SQLAlchemy модели
│   ├── connection.py      # Подключение к БД
│   └── init_data.py       # Импорт методологий
│
├── pages/                 # Будущие страницы Streamlit
├── utils/                 # Утилиты
└── data/                  # Данные (CSV, JSON)
```

---

## 🛠️ Используемые технологии

**Stack:**
- **Backend:** Python 3.9+
- **UI:** Streamlit 1.29
- **Database:** SQLite (для локальной разработки) → PostgreSQL (для production)
- **ORM:** SQLAlchemy
- **AI:** Anthropic Claude 3.5 Sonnet

**Подход:**
- **"Vibe-coding"** — весь код сгенерирован через Claude Code
- **No-code mindset** — минимум ручного программирования
- **AI-first** — Claude делает всю рутинную работу

---

## 📊 Что делает приложение

### 1. Создание проекта

1. Заполняете форму (название, клиент, даты)
2. Нажимаете "Сгенерировать project code"
3. **Claude AI генерирует** уникальный код в формате `XXXX.AAA.client-slug`
4. Сохраняете проект в базу

**Пример:** `МедIQ` → `2168.MED.mediq`

### 2. Просмотр всех проектов

- Таблица с фильтрами
- Поиск по названию/клиенту
- Фильтр по статусу (draft, active, completed)
- Сортировка

### 3. Статистика

- Общее количество проектов
- Разбивка по статусам
- (Графики будут добавлены в V2)

---

## 🔑 Конфигурация (.env)

```bash
# Anthropic Claude API
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# Database
DATABASE_URL=sqlite:///./pm_tool.db

# App Settings
APP_NAME=Paper Planes PM Tool
APP_VERSION=1.0.0
DEBUG=True

# Authentication (будет добавлено в V2)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-this-password
```

---

## 🧪 Тестирование

### Создать тестовый проект:

1. Запустить приложение: `streamlit run app.py`
2. Перейти на страницу "➕ Создать проект"
3. Заполнить:
   - Название: `Тестовый проект`
   - Клиент: `Тестовая Компания`
   - Даты: выбрать любые
4. Сгенерировать project code
5. Создать проект
6. Проверить в таблице "📊 Все проекты"

---

## 🚢 Деплой (следующий шаг)

### Вариант 1: Railway (рекомендуется)

1. Создать аккаунт на https://railway.app
2. Подключить GitHub репозиторий
3. Добавить переменные окружения (ANTHROPIC_API_KEY)
4. Deploy автоматически
5. Получить URL: `https://your-app.railway.app`

### Вариант 2: Render

1. Создать аккаунт на https://render.com
2. New Web Service → подключить репозиторий
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `streamlit run app.py --server.port $PORT`
5. Deploy

### Вариант 3: Streamlit Cloud

1. https://streamlit.io/cloud
2. Deploy from GitHub
3. Бесплатный tier (1 app)

---

## 📈 Roadmap

### V1.0 (MVP) ✅
- [x] Создание проектов
- [x] AI генерация project code
- [x] Таблица проектов
- [x] База данных
- [x] Методологии БПМ/БПА

### V1.1 (Next)
- [ ] Step 2: Upload документов + AI извлечение данных
- [ ] Step 3: Выбор методологий (чек-листы)
- [ ] Google Drive интеграция
- [ ] Authentication (логин/пароль)

### V2.0
- [ ] Steps 4-7 (Fullkit, AI генерация, Search, Export)
- [ ] Admin dashboard (метрики, Кайдзен)
- [ ] Role-based access (сотрудники vs admin)
- [ ] PostgreSQL для production

---

## 🆘 Troubleshooting

### Ошибка: "ANTHROPIC_API_KEY not found"

**Решение:**
1. Проверьте, что файл `.env` создан (не `.env.example`)
2. Проверьте, что в `.env` есть строка: `ANTHROPIC_API_KEY=sk-ant-api03-...`
3. Перезапустите приложение

### Ошибка: "Module not found"

**Решение:**
```bash
# Убедитесь что виртуальное окружение активировано
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Переустановите зависимости
pip install -r requirements.txt
```

### База данных не инициализируется

**Решение:**
```bash
# Удалить старую базу
rm pm_tool.db

# Создать заново
python database/init_data.py
```

---

## 📞 Поддержка

**Вопросы по коду:**
- Создать issue в проекте
- Связаться с Сергеем Худовековым

**Anthropic Claude API:**
- Документация: https://docs.anthropic.com
- Console: https://console.anthropic.com

**Streamlit:**
- Документация: https://docs.streamlit.io
- Forum: https://discuss.streamlit.io

---

## 📄 Лицензия

© 2025 Paper Planes. Internal tool for team use.

---

## 🎉 Создано с помощью "Vibe-Coding"

Весь код этого приложения был сгенерирован с помощью **Claude Code** (Anthropic) в рамках "vibe-coding" подхода:

- 🤖 **AI написал код** — я только формулировал требования
- ⚡ **Разработка за 1 день** — вместо 2 недель
- 🎨 **Фокус на продукте** — не на синтаксисе

**Это будущее разработки!** 🚀

---

**Дата создания:** 2025-10-24
**Версия:** 1.0.0
**Автор:** Paper Planes Team (с помощью Claude Code)
