"""
Claude API client for Paper Planes PM Tool
"""
import os
import json
from typing import Dict, Any
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


class ClaudeClient:
    """Client for interacting with Claude API"""

    def __init__(self):
        # Try to load from Streamlit Secrets first (for cloud deployment)
        api_key = None
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and 'ANTHROPIC_API_KEY' in st.secrets:
                api_key = st.secrets['ANTHROPIC_API_KEY']
        except (ImportError, KeyError):
            pass

        # Fall back to environment variable
        if not api_key:
            api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in Streamlit secrets or environment variables")

        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"

    def generate_project_code(self, client_name: str, last_code: str = "2167") -> Dict[str, Any]:
        """
        Generate project code using Claude AI

        Args:
            client_name: Name of the client
            last_code: Last used project code (default: "2167")

        Returns:
            Dict with project_code, number, abbreviation, slug
        """
        prompt = f"""Последний используемый project code: {last_code}. Название клиента: {client_name}.

Сгенерируй новый project code в формате XXXX.AAA.client-slug, где:
- XXXX — порядковый номер (инкремент от {last_code})
- AAA — трехбуквенная аббревиатура названия клиента (UPPERCASE, кириллица или латиница)
- client-slug — slug названия клиента (lowercase с дефисами)

Верни JSON:
{{
  "project_code": "XXXX.AAA.client-slug",
  "number": XXXX,
  "abbreviation": "AAA",
  "slug": "client-slug"
}}"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=0.3,
                system="Ты — система генерации project codes для Paper Planes консалтингового агентства. Отвечай ТОЛЬКО валидным JSON, без лишнего текста.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extract JSON from response
            response_text = message.content[0].text
            result = json.loads(response_text)

            return result

        except Exception as e:
            raise Exception(f"Error generating project code: {str(e)}")

    def extract_contract_data(self, contract_text: str) -> Dict[str, Any]:
        """
        Extract structured data from contract text using Claude AI

        Args:
            contract_text: Full text of the contract

        Returns:
            Dict with budget, payment_stages, duration, deliverables, methodologies, confidence_score
        """
        prompt = f"""Ты — эксперт по анализу консалтинговых договоров. Твоя задача — ТОЧНО извлечь все данные из договора.

**КРИТИЧЕСКИ ВАЖНО:**
1. Извлекай ТОЧНЫЕ числа из текста договора
2. Различай "с НДС" и "без НДС"
3. Извлеки ВСЕ пункты технического задания/результаты работы
4. Для каждого пункта ТЗ определи применимые методологии

**ИНСТРУКЦИИ ПО ИЗВЛЕЧЕНИЮ:**

**1. ФИНАНСЫ (budget):**
- `total` — ИТОГОВАЯ стоимость договора (ищи "стоимость услуг", "цена договора", "общая стоимость")
- Если видишь "с НДС" → vat_included = true, если "без НДС" → false
- `vat_rate` — ставка НДС (обычно 5% или 20%, смотри что указано в договоре)
- `currency` — валюта (обычно RUB, USD, EUR)

**2. ЭТАПЫ ОПЛАТЫ (payment_stages):**
- Извлеки ВСЕ этапы с точными суммами
- `stage_number` — порядковый номер (1, 2, 3...)
- `amount` — сумма этапа (ТОЧНОЕ число из договора)
- `description` — описание этапа
- `trigger` — условие оплаты (например: "Подписание договора", "Сдача отчета")

**3. СРОКИ (duration):**
- `weeks` — длительность в неделях (посчитай из дат или срока)
- `start_date` — дата начала (формат YYYY-MM-DD)
- `end_date` — дата окончания (формат YYYY-MM-DD)

**4. РЕЗУЛЬТАТЫ РАБОТЫ (deliverables):**
- Извлеки КАЖДЫЙ пункт Технического задания / Результаты работы / Приложения
- Для каждого пункта укажи:
  - `number` — номер пункта (например: "3.1", "1", "А")
  - `title` — короткое название (из договора)
  - `description` — полное описание пункта
  - `suggested_methodologies` — список кодов БПМ/БПА которые подходят для этого пункта

**5. МЕТОДОЛОГИИ БПМ/БПА (methodologies):**
Определи какие методы исследования упоминаются в договоре:

**БПМ (Майнинг - сбор информации):**
- БПМ1 (Опросы) — если упоминаются "опросы", "анкетирование"
- БПМ2 (Интервью с клиентами) — если "глубинные интервью", "интервью с ЛПР", "интервью с клиентами", "IDI"
- БПМ3 (Оргинтервью) — если "интервью с персоналом", "опрос сотрудников", "организационные интервью", "анализ проблем"
- БПМ4 (Кабинетный анализ) — если "анализ рынка", "desk research", "вторичные данные"
- БПМ5 (Хронометраж) — если "наблюдение", "полевые исследования", "хронометраж", "измерение времени"
- БПМ6 (Тайник) — если "mystery shopping", "тайный покупатель"
- БПМ7 (Ассесмент) — если "ассесмент", "оценка компетенций"
- БПМ8 (Фокус-группа) — если "фокус-группы", "групповые интервью", "FGD"
- БПМ9 (Анализ база) — если "анализ клиентской базы", "анализ данных CRM", "анализ базы данных"
- БПМ10 (Анализ рынка) — если "анализ рынка", "рыночное исследование", "конкуренты"
- БПМ11 (Анализ производства) — если "анализ производства", "производственные процессы"

**БПА (Ассемблинг - консолидация в слайды):**
- БПА1 (Целевые клиентские группы (ЦКГ)) — если упоминается сегментация клиентов
- БПА2 (Приоритетные рынки) — если "оценка рынков", "5 сил Портера"
- БПА11 (Позиционирование) — если "позиционирование", "бренд", "УТП", "EVP"
- БПА12 (CJM/EJM) — если "Customer Journey Map", "Employee Journey Map", "карта пути клиента"
- БПА19 (Финмодель) — если "финансовая модель", "финмашина"
- БПА20 (Бизнес-модель) — если "бизнес-модель", "Canvas", "Остервальдер"

Для каждой методологии укажи:
- `code` — код БПМ/БПА
- `name` — название
- `quantity` — количество (если указано, например "20 интервью")
- `details` — детали из договора

**6. УРОВЕНЬ УВЕРЕННОСТИ (confidence_score):**
- 90-100% — все данные найдены четко
- 70-89% — большинство данных найдено
- 50-69% — часть данных отсутствует или неясна
- <50% — много неясностей

---

**ТЕКСТ ДОГОВОРА:**
{contract_text}

---

**ВЕРНИ ТОЛЬКО ВАЛИДНЫЙ JSON (без комментариев):**
{{
  "budget": {{
    "total": 1500000,
    "currency": "RUB",
    "vat_included": true,
    "vat_rate": 20
  }},
  "payment_stages": [
    {{
      "stage_number": 1,
      "amount": 500000,
      "description": "Аванс",
      "trigger": "Подписание договора"
    }}
  ],
  "duration": {{
    "weeks": 12,
    "start_date": "2025-01-15",
    "end_date": "2025-04-15"
  }},
  "deliverables": [
    {{
      "number": "3.1",
      "title": "Анализ рынка",
      "description": "Проведение комплексного анализа рынка медицинских информационных систем",
      "suggested_methodologies": ["БПМ4", "БПМ2"]
    }}
  ],
  "methodologies": [
    {{
      "code": "БПМ2",
      "name": "Интервью с клиентами",
      "quantity": 20,
      "details": "Интервью с ЛПР медицинских организаций"
    }}
  ],
  "confidence_score": 95
}}"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                temperature=0,
                system="Ты — эксперт по анализу консалтинговых договоров Paper Planes. Извлекаешь структурированные данные. Отвечай ТОЛЬКО валидным JSON. ОБЯЗАТЕЛЬНО извлеки ВСЕ пункты ТЗ и ВСЕ этапы оплаты из договора.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extract JSON from response
            response_text = message.content[0].text
            result = json.loads(response_text)

            return result

        except Exception as e:
            raise Exception(f"Error extracting contract data: {str(e)}")


# Singleton instance
_claude_client = None


def get_claude_client() -> ClaudeClient:
    """Get Claude client singleton"""
    global _claude_client
    if _claude_client is None:
        _claude_client = ClaudeClient()
    return _claude_client
