"""
Project generator for Paper Planes PM Tool
Creates project structure, adminscale, and PERT documents
"""
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


class ProjectGenerator:
    """Generates project structure and documents"""

    def __init__(self, vault_path: str):
        """
        Initialize generator with Obsidian vault path

        Args:
            vault_path: Path to HUDDY Vault root
        """
        self.vault_path = Path(vault_path)
        self.projects_path = self.vault_path / "20-projects" / "21-engagements" / "211-active"

    def create_project_structure(self, project_code: str, project_name: str) -> Path:
        """
        Create project folder structure

        Args:
            project_code: Project code (e.g., "2169.CLI.client")
            project_name: Client name

        Returns:
            Path to project root folder
        """
        # Extract ticker from project code (e.g., "CLI" from "2169.CLI.client")
        ticker = project_code.split(".")[1] if "." in project_code else "XXX"

        # Create project folder name (e.g., "2169.CLI.client-name")
        folder_name = project_code.lower()
        project_folder = self.projects_path / folder_name

        # Create folder structure
        folders = [
            project_folder,
            project_folder / f"{ticker}.01-inbox",
            project_folder / f"{ticker}.02-research",
            project_folder / f"{ticker}.03-meetings",
            project_folder / f"{ticker}.04-project-docs",
            project_folder / f"{ticker}.05-deliverables",
        ]

        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)

        return project_folder

    def generate_adminscale(
        self,
        project_data: Dict[str, Any],
        extracted_data: Dict[str, Any],
        claude_client
    ) -> str:
        """
        Generate adminscale markdown using Claude AI

        Args:
            project_data: Project information from UI
            extracted_data: Extracted data from contract
            claude_client: Claude API client

        Returns:
            Generated adminscale markdown content
        """
        # Prepare context for Claude
        deliverables_list = "\n".join([
            f"- {d.get('number', '')}. {d.get('title', '')}: {d.get('description', '')}"
            for d in extracted_data.get("deliverables", [])
        ])

        methodologies_list = "\n".join([
            f"- {m.get('code', '')} ({m.get('name', '')}): {m.get('details', '')}"
            for m in extracted_data.get("methodologies", [])
        ])

        prompt = f"""Сгенерируй админшкалу (administrative scale) для консалтингового проекта.

**ИНФОРМАЦИЯ О ПРОЕКТЕ:**
- Project Code: {project_data.get('project_code', '')}
- Название: {project_data.get('name', '')}
- Клиент: {project_data.get('client', '')}
- Группа: {"Правая" if project_data.get('group') == 'right' else "Левая"}
- Тип: {"Новый проект" if project_data.get('project_type') == 'new' else "Существующий проект"}
- Даты: {project_data.get('start_date')} - {project_data.get('end_date')}
- Бюджет: {extracted_data.get('budget', {}).get('total', 0)} {extracted_data.get('budget', {}).get('currency', 'RUB')}
- Длительность: {extracted_data.get('duration', {}).get('weeks', 'N/A')} недель

**РЕЗУЛЬТАТЫ РАБОТЫ (ИЗ ДОГОВОРА):**
{deliverables_list}

**МЕТОДОЛОГИИ БПМ:**
{methodologies_list}

**NOTES FROM SALES:**
{project_data.get('sales_notes', 'Не указано')}

**PROJECT SPECIFICS:**
{project_data.get('project_specifics', 'Не указано')}

---

Сгенерируй markdown-документ админшкалы по следующей структуре:

```markdown
---
type: project
subtype: engagement
ticker: [TICKER]
client: "[[{project_data.get('client', '')}]]"
contract_value: [VALUE]
start_date: {project_data.get('start_date')}
deadline: {project_data.get('end_date')}
status: setup
priority: 5

# Триаж и схватки
in_triage: true
triage_sprint: "2025-WXX-Схватка1"

# Этапы и РГ
project_stage: "setup"
rg: "{project_data.get('group', 'left')}"

# Команда проекта
team:
  lead: "[[Худовеков Сергей]]"
  manager: ""
  team: []

# Deliverables
deliverables:
  [СПИСОК ИЗ ДОГОВОРА]

tags:
  - "#engagement"
---

# [TICKER]: {project_data.get('client', '')} — Adminscale

**Класс:** ENGAGEMENT
**Клиент:** {project_data.get('client', '')}
**Статус:** 🟢 Active
**Лид:** [ИМЯ]

---

## 1. ВХОД (Entry)

### Industry & Client Context
- **Клиент:** {project_data.get('client', '')}
- **Отрасль:** [ОПРЕДЕЛИ НА ОСНОВЕ КОНТЕКСТА]
- **Контакт:** [ОПРЕДЕЛИ ИЗ КОНТЕКСТА]

### Facts
- **Исходная ситуация:** [СФОРМУЛИРУЙ НА ОСНОВЕ PROJECT SPECIFICS И DELIVERABLES]
- **Барьеры:** [ОПРЕДЕЛИ НА ОСНОВЕ КОНТЕКСТА]

### Resources & Risks
- **Команда:** [ОПРЕДЕЛИ НА ОСНОВЕ BUDGET И SCOPE]
- **Риски:** [ОПРЕДЕЛИ НА ОСНОВЕ PROJECT SPECIFICS]

---

## 2. ЦЕЛЬ (Goal)

**Формулировка:** [MEASURABLE GOAL С ДАТОЙ И ПОРОГОМ, НА ОСНОВЕ DELIVERABLES]

---

## 3. ЗАМЫСЕЛ (Intent)

### Sub-goals
[СОЗДАЙ 3-5 SUB-GOALS НА ОСНОВЕ DELIVERABLES И МЕТОДОЛОГИЙ]

---

## 4. ПЛАН (Plan)

### Этапы
**Stage 1 (Setup - Неделя 1):** [ОПРЕДЕЛИ НА ОСНОВЕ СТАНДАРТНОЙ МЕТОДОЛОГИИ]
**Stage 2 (Discover - Неделя 2):** [...]
**Stage 3 (Define - Недели 3-7):** [...]
**Stage 4 (Develop - Неделя 8):** [...]
**Stage 5 (Deliver - Неделя 9):** [...]

---

## 5. ЗАДАЧИ (Tasks)

```tasks
not done
path includes [PROJECT_CODE_LOWER]
sort by priority
```

---

## 6. ЦКП (Deliverables)

### Deliverables
[СПИСОК ВСЕХ DELIVERABLES С ПУТЯМИ К ФАЙЛАМ]

---

## 7. СТАТИСТИКИ (Statistics)

| Метрика | Baseline | Target | Current |
|---------|----------|--------|---------|
| [ОПРЕДЕЛИ НА ОСНОВЕ ПРОЕКТА] | | | |

---

## Project Log

### {datetime.now().strftime('%Y-%m-%d')}
- ✅ Проект создан через PM Tool
- ✅ Структура папок создана
- ✅ Админшкала сгенерирована

---

**Создан:** {datetime.now().strftime('%Y-%m-%d')}
```

ВАЖНО:
1. Сгенерируй ПОЛНОСТЬЮ заполненный markdown без placeholder'ов в квадратных скобках
2. Используй данные из контекста для всех полей
3. Создай реалистичные sub-goals на основе deliverables
4. Сформулируй measurable goal
5. Детально опиши каждый этап плана

Верни ТОЛЬКО markdown-текст, без дополнительных комментариев."""

        try:
            message = claude_client.client.messages.create(
                model=claude_client.model,
                max_tokens=8000,
                temperature=0.3,
                system="Ты — эксперт по управлению проектами Paper Planes. Генерируешь детальные админшкалы. Отвечай ТОЛЬКО markdown-текстом документа.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            return message.content[0].text

        except Exception as e:
            raise Exception(f"Error generating adminscale: {str(e)}")

    def generate_pert_for_xmind(
        self,
        project_data: Dict[str, Any],
        extracted_data: Dict[str, Any],
        claude_client
    ) -> str:
        """
        Generate PERT structure markdown for xMind import

        Args:
            project_data: Project information
            extracted_data: Extracted contract data
            claude_client: Claude API client

        Returns:
            PERT markdown for xMind import
        """
        deliverables_list = "\n".join([
            f"- {d.get('number', '')}. {d.get('title', '')}"
            for d in extracted_data.get("deliverables", [])
        ])

        prompt = f"""Создай PERT-диаграмму (структуру задач) для проекта в формате Markdown с иерархией заголовков.

**ПРОЕКТ:** {project_data.get('name', '')}
**КЛИЕНТ:** {project_data.get('client', '')}
**DELIVERABLES:**
{deliverables_list}

**ДЛИТЕЛЬНОСТЬ:** {extracted_data.get('duration', {}).get('weeks', 12)} недель

Создай детальную структуру задач по методологии "Сдвоенный рубин" Paper Planes:

# {project_data.get('project_code', '')} - PERT

## Этап 1: Setup (Неделя 1)
### 1.1 Tier-1 интервью
### 1.2 Создание устава проекта
### 1.3 Формирование Admin-шкалы базовой
### 1.4 Исходный запрос данных
### 1.5 Формулировка ключевых БПВ

## Этап 2: Discover (Неделя 2)
### 2.1 Карта проблем (Q, A)
### 2.2 Программа исследования
### 2.3 Разработка анкет и гайдов
### 2.4 Storyline (черновой)

[ПРОДОЛЖИ СТРУКТУРУ ДО 5 ЭТАПОВ: Setup, Discover, Define, Develop, Deliver]

Для КАЖДОГО deliverable создай отдельную ветку задач в соответствующих этапах.

Формат: используй ## для этапов, ### для задач, #### для подзадач.

Верни ТОЛЬКО markdown иерархию без пояснений."""

        try:
            message = claude_client.client.messages.create(
                model=claude_client.model,
                max_tokens=6000,
                temperature=0.3,
                system="Ты — эксперт по планированию проектов Paper Planes. Создаёшь детальные PERT-диаграммы. Отвечай ТОЛЬКО markdown-иерархией.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            return message.content[0].text

        except Exception as e:
            raise Exception(f"Error generating PERT: {str(e)}")

    def save_project_files(
        self,
        project_folder: Path,
        ticker: str,
        project_data: Dict[str, Any],
        adminscale_content: str,
        pert_content: str
    ) -> Dict[str, Path]:
        """
        Save all project files

        Args:
            project_folder: Path to project root
            ticker: Project ticker
            project_data: Project data
            adminscale_content: Generated adminscale markdown
            pert_content: Generated PERT markdown

        Returns:
            Dict with paths to created files
        """
        files_created = {}

        # Save adminscale
        adminscale_file = project_folder / f"{ticker}.{project_data['client'].replace(' ', '-')}.adminscale.md"
        adminscale_file.write_text(adminscale_content, encoding='utf-8')
        files_created['adminscale'] = adminscale_file

        # Save PERT for xMind
        pert_file = project_folder / f"{ticker}.04-project-docs" / f"{ticker}.PERT_FOR_XMIND.md"
        pert_file.write_text(pert_content, encoding='utf-8')
        files_created['pert'] = pert_file

        # Save contract text if available
        if 'contract_text' in project_data:
            contract_file = project_folder / f"{ticker}.01-inbox" / "Договор.txt"
            contract_file.write_text(project_data['contract_text'], encoding='utf-8')
            files_created['contract'] = contract_file

        # Create README
        readme_content = f"""# {project_data['project_code']}: {project_data['name']}

**Клиент:** {project_data['client']}
**Группа:** {"Правая" if project_data.get('group') == 'right' else "Левая"}
**Статус:** 🟢 Setup
**Создан:** {datetime.now().strftime('%Y-%m-%d')}

## Структура проекта

- `{ticker}.01-inbox/` — Входящие документы и материалы
- `{ticker}.02-research/` — Исследования и анализ
- `{ticker}.03-meetings/` — Заметки со встреч
- `{ticker}.04-project-docs/` — Проектные документы
- `{ticker}.05-deliverables/` — Результаты работы

## Ключевые документы

- [[{adminscale_file.name}]] — Админшкала проекта
- [[{pert_file.name}]] — PERT-диаграмма (импорт в xMind)

## Команда

- Лид:
- PM:
- Команда:

---
Создано автоматически через Paper Planes PM Tool
"""
        readme_file = project_folder / "README.md"
        readme_file.write_text(readme_content, encoding='utf-8')
        files_created['readme'] = readme_file

        return files_created

    def create_project_with_gdrive_sync(
        self,
        project_data: Dict[str, Any],
        extracted_data: Dict[str, Any],
        claude_client,
        google_drive_client=None
    ) -> Dict[str, Any]:
        """
        Complete project creation with dual sync to Obsidian and Google Drive

        Args:
            project_data: Project information from UI
            extracted_data: Extracted data from contract
            claude_client: Claude API client
            google_drive_client: Google Drive client (optional)

        Returns:
            Dict with all created resources (folders, files, links)
        """
        ticker = project_data['project_code'].split(".")[1] if "." in project_data['project_code'] else "XXX"

        # 1. Generate documents via AI (required for GDrive sync)
        adminscale_content = self.generate_adminscale(
            project_data,
            extracted_data,
            claude_client
        )

        pert_content = self.generate_pert_for_xmind(
            project_data,
            extracted_data,
            claude_client
        )

        # 2. Try to create Obsidian folder structure (optional for cloud deployment)
        project_folder = None
        files_created = {}

        try:
            project_folder = self.create_project_structure(
                project_data['project_code'],
                project_data['name']
            )

            # Save files to Obsidian
            files_created = self.save_project_files(
                project_folder,
                ticker,
                project_data,
                adminscale_content,
                pert_content
            )
        except (PermissionError, OSError) as e:
            # Obsidian Vault not available (likely cloud deployment)
            # Create temp files for GDrive upload
            import tempfile
            from pathlib import Path

            temp_dir = Path(tempfile.mkdtemp(prefix=f"project_{ticker}_"))

            # Save files to temp directory
            files_created = self.save_project_files(
                temp_dir,
                ticker,
                project_data,
                adminscale_content,
                pert_content
            )

        result = {
            'obsidian_path': str(project_folder) if project_folder else None,
            'files': files_created,
            'google_drive': None
        }

        # 4. Sync to Google Drive if client provided
        if google_drive_client:
            try:
                # Create GDrive folder structure
                gdrive_structure = google_drive_client.create_project_folder_structure(
                    project_data['project_code'],
                    project_data['client'],
                    project_data['group']
                )

                # Upload files to GDrive
                uploaded_files = google_drive_client.upload_project_files(
                    files_created,
                    gdrive_structure,
                    ticker
                )

                result['google_drive'] = {
                    'folder_id': gdrive_structure['project_folder']['id'],
                    'folder_url': gdrive_structure['project_folder']['url'],
                    'files': uploaded_files
                }

            except Exception as e:
                # Don't fail entire project creation if GDrive sync fails
                result['google_drive_error'] = str(e)

        return result


# Singleton instance
_project_generator = None


def get_project_generator(vault_path: str = None) -> ProjectGenerator:
    """Get project generator singleton"""
    global _project_generator
    if _project_generator is None:
        if vault_path is None:
            # Default path to HUDDY Vault
            vault_path = "/Users/khudovekov/Library/Mobile Documents/com~apple~CloudDocs/HUDDY Vault"
        _project_generator = ProjectGenerator(vault_path)
    return _project_generator
