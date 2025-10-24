"""
Initialize database with methodologies data
"""
from database.connection import get_db, init_db
from database.models import Methodology


# БПМ методологии (11 типов) - Майнинг (сбор информации)
BPM_METHODOLOGIES = [
    {
        "code": "БПМ1",
        "name": "Опросы",
        "category": "БПМ",
        "description": "Количественные исследования с большими выборками",
        "typical_effort_hours": 16,
        "requires_details": True
    },
    {
        "code": "БПМ2",
        "name": "Интервью с клиентами",
        "category": "БПМ",
        "description": "Качественные интервью с клиентами для выявления инсайтов",
        "typical_effort_hours": 24,
        "requires_details": True
    },
    {
        "code": "БПМ3",
        "name": "Оргинтервью",
        "category": "БПМ",
        "description": "Организационные интервью - анализ проблем через интервью с сотрудниками",
        "typical_effort_hours": 12,
        "requires_details": True
    },
    {
        "code": "БПМ4",
        "name": "Кабинетный анализ",
        "category": "БПМ",
        "description": "Desk research: анализ вторичных данных, отчетов, документации",
        "typical_effort_hours": 8,
        "requires_details": False
    },
    {
        "code": "БПМ5",
        "name": "Хронометраж",
        "category": "БПМ",
        "description": "Наблюдение и измерение временных затрат на процессы",
        "typical_effort_hours": 16,
        "requires_details": True
    },
    {
        "code": "БПМ6",
        "name": "Тайник",
        "category": "БПМ",
        "description": "Mystery shopping / Тайный покупатель",
        "typical_effort_hours": 12,
        "requires_details": True
    },
    {
        "code": "БПМ7",
        "name": "Ассесмент",
        "category": "БПМ",
        "description": "Оценка компетенций сотрудников и команды",
        "typical_effort_hours": 8,
        "requires_details": True
    },
    {
        "code": "БПМ8",
        "name": "Фокус-группа",
        "category": "БПМ",
        "description": "Групповая дискуссия для выявления коллективных мнений",
        "typical_effort_hours": 10,
        "requires_details": True
    },
    {
        "code": "БПМ9",
        "name": "Анализ база",
        "category": "БПМ",
        "description": "Анализ клиентской базы и данных CRM",
        "typical_effort_hours": 20,
        "requires_details": True
    },
    {
        "code": "БПМ10",
        "name": "Анализ рынка",
        "category": "БПМ",
        "description": "Исследование рыночной конъюнктуры и конкурентов",
        "typical_effort_hours": 16,
        "requires_details": True
    },
    {
        "code": "БПМ11",
        "name": "Анализ производства",
        "category": "БПМ",
        "description": "Исследование производственных процессов и мощностей",
        "typical_effort_hours": 12,
        "requires_details": True
    }
]

# БПА методологии (25 типов) - Ассемблинг (консолидация майнинга в выводы/слайды)
BPA_METHODOLOGIES = [
    {
        "code": "БПА1",
        "name": "Целевые клиентские группы (ЦКГ)",
        "category": "БПА",
        "description": "Сегментация и описание целевых клиентских групп",
        "typical_effort_hours": 8,
        "requires_details": True
    },
    {
        "code": "БПА2",
        "name": "Приоритетные рынки (Оценка по 5 силам Портера)",
        "category": "БПА",
        "description": "Оценка и приоритизация рынков",
        "typical_effort_hours": 6,
        "requires_details": True
    },
    {
        "code": "БПА3",
        "name": "Как сегменты",
        "category": "БПА",
        "description": "Сегментация рынка",
        "typical_effort_hours": 6,
        "requires_details": True
    },
    {
        "code": "БПА4",
        "name": "Как регионы",
        "category": "БПА",
        "description": "Региональная сегментация",
        "typical_effort_hours": 6,
        "requires_details": True
    },
    {
        "code": "БПА5",
        "name": "Целевой трафик-мэп (TM)",
        "category": "БПА",
        "description": "Карта целевого трафика",
        "typical_effort_hours": 8,
        "requires_details": True
    },
    {
        "code": "БПА6",
        "name": "Бизнес-процессы",
        "category": "БПА",
        "description": "Описание бизнес-процессов",
        "typical_effort_hours": 10,
        "requires_details": True
    },
    {
        "code": "БПА7",
        "name": "Кроссфункциональные процессы (КФП)",
        "category": "БПА",
        "description": "Кроссфункциональные процессы (например, выравнивание)",
        "typical_effort_hours": 10,
        "requires_details": True
    },
    {
        "code": "БПА8",
        "name": "Процессы функциональных колодцев",
        "category": "БПА",
        "description": "БП + примечание, например, CM, ОП, HR и т.п.",
        "typical_effort_hours": 8,
        "requires_details": True
    },
    {
        "code": "БПА9",
        "name": "Целевая Ассортиментная матрица (AM)",
        "category": "БПА",
        "description": "Ассортиментная матрица",
        "typical_effort_hours": 8,
        "requires_details": True
    },
    {
        "code": "БПА10",
        "name": "Ценовая политика (Цена)",
        "category": "БПА",
        "description": "Разработка ценовой политики",
        "typical_effort_hours": 8,
        "requires_details": True
    },
    {
        "code": "БПА11",
        "name": "Позиционирование (Бренд/УТП/EVP)",
        "category": "БПА",
        "description": "Позиционирование бренда и ценностное предложение",
        "typical_effort_hours": 10,
        "requires_details": True
    },
    {
        "code": "БПА12",
        "name": "CJM/EJM",
        "category": "БПА",
        "description": "Customer Journey Map / Employee Journey Map",
        "typical_effort_hours": 10,
        "requires_details": True
    },
    {
        "code": "БПА13",
        "name": "Оргструктура (ОС)",
        "category": "БПА",
        "description": "Оргструктура + примечание, например, ОМ, ОП, HR и т.п.",
        "typical_effort_hours": 6,
        "requires_details": True
    },
    {
        "code": "БПА14",
        "name": "Модель компетенций (МК)",
        "category": "БПА",
        "description": "Разработка модели компетенций",
        "typical_effort_hours": 8,
        "requires_details": True
    },
    {
        "code": "БПА15",
        "name": "Материалы поддержки продаж (МПП)",
        "category": "БПА",
        "description": "МПП, включая книгу продаж, скрипты и т.п.",
        "typical_effort_hours": 12,
        "requires_details": True
    },
    {
        "code": "БПА16",
        "name": "ИТ-стек (БТ и тп)",
        "category": "БПА",
        "description": "Описание ИТ-стека и бизнес-технологий",
        "typical_effort_hours": 6,
        "requires_details": True
    },
    {
        "code": "БПА17",
        "name": "Целевая модель данных (ЦМД)",
        "category": "БПА",
        "description": "Целевая модель данных",
        "typical_effort_hours": 10,
        "requires_details": True
    },
    {
        "code": "БПА18",
        "name": "Рычаги роста (Брейн)",
        "category": "БПА",
        "description": "Рычаги роста по доходам или расходам",
        "typical_effort_hours": 8,
        "requires_details": True
    },
    {
        "code": "БПА19",
        "name": "Финмодель (ФМ) или Финмашина",
        "category": "БПА",
        "description": "Финансовая модель или Финмашина",
        "typical_effort_hours": 16,
        "requires_details": True
    },
    {
        "code": "БПА20",
        "name": "Модель Остервальдера и Пинье (ОиП) или Бизнес-модель (БМ)",
        "category": "БПА",
        "description": "Бизнес-модель Остервальдера и Пинье или Бизнес-модель Canvas",
        "typical_effort_hours": 8,
        "requires_details": True
    },
    {
        "code": "БПА21",
        "name": "Бизнес-календари и Операционная система работ (ОСР)",
        "category": "БПА",
        "description": "Бизнес-календари и ОСР",
        "typical_effort_hours": 8,
        "requires_details": True
    },
    {
        "code": "БПА22",
        "name": "Должностные инструкции (ДИ) или папка сотрудника",
        "category": "БПА",
        "description": "Должностные инструкции или папка сотрудника",
        "typical_effort_hours": 8,
        "requires_details": True
    },
    {
        "code": "БПА23",
        "name": "Функциональная стратегия",
        "category": "БПА",
        "description": "Разработка функциональной стратегии",
        "typical_effort_hours": 10,
        "requires_details": True
    },
    {
        "code": "БПА24",
        "name": "Найм",
        "category": "БПА",
        "description": "Процессы и материалы найма",
        "typical_effort_hours": 6,
        "requires_details": True
    },
    {
        "code": "БПА25",
        "name": "Проведение обучения",
        "category": "БПА",
        "description": "Материалы и процессы обучения",
        "typical_effort_hours": 8,
        "requires_details": True
    }
]


def import_methodologies():
    """Import all methodologies into database"""
    db = get_db()

    try:
        # Check if already imported
        existing_count = db.query(Methodology).count()
        if existing_count > 0:
            print(f"⚠️ Database already contains {existing_count} methodologies. Skipping import.")
            return

        # Import БПМ
        for method_data in BPM_METHODOLOGIES:
            methodology = Methodology(**method_data)
            db.add(methodology)

        # Import БПА
        for method_data in BPA_METHODOLOGIES:
            methodology = Methodology(**method_data)
            db.add(methodology)

        db.commit()

        total = len(BPM_METHODOLOGIES) + len(BPA_METHODOLOGIES)
        print(f"✅ Imported {total} methodologies ({len(BPM_METHODOLOGIES)} БПМ + {len(BPA_METHODOLOGIES)} БПА)")

    except Exception as e:
        db.rollback()
        print(f"❌ Error importing methodologies: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Initialize database and import data
    print("Initializing database...")
    init_db()

    print("\nImporting methodologies...")
    import_methodologies()

    print("\n🎉 Database setup complete!")
