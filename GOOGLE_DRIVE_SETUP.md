# Google Drive Integration Setup

PM Tool теперь поддерживает автоматическую синхронизацию проектов с Google Drive.

## Структура в Google Drive

При создании проекта автоматически создается следующая структура:

```
04-Engagement/
├── Правая группа/
│   └── 2169.CLI Название клиента/
│       ├── CLI.01-inbox/
│       ├── CLI.02-research/
│       ├── CLI.03-meetings/
│       ├── CLI.04-project-docs/
│       └── CLI.05-deliverables/
└── Левая группа/
    └── [аналогично]
```

## Настройка OAuth Credentials

### Шаг 1: Создание проекта в Google Cloud Console

1. Перейдите на https://console.cloud.google.com/
2. Создайте новый проект или выберите существующий
3. Название проекта: "Paper Planes PM Tool"

### Шаг 2: Включение Google Drive API

1. В меню слева выберите **APIs & Services** → **Library**
2. Найдите **Google Drive API**
3. Нажмите **Enable**

### Шаг 3: Настройка OAuth Consent Screen

1. В меню слева: **APIs & Services** → **OAuth consent screen**
2. Выберите **External** (если не корпоративный Google Workspace)
3. Заполните обязательные поля:
   - App name: "Paper Planes PM Tool"
   - User support email: [ваш email]
   - Developer contact: [ваш email]
4. Нажмите **Save and Continue**
5. На странице **Scopes** нажмите **Add or Remove Scopes**
6. Найдите и добавьте:
   - `https://www.googleapis.com/auth/drive.file`
7. Сохраните и продолжите
8. Добавьте **Test users** (ваш email)
9. Сохраните

### Шаг 4: Создание OAuth Client ID

1. В меню слева: **APIs & Services** → **Credentials**
2. Нажмите **+ Create Credentials** → **OAuth client ID**
3. Application type: **Desktop app**
4. Name: "Paper Planes PM Tool Desktop"
5. Нажмите **Create**
6. В появившемся окне нажмите **Download JSON**
7. Сохраните файл как `credentials.json` в корне проекта

### Шаг 5: Настройка .env файла

Создайте или обновите файл `.env` в корне проекта:

```bash
# Claude API
ANTHROPIC_API_KEY=sk-ant-xxx

# Google Drive (опционально, по умолчанию используются эти значения)
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_TOKEN_PATH=token.pickle
```

### Шаг 6: Первый запуск

1. Убедитесь что файл `credentials.json` находится в корне проекта
2. Запустите приложение: `streamlit run app.py`
3. При первом создании проекта откроется браузер для авторизации
4. Разрешите приложению доступ к Google Drive
5. После авторизации создастся файл `token.pickle` с токеном доступа

## Важные примечания

### Безопасность

- ⚠️ **НЕ коммитьте** `credentials.json` и `token.pickle` в git
- Эти файлы уже добавлены в `.gitignore`
- Храните credentials.json в безопасном месте

### Работа без Google Drive

Если Google Drive не настроен:
- Приложение будет работать нормально
- Проекты будут создаваться только в Obsidian Vault
- При создании проекта появится предупреждение, но процесс продолжится

### Права доступа

PM Tool использует scope `drive.file`, что означает:
- ✅ Доступ только к файлам, созданным самим приложением
- ❌ НЕТ доступа к другим файлам в вашем Google Drive
- ✅ Безопасно для личного и корпоративного использования

### Структура папок

Папка **04-Engagement** создается автоматически при первом использовании.

Внутри создаются две подпапки:
- **Правая группа** - для проектов правой группы
- **Левая группа** - для проектов левой группы

### Синхронизация

При создании проекта автоматически:
1. Создается структура папок в Obsidian Vault
2. Генерируется админшкала и PERT
3. Создается структура папок в Google Drive
4. Загружаются все файлы в Google Drive
5. Ссылка на папку сохраняется в БД

## Troubleshooting

### Ошибка: "credentials.json not found"

**Решение:** Скачайте credentials.json из Google Cloud Console (см. Шаг 4)

### Ошибка при первой авторизации

**Решение:**
- Убедитесь что ваш email добавлен в Test users
- Проверьте что Google Drive API включен

### Токен истек (token expired)

**Решение:**
- Удалите файл `token.pickle`
- При следующем запуске пройдите авторизацию заново

### Файлы не загружаются в GDrive

**Проверьте:**
- Наличие `credentials.json` и `token.pickle`
- Права доступа к Google Drive API
- Логи в консоли Streamlit

## Дополнительная информация

- [Google Drive API Documentation](https://developers.google.com/drive/api/guides/about-sdk)
- [OAuth 2.0 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)

---

**Создано:** 2025-10-24
**Версия:** 1.0
