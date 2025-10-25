"""
Paper Planes PM Tool - Streamlit Application
Main entry point for the web application
"""
import streamlit as st
import pandas as pd
import io
import yaml
from datetime import datetime, date
import streamlit_authenticator as stauth
from database.connection import get_db, init_db
from database.models import (
    Project, Methodology, ProjectDocument, PaymentStage, MethodologySelection,
    Deliverable, TaskDependency, SetupChecklistItem, SETUP_CHECKLIST_ITEMS, SETUP_APPROVERS
)
from database.init_data import import_methodologies
from api.claude_client import get_claude_client
from api.project_generator import get_project_generator
from api.google_drive_client import get_google_drive_client

# Page configuration
st.set_page_config(
    page_title="Paper Planes PM Tool",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database on first run
@st.cache_resource
def initialize_database():
    """Initialize database and import methodologies"""
    init_db()
    import_methodologies()
    return True

# Load authentication config
@st.cache_resource
def load_auth_config():
    """Load authentication configuration"""
    # Try to load from Streamlit Secrets first (for cloud deployment)
    try:
        if hasattr(st, 'secrets') and 'credentials' in st.secrets:
            # Convert st.secrets to dict format expected by streamlit-authenticator
            config = {
                'credentials': st.secrets['credentials'].to_dict(),
                'cookie': st.secrets.get('cookie', {
                    'expiry_days': 30,
                    'key': 'paperplanes_auth_key',
                    'name': 'paperplanes_auth_cookie'
                }).to_dict() if hasattr(st.secrets.get('cookie', {}), 'to_dict') else st.secrets.get('cookie', {
                    'expiry_days': 30,
                    'key': 'paperplanes_auth_key',
                    'name': 'paperplanes_auth_cookie'
                }),
                'preauthorized': st.secrets.get('preauthorized', {'emails': []}).to_dict() if hasattr(st.secrets.get('preauthorized', {}), 'to_dict') else st.secrets.get('preauthorized', {'emails': []})
            }
            return config
    except (ImportError, KeyError, AttributeError):
        pass

    # Fall back to config.yaml file
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=yaml.SafeLoader)
    return config

# Initialize
initialize_database()


def main():
    """Main application"""

    # Header
    st.title("✈️ Paper Planes PM Tool")
    st.markdown("### Управление проектами Paper Planes")

    # Sidebar
    with st.sidebar:
        st.header("Навигация")
        page = st.radio(
            "Выберите страницу:",
            ["📊 Все проекты", "➕ Создать проект", "📈 Статистика"],
            label_visibility="collapsed"
        )

    # Route to pages
    if page == "📊 Все проекты":
        show_all_projects()
    elif page == "➕ Создать проект":
        show_create_project()
    elif page == "📈 Статистика":
        show_statistics()


def show_all_projects():
    """Show all projects table with extended registry information"""
    st.header("📊 Все проекты")

    # Get projects from database
    db = get_db()
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    db.close()

    if not projects:
        st.info("📭 Пока нет проектов. Создайте первый проект!")
        return

    # Convert to DataFrame with extended columns
    data = []
    for proj in projects:
        # Calculate days remaining if dates available
        days_to_end = None
        if proj.contract_project_end_date:
            from datetime import date
            days_to_end = (proj.contract_project_end_date - date.today()).days

        data.append({
            "Код": proj.project_code,
            "Название": proj.name,
            "Клиент": proj.client,
            "Группа": "🟢 Правая" if proj.group == "right" else "🔵 Левая",
            "Статус": proj.status,
            "Старт": proj.start_date.strftime("%d.%m.%Y") if proj.start_date else "",
            "Окончание": proj.contract_project_end_date.strftime("%d.%m.%Y") if proj.contract_project_end_date else proj.end_date.strftime("%d.%m.%Y"),
            "Осталось дней": days_to_end if days_to_end is not None else None,
            "Недель": proj.duration_weeks or proj.phase_duration_weeks,
            "📁 Папка": proj.google_drive_folder_url if proj.google_drive_folder_url else None,
            "📄 Админшкала": proj.adminscale_url if proj.adminscale_url else None,
            "📊 PERT": proj.pert_url if proj.pert_url else None,
            "🗺️ Карта проблем": proj.problem_map_url if proj.problem_map_url else None,
            "_project_id": proj.id  # Hidden column for selection
        })

    df = pd.DataFrame(data)

    # Filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        search = st.text_input("🔍 Поиск по названию или клиенту")
    with col2:
        status_filter = st.multiselect(
            "Статус",
            ["draft", "setup", "active", "completed", "archived"],
            default=["setup", "active"]
        )
    with col3:
        group_filter = st.multiselect(
            "Группа",
            ["🟢 Правая", "🔵 Левая"],
            default=["🟢 Правая", "🔵 Левая"]
        )
    with col4:
        st.metric("Всего проектов", len(projects))

    # Apply filters
    df_filtered = df.copy()
    if search:
        df_filtered = df_filtered[
            df_filtered["Название"].str.contains(search, case=False, na=False) |
            df_filtered["Клиент"].str.contains(search, case=False, na=False)
        ]
    if status_filter:
        df_filtered = df_filtered[df_filtered["Статус"].isin(status_filter)]
    if group_filter:
        df_filtered = df_filtered[df_filtered["Группа"].isin(group_filter)]

    st.caption(f"Показано проектов: {len(df_filtered)} из {len(df)}")

    # Display table with links
    st.dataframe(
        df_filtered.drop(columns=["_project_id"]),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Код": st.column_config.TextColumn(
                "Код проекта",
                width="medium",
                help="Уникальный код проекта"
            ),
            "Название": st.column_config.TextColumn(
                "Название",
                width="large"
            ),
            "Группа": st.column_config.TextColumn(
                "Группа",
                width="small"
            ),
            "Статус": st.column_config.TextColumn(
                "Статус",
                width="small",
                help="Текущий статус проекта"
            ),
            "Осталось дней": st.column_config.NumberColumn(
                "Дней до конца",
                width="small",
                help="Дней до договорной даты окончания"
            ),
            "Недель": st.column_config.NumberColumn(
                "Недель",
                width="small",
                help="Длительность проекта в неделях"
            ),
            "📁 Папка": st.column_config.LinkColumn(
                "📁 Папка",
                width="small",
                help="Ссылка на папку в Google Drive",
                display_text="Открыть"
            ),
            "📄 Админшкала": st.column_config.LinkColumn(
                "📄 Админшкала",
                width="small",
                help="Ссылка на админшкалу проекта",
                display_text="Открыть"
            ),
            "📊 PERT": st.column_config.LinkColumn(
                "📊 PERT",
                width="small",
                help="Ссылка на PERT-диаграмму",
                display_text="Открыть"
            ),
            "🗺️ Карта проблем": st.column_config.LinkColumn(
                "🗺️ Карта",
                width="small",
                help="Ссылка на карту проблем",
                display_text="Открыть"
            )
        }
    )


def show_create_project():
    """Show create project form with multi-step process"""
    st.header("➕ Создать новый проект")

    # Initialize session state for multi-step form
    if "create_step" not in st.session_state:
        st.session_state.create_step = 1
    if "project_data" not in st.session_state:
        st.session_state.project_data = {}
    if "extracted_data" not in st.session_state:
        st.session_state.extracted_data = None

    # Progress indicator
    st.progress((st.session_state.create_step - 1) / 3)
    st.caption(f"Шаг {st.session_state.create_step} из 4")

    # Step 1: Basic Information
    if st.session_state.create_step == 1:
        show_step1_basic_info()

    # Step 2: Upload Contract & AI Extraction
    elif st.session_state.create_step == 2:
        show_step2_contract_upload()

    # Step 3: Project Planning
    elif st.session_state.create_step == 3:
        show_step3_planning()

    # Step 4: Review & Create
    elif st.session_state.create_step == 4:
        show_step4_review_create()


def show_step1_basic_info():
    """Step 1: Basic project information"""
    st.subheader("Шаг 1: Основная информация")

    col1, col2 = st.columns(2)

    with col1:
        project_name = st.text_input(
            "Название проекта *",
            value=st.session_state.project_data.get("name", ""),
            placeholder="Например: Разработка стратегии продвижения МИС",
            help="Полное название проекта"
        )

        client_name = st.text_input(
            "Клиент *",
            value=st.session_state.project_data.get("client", ""),
            placeholder="Например: МедIQ",
            help="Название компании клиента"
        )

        start_date = st.date_input(
            "Дата старта *",
            value=st.session_state.project_data.get("start_date", datetime.now().date()),
            help="Дата начала проекта"
        )

        # Group selection
        group = st.selectbox(
            "Группа *",
            options=["left", "right"],
            format_func=lambda x: "Левая группа" if x == "left" else "Правая группа",
            index=0 if st.session_state.project_data.get("group", "left") == "left" else 1,
            help="Центр прибыли, к которому относится проект"
        )

    with col2:
        end_date = st.date_input(
            "Дата окончания *",
            value=st.session_state.project_data.get("end_date", datetime.now().date()),
            help="Планируемая дата завершения"
        )

        # Project type selection
        project_type = st.selectbox(
            "Тип проекта *",
            options=["new", "existing"],
            format_func=lambda x: "Новый проект" if x == "new" else "Существующий проект",
            index=0 if st.session_state.project_data.get("project_type", "new") == "new" else 1,
            help="Новый проект или продолжение существующего"
        )

        st.markdown("**Project Code**")

        # Generate project code button
        if st.button("🔄 Сгенерировать project code", use_container_width=True):
            if client_name:
                with st.spinner("Генерирую project code с помощью AI..."):
                    try:
                        db = get_db()
                        last_project = db.query(Project).order_by(Project.id.desc()).first()
                        db.close()

                        last_code = last_project.project_code.split(".")[0] if last_project else "2167"

                        claude_client = get_claude_client()
                        result = claude_client.generate_project_code(client_name, last_code)

                        st.session_state.project_data["project_code"] = result["project_code"]
                        st.success(f"✅ Сгенерирован: {result['project_code']}")
                    except Exception as e:
                        st.error(f"❌ Ошибка: {str(e)}")
            else:
                st.warning("⚠️ Введите название клиента")

        # Show generated code
        if "project_code" in st.session_state.project_data:
            st.info(f"📌 **Project Code:** `{st.session_state.project_data['project_code']}`")

    st.markdown("---")

    # Next button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("➡️ Далее", type="primary", use_container_width=True):
            # Validation
            if not all([project_name, client_name, start_date, end_date]):
                st.error("⚠️ Заполните все обязательные поля")
                return

            if end_date < start_date:
                st.error("⚠️ Дата окончания должна быть позже даты старта")
                return

            if "project_code" not in st.session_state.project_data:
                st.error("⚠️ Сгенерируйте project code")
                return

            # Save data
            st.session_state.project_data.update({
                "name": project_name,
                "client": client_name,
                "start_date": start_date,
                "end_date": end_date,
                "group": group,
                "project_type": project_type
            })

            # Move to next step
            st.session_state.create_step = 2
            st.rerun()


def show_step2_contract_upload():
    """Step 2: Upload contract and extract data with AI"""
    st.subheader("Шаг 2: Загрузка договора")

    st.info("📝 Вставьте текст договора в поле ниже или загрузите файл (опционально)")

    # Text input field (primary method)
    st.markdown("### 📄 Текст договора")
    contract_text_input = st.text_area(
        "Вставьте полный текст договора:",
        value=st.session_state.project_data.get("contract_text_input", ""),
        height=300,
        placeholder="Скопируйте и вставьте сюда текст договора...",
        help="Вставьте текст договора сюда. AI будет извлекать данные из этого поля."
    )

    # File upload (required, for Google Drive storage)
    st.markdown("---")
    st.markdown("### 📎 Файл договора")
    st.caption("Файл будет сохранен в Google Drive, но AI обработает текст из поля выше")

    uploaded_file = st.file_uploader(
        "Выберите файл для сохранения в архиве:",
        type=["pdf", "txt", "docx"],
        help="Файл договора для сохранения в архиве проекта (обязательно)"
    )

    # Save filename if uploaded
    if uploaded_file:
        st.session_state.project_data["contract_filename"] = uploaded_file.name
        st.success(f"✅ Файл {uploaded_file.name} будет сохранен в архиве проекта")

    # Proposal upload
    st.markdown("---")
    st.markdown("### 📄 Коммерческое предложение (КП)")
    st.caption("PDF файл коммерческого предложения для архива")

    proposal_file = st.file_uploader(
        "Выберите файл КП:",
        type=["pdf"],
        help="Опционально: файл коммерческого предложения",
        key="proposal_uploader"
    )

    if proposal_file:
        st.session_state.project_data["proposal_filename"] = proposal_file.name
        st.success(f"✅ КП {proposal_file.name} будет сохранен в архиве")

    # Sales notes - Granola recording link
    st.markdown("---")
    st.markdown("### 📝 Записи встреч по продаже")
    st.caption("Ссылка на запись встречи в Granola (или другом инструменте транскрипции)")

    sales_notes_url = st.text_input(
        "Вставьте ссылку на запись встречи:",
        value=st.session_state.project_data.get("sales_notes_url", ""),
        placeholder="https://granola.ai/recording/...",
        help="Ссылка на запись встречи (Granola, Otter.ai и т.д.)",
        key="sales_notes_url_input"
    )

    if sales_notes_url:
        st.session_state.project_data["sales_notes_url"] = sales_notes_url

    # Transcript text area
    st.markdown("#### Транскрипция встречи")
    st.caption("Скопируйте и вставьте транскрипцию из Granola сюда")

    sales_transcript = st.text_area(
        "Вставьте транскрипцию:",
        value=st.session_state.project_data.get("sales_transcript", ""),
        height=250,
        placeholder="Вставьте текст транскрипции встречи...\n\nНапример:\n[00:00] Иван: Добрый день...\n[00:15] Клиент: Здравствуйте, у нас есть задача...",
        help="Полная транскрипция встречи для обработки AI",
        key="sales_transcript_input"
    )

    if sales_transcript:
        st.session_state.project_data["sales_transcript"] = sales_transcript
        # Save combined data to sales_notes
        notes_content = ""
        if sales_notes_url:
            notes_content += f"Запись встречи: {sales_notes_url}\n\n"
        notes_content += sales_transcript
        st.session_state.project_data["sales_notes"] = notes_content

    # Project specifics
    st.markdown("---")
    st.markdown("### 🎯 Особенности проекта (от продавца)")
    st.caption("Важные детали, контекст, риски, специфика клиента")

    project_specifics = st.text_area(
        "Опишите особенности проекта:",
        value=st.session_state.project_data.get("project_specifics", ""),
        height=150,
        placeholder="Например:\n- Клиент очень требовательный к срокам\n- Есть риск расширения scope\n- Важно учесть политику безопасности...",
        help="Детали проекта которые важно знать команде",
        key="project_specifics_input"
    )

    if project_specifics:
        st.session_state.project_data["project_specifics"] = project_specifics

    st.markdown("---")

    # AI extraction button
    if contract_text_input:
        if st.button("🤖 Извлечь данные с помощью AI", type="primary", use_container_width=True):
            with st.spinner("Claude анализирует договор... Это может занять 30-60 секунд"):
                try:
                    claude_client = get_claude_client()
                    extracted = claude_client.extract_contract_data(contract_text_input)

                    st.session_state.extracted_data = extracted
                    st.session_state.project_data["contract_text"] = contract_text_input
                    st.session_state.project_data["contract_text_input"] = contract_text_input

                    st.success(f"✅ Данные извлечены! Уровень уверенности: {extracted.get('confidence_score', 0)}%")
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Ошибка AI извлечения: {str(e)}")
    else:
        st.warning("⚠️ Вставьте текст договора в поле выше для извлечения данных")

    # Show extracted data
    if st.session_state.extracted_data:
        st.markdown("### 📊 Извлеченные данные")

        data = st.session_state.extracted_data

        # Budget
        if "budget" in data:
            st.markdown("#### 💰 Финансы")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Бюджет", f"{data['budget']['total']:,.0f} {data['budget']['currency']}")
            with col2:
                st.metric("НДС", f"{data['budget']['vat_rate']}%" if data['budget'].get('vat_included') else "Без НДС")
            with col3:
                if "duration" in data and "weeks" in data["duration"]:
                    st.metric("Длительность", f"{data['duration']['weeks']} нед")

        # Payment stages
        if "payment_stages" in data and data["payment_stages"]:
            st.markdown("#### 💳 Этапы оплаты")
            stages_df = pd.DataFrame(data["payment_stages"])
            st.dataframe(stages_df, use_container_width=True, hide_index=True)

        # Deliverables (пункты ТЗ)
        if "deliverables" in data and data["deliverables"]:
            st.markdown("#### 📋 Пункты ТЗ / Результаты работы")
            st.caption("Каждый пункт содержит предложенные методологии БПМ/БПА")

            for i, deliv in enumerate(data["deliverables"], 1):
                with st.expander(f"**{deliv.get('number', i)}.** {deliv['title']}", expanded=(i<=3)):
                    st.markdown(f"**Описание:** {deliv.get('description', 'Не указано')}")
                    if deliv.get('suggested_methodologies'):
                        st.markdown(f"**Предложенные методологии:** {', '.join(deliv['suggested_methodologies'])}")

        # Methodologies (общий список)
        if "methodologies" in data and data["methodologies"]:
            st.markdown("#### 🔬 Методологии (общий список)")
            st.caption("Методы исследования упомянутые в договоре")
            methods_df = pd.DataFrame(data["methodologies"])
            st.dataframe(methods_df, use_container_width=True, hide_index=True)

        st.markdown("---")

        # Navigation buttons
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            if st.button("⬅️ Назад", use_container_width=True):
                st.session_state.create_step = 1
                st.rerun()
        with col2:
            if st.button("➡️ Далее", type="primary", use_container_width=True):
                st.session_state.create_step = 3
                st.rerun()
    else:
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            if st.button("⬅️ Назад", use_container_width=True):
                st.session_state.create_step = 1
                st.rerun()
        with col2:
            if st.button("⏩ Пропустить", use_container_width=True):
                st.session_state.create_step = 3
                st.rerun()


def show_step3_planning():
    """Step 3: Project planning - assign methodologies and dependencies"""
    st.subheader("Шаг 3: Планирование проекта")

    # Check if we have extracted deliverables
    if not st.session_state.extracted_data or "deliverables" not in st.session_state.extracted_data:
        st.warning("⚠️ Нет пунктов ТЗ для планирования. Вернитесь на шаг 2 и загрузите договор.")
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("⬅️ Назад", use_container_width=True):
                st.session_state.create_step = 2
                st.rerun()
        return

    # Load all methodologies from database
    db = get_db()
    methodologies = db.query(Methodology).order_by(Methodology.category, Methodology.code).all()

    # Create methodology options for multiselect
    methodology_options = {f"{m.code}: {m.name}": m.code for m in methodologies}
    methodology_labels = list(methodology_options.keys())

    st.markdown("### 📋 Таблица планирования")
    st.caption("Для каждого пункта ТЗ выберите методологии и укажите зависимости")

    # Initialize planning data in session state if not exists
    if "planning_data" not in st.session_state:
        st.session_state.planning_data = {}

    deliverables = st.session_state.extracted_data["deliverables"]

    # Create deliverable options for dependency selection
    deliverable_options = ["Нет зависимости"] + [
        f"{d.get('number', i)}: {d['title'][:50]}"
        for i, d in enumerate(deliverables, 1)
    ]

    # Dependency types
    dependency_types = {
        "FS (Finish-to-Start)": "FS",
        "SS (Start-to-Start)": "SS",
        "FF (Finish-to-Finish)": "FF",
        "SF (Start-to-Finish)": "SF"
    }

    st.markdown("---")

    # Display each deliverable with planning controls
    for i, deliv in enumerate(deliverables):
        deliv_key = f"deliv_{i}"

        with st.expander(f"**{deliv.get('number', i+1)}.** {deliv['title']}", expanded=True):
            st.markdown(f"**Описание:** {deliv.get('description', 'Не указано')}")

            if deliv.get('suggested_methodologies'):
                st.caption(f"💡 AI рекомендует: {', '.join(deliv['suggested_methodologies'])}")

            # Initialize planning data for this deliverable
            if deliv_key not in st.session_state.planning_data:
                # Pre-select suggested methodologies if available
                suggested = deliv.get('suggested_methodologies', [])
                preselected = [label for label in methodology_labels
                              if any(code in label for code in suggested)]

                st.session_state.planning_data[deliv_key] = {
                    "methodologies": preselected,
                    "dependencies": []  # List of {predecessor_idx, dependency_type}
                }

            # Methodology multiselect
            selected_labels = st.multiselect(
                "Методологии БПМ/БПА/БПВ",
                options=methodology_labels,
                default=st.session_state.planning_data[deliv_key]["methodologies"],
                key=f"methodologies_{i}",
                help="Выберите одну или несколько методологий для этого пункта ТЗ"
            )
            st.session_state.planning_data[deliv_key]["methodologies"] = selected_labels

            # Show selected methodologies codes
            if selected_labels:
                selected_codes = [methodology_options[label] for label in selected_labels]
                st.caption(f"✓ Методологии: {', '.join(selected_codes)}")

            st.markdown("**Зависимости от других задач:**")

            # Show existing dependencies
            dependencies = st.session_state.planning_data[deliv_key]["dependencies"]

            if dependencies:
                for dep_idx, dep in enumerate(dependencies):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        pred_idx = st.selectbox(
                            "Предшествующая задача",
                            options=range(len(deliverable_options)),
                            format_func=lambda x: deliverable_options[x],
                            index=dep["predecessor_idx"],
                            key=f"dep_pred_{i}_{dep_idx}",
                            label_visibility="collapsed"
                        )
                        dep["predecessor_idx"] = pred_idx

                    with col2:
                        if pred_idx > 0:
                            dep_type_label = st.selectbox(
                                "Тип связи",
                                options=list(dependency_types.keys()),
                                index=list(dependency_types.values()).index(dep["dependency_type"]),
                                key=f"dep_type_{i}_{dep_idx}",
                                label_visibility="collapsed"
                            )
                            dep["dependency_type"] = dependency_types[dep_type_label]
                        else:
                            st.caption("_Выберите задачу_")

                    with col3:
                        if st.button("🗑️", key=f"del_dep_{i}_{dep_idx}", help="Удалить зависимость"):
                            dependencies.pop(dep_idx)
                            st.rerun()
            else:
                st.caption("_Нет зависимостей_")

            # Add new dependency button
            if st.button("➕ Добавить зависимость", key=f"add_dep_{i}"):
                dependencies.append({"predecessor_idx": 0, "dependency_type": "FS"})
                st.rerun()

    st.markdown("---")

    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        if st.button("⬅️ Назад", use_container_width=True):
            st.session_state.create_step = 2
            st.rerun()
    with col2:
        if st.button("➡️ Далее", type="primary", use_container_width=True):
            st.session_state.create_step = 4
            st.rerun()


def show_step4_review_create():
    """Step 4: Review all data and create project"""
    st.subheader("Шаг 4: Проверка и создание")

    # Show summary
    st.markdown("### 📋 Сводка проекта")

    data = st.session_state.project_data

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Название:** {data['name']}")
        st.markdown(f"**Клиент:** {data['client']}")
        st.markdown(f"**Project Code:** `{data['project_code']}`")
    with col2:
        st.markdown(f"**Старт:** {data['start_date'].strftime('%d.%m.%Y')}")
        st.markdown(f"**Окончание:** {data['end_date'].strftime('%d.%m.%Y')}")

    # Show extracted data if available
    if st.session_state.extracted_data:
        st.markdown("### 💰 Извлеченные данные из договора")
        extracted = st.session_state.extracted_data

        col1, col2, col3 = st.columns(3)
        with col1:
            if "budget" in extracted:
                st.metric("Бюджет", f"{extracted['budget']['total']:,.0f} {extracted['budget']['currency']}")
        with col2:
            if "deliverables" in extracted:
                st.metric("Пунктов ТЗ", len(extracted['deliverables']))
        with col3:
            if "methodologies" in extracted:
                st.metric("Методологий", len(extracted['methodologies']))

        if "payment_stages" in extracted:
            st.caption(f"📌 Этапов оплаты: {len(extracted.get('payment_stages', []))}")

    st.markdown("---")

    # Create button
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        if st.button("⬅️ Назад", use_container_width=True):
            st.session_state.create_step = 3
            st.rerun()
    with col2:
        if st.button("✅ Создать проект", type="primary", use_container_width=True):
            with st.spinner("Создаю проект..."):
                try:
                    db = get_db()

                    # Create project
                    extracted = st.session_state.extracted_data or {}
                    budget = extracted.get("budget", {})
                    duration = extracted.get("duration", {})

                    new_project = Project(
                        project_code=data["project_code"],
                        name=data["name"],
                        client=data["client"],
                        contract_signed_date=data.get("contract_signed_date"),
                        prepayment_date=data["start_date"],  # Day 0 = start_date
                        start_date=data["start_date"],
                        end_date=data["end_date"],
                        payment_scenario=data.get("payment_scenario", "thirds"),
                        status="draft",
                        group=data["group"],
                        project_type=data["project_type"],
                        budget_total=budget.get("total"),
                        budget_currency=budget.get("currency", "RUB"),
                        vat_included=budget.get("vat_included", True),
                        vat_rate=budget.get("vat_rate", 5),
                        duration_weeks=duration.get("weeks"),
                        sales_notes=data.get("sales_notes"),
                        project_specifics=data.get("project_specifics"),
                        created_by="admin"
                    )

                    db.add(new_project)
                    db.flush()  # Get project ID

                    # Add contract document if uploaded
                    if "contract_text" in data:
                        doc = ProjectDocument(
                            project_id=new_project.id,
                            type="contract",
                            file_name=data.get("contract_filename", "contract.txt"),
                            extracted_text=data["contract_text"],
                            ai_extracted_data=extracted,
                            ai_processing_status="completed",
                            ai_confidence_score=extracted.get("confidence_score", 0),
                            processed_at=datetime.utcnow()
                        )
                        db.add(doc)

                    # Add proposal document if uploaded
                    if "proposal_filename" in data:
                        proposal_doc = ProjectDocument(
                            project_id=new_project.id,
                            type="proposal",
                            file_name=data["proposal_filename"],
                            ai_processing_status="pending"
                        )
                        db.add(proposal_doc)

                    # Add payment stages
                    if "payment_stages" in extracted:
                        for stage in extracted["payment_stages"]:
                            payment = PaymentStage(
                                project_id=new_project.id,
                                stage_number=stage["stage_number"],
                                amount=stage["amount"],
                                description=stage.get("description"),
                                trigger=stage.get("trigger"),
                                is_from_contract=True
                            )
                            db.add(payment)

                    # Add deliverables (пункты ТЗ) with planning data
                    created_deliverables = []
                    if "deliverables" in extracted:
                        # Get planning data and methodology mapping
                        planning_data = st.session_state.get("planning_data", {})
                        methodology_options = {f"{m.code}: {m.name}": m.code for m in db.query(Methodology).all()}

                        for i, deliv in enumerate(extracted["deliverables"]):
                            deliv_key = f"deliv_{i}"

                            # Get selected methodologies from planning data
                            selected_methodologies = []
                            if deliv_key in planning_data:
                                selected_labels = planning_data[deliv_key].get("methodologies", [])
                                selected_methodologies = [methodology_options[label] for label in selected_labels if label in methodology_options]

                            deliverable = Deliverable(
                                project_id=new_project.id,
                                number=deliv.get("number"),
                                title=deliv["title"],
                                description=deliv.get("description"),
                                suggested_methodologies=deliv.get("suggested_methodologies", []),
                                selected_methodologies=selected_methodologies,
                                is_from_contract=True
                            )
                            db.add(deliverable)
                            db.flush()  # Get ID for dependency creation
                            created_deliverables.append((i, deliverable))

                        # Create task dependencies (multiple dependencies per task)
                        for i, deliverable in created_deliverables:
                            deliv_key = f"deliv_{i}"
                            if deliv_key in planning_data:
                                dependencies = planning_data[deliv_key].get("dependencies", [])
                                for dep in dependencies:
                                    predecessor_idx = dep.get("predecessor_idx", 0)
                                    if predecessor_idx > 0:  # 0 means no dependency
                                        # predecessor_idx is 1-based (0 is "no dependency", 1 is first deliverable, etc.)
                                        predecessor_deliv_idx = predecessor_idx - 1
                                        if 0 <= predecessor_deliv_idx < len(created_deliverables):
                                            predecessor_deliv = created_deliverables[predecessor_deliv_idx][1]
                                            dependency_type = dep.get("dependency_type", "FS")

                                            task_dependency = TaskDependency(
                                                project_id=new_project.id,
                                                predecessor_id=predecessor_deliv.id,
                                                successor_id=deliverable.id,
                                                dependency_type=dependency_type,
                                                lag_days=0
                                            )
                                            db.add(task_dependency)

                    # Add methodologies
                    if "methodologies" in extracted:
                        for meth in extracted["methodologies"]:
                            # Find methodology by code
                            methodology = db.query(Methodology).filter(Methodology.code == meth["code"]).first()
                            if methodology:
                                selection = MethodologySelection(
                                    project_id=new_project.id,
                                    methodology_id=methodology.id,
                                    is_selected=True,
                                    is_from_contract=True,
                                    quantity=meth.get("quantity"),
                                    details=meth.get("details")
                                )
                                db.add(selection)

                    # Create Setup Checklist items
                    for item_template in SETUP_CHECKLIST_ITEMS:
                        checklist_item = SetupChecklistItem(
                            project_id=new_project.id,
                            item_number=item_template["item_number"],
                            title=item_template["title"],
                            description=item_template["description"]
                        )
                        db.add(checklist_item)

                    # Generate project structure and documents with GDrive sync
                    with st.spinner("🎨 Генерирую админшкалу и PERT..."):
                        try:
                            generator = get_project_generator()
                            claude_client = get_claude_client()

                            # Try to initialize Google Drive client
                            gdrive_client = None
                            try:
                                gdrive_client = get_google_drive_client()
                            except Exception as gdrive_error:
                                st.warning(f"⚠️ Google Drive недоступен: {str(gdrive_error)}\nПроект будет создан только в Obsidian Vault")

                            # Create project with dual sync
                            result = generator.create_project_with_gdrive_sync(
                                data,
                                extracted,
                                claude_client,
                                gdrive_client
                            )

                            # Update project with paths and links
                            new_project.obsidian_path = result['obsidian_path']

                            if result.get('google_drive'):
                                new_project.google_drive_folder_id = result['google_drive']['folder_id']
                                new_project.google_drive_folder_url = result['google_drive']['folder_url']

                        except Exception as e:
                            st.warning(f"⚠️ Проект создан в БД, но не удалось сгенерировать документы: {str(e)}")
                            result = None

                    # Single commit after all operations
                    db.commit()

                    # Refresh object to access attributes after commit
                    db.refresh(new_project)

                    db.close()

                    st.success(f"🎉 Проект создан! Project code: {new_project.project_code}")

                    # Show created files and locations
                    if result:
                        files = result.get('files', {})
                        project_folder_name = result['obsidian_path'].split('/')[-1]

                        st.info(f"📁 **Созданы файлы в Obsidian:**\n"
                                f"- Админшкала: `{files.get('adminscale', 'N/A').name if 'adminscale' in files else 'N/A'}`\n"
                                f"- PERT для xMind: `{files.get('pert', 'N/A').name if 'pert' in files else 'N/A'}`\n"
                                f"- README: `{files.get('readme', 'N/A').name if 'readme' in files else 'N/A'}`\n"
                                f"\n📂 Папка проекта: `{project_folder_name}`")

                        # Show Google Drive links if available
                        if result.get('google_drive'):
                            gdrive_url = result['google_drive']['folder_url']
                            st.success(f"☁️ **Проект синхронизирован с Google Drive:**\n"
                                      f"[Открыть папку проекта в Google Drive]({gdrive_url})")
                        elif result.get('google_drive_error'):
                            st.warning(f"⚠️ Синхронизация с Google Drive не удалась: {result['google_drive_error']}")

                    # Clear session state
                    st.session_state.create_step = 1
                    st.session_state.project_data = {}
                    st.session_state.extracted_data = None

                    st.info("👉 Перейдите на страницу 'Все проекты' чтобы увидеть созданный проект")

                except Exception as e:
                    st.error(f"❌ Ошибка при создании проекта: {str(e)}")
                    db.rollback()
                    db.close()


def show_statistics():
    """Show statistics dashboard"""
    st.header("📈 Статистика и Администрирование")

    db = get_db()

    # Get stats
    total_projects = db.query(Project).count()
    draft_count = db.query(Project).filter(Project.status == "draft").count()
    active_count = db.query(Project).filter(Project.status == "active").count()
    completed_count = db.query(Project).filter(Project.status == "completed").count()

    db.close()

    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Всего проектов", total_projects, help="Общее количество проектов в системе")
    with col2:
        st.metric("Черновики", draft_count, help="Проекты в статусе draft")
    with col3:
        st.metric("В работе", active_count, help="Активные проекты")
    with col4:
        st.metric("Завершено", completed_count, help="Завершенные проекты")

    st.divider()

    # Excel Import Section
    st.subheader("📥 Импорт проектов из Excel")

    with st.expander("Импорт существующих проектов из реестра"):
        st.markdown("""
        Загрузите существующий реестр проектов из Excel файла для массового импорта.

        **Формат файла:**
        - Лист должен содержать колонки: Название, Ссылка на папку, Дата старта, и т.д.
        - Поддерживается файл формата `B2c. Формуляр.xlsx` с листом ` Буферы и ссылки на все`
        """)

        # File upload
        uploaded_file = st.file_uploader(
            "Выберите Excel файл",
            type=["xlsx", "xls"],
            help="Загрузите файл реестра проектов"
        )

        # Group selection for import
        import_group = st.selectbox(
            "Группа для импортируемых проектов",
            options=["right", "left"],
            format_func=lambda x: "Правая группа" if x == "right" else "Левая группа",
            help="Все проекты будут импортированы в выбранную группу"
        )

        if uploaded_file:
            # Save uploaded file temporarily
            import tempfile
            import os
            from api.excel_import import preview_excel_import, import_projects_from_excel

            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name

            try:
                # Preview data
                st.info("📋 Предпросмотр данных из файла:")
                preview_df = preview_excel_import(tmp_path)
                st.dataframe(preview_df.head(10), use_container_width=True)
                st.caption(f"Всего проектов к импорту: {len(preview_df)}")

                # Import button
                if st.button("✅ Импортировать проекты", type="primary"):
                    with st.spinner("Импортируем проекты..."):
                        db = get_db()
                        stats = import_projects_from_excel(
                            tmp_path,
                            sheet_name=' Буферы и ссылки на все',
                            db_session=db,
                            default_group=import_group
                        )
                        db.close()

                    # Show results
                    st.success(f"✅ Импортировано проектов: {stats['imported']}")
                    if stats['skipped'] > 0:
                        st.warning(f"⏭️ Пропущено проектов: {stats['skipped']}")

                    if stats['errors']:
                        with st.expander("⚠️ Ошибки импорта"):
                            for error in stats['errors']:
                                st.error(error)

                    if stats['imported'] > 0:
                        st.info("👉 Перейдите на страницу 'Все проекты' чтобы увидеть импортированные проекты")

            except Exception as e:
                st.error(f"Ошибка при чтении файла: {str(e)}")
            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

    # Charts will be added in future versions
    st.divider()
    st.info("📊 Графики и детальная аналитика будут добавлены в следующих версиях")


if __name__ == "__main__":
    # Load authentication config
    config = load_auth_config()

    # Create authenticator
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )

    # Login widget
    name, authentication_status, username = authenticator.login('Вход', 'main')

    if authentication_status:
        # User is authenticated
        authenticator.logout('Выход', 'sidebar')

        # Show user info in sidebar
        with st.sidebar:
            st.write(f'Добро пожаловать, *{name}*!')
            st.markdown("---")

        # Run main application
        main()

    elif authentication_status == False:
        st.error('❌ Неверный логин или пароль')

    elif authentication_status == None:
        st.warning('⚠️ Пожалуйста, введите логин и пароль')
