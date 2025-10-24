"""
Database models for Paper Planes PM Tool
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Date, JSON, Float, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Project(Base):
    """Проекты Paper Planes"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    project_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    client = Column(String(100), nullable=False, index=True)

    # Payment and timing
    contract_signed_date = Column(Date)
    prepayment_date = Column(Date, nullable=False)  # Day 0 of project
    start_date = Column(Date, nullable=False)  # = prepayment_date
    end_date = Column(Date, nullable=False)
    payment_scenario = Column(String(20), default="thirds")  # thirds, heavy_analytics

    status = Column(String(20), default="draft", index=True)

    # Organization
    group = Column(String(20), nullable=False, index=True)  # left or right
    project_type = Column(String(20), nullable=False)  # new or existing

    # Financial data (from contract AI extraction)
    budget_total = Column(Numeric(15, 2))  # Total project budget
    budget_currency = Column(String(10), default="RUB")
    vat_included = Column(Boolean, default=True)
    vat_rate = Column(Integer, default=5)  # VAT rate percentage
    duration_weeks = Column(Integer)  # Project duration in weeks

    # Sales data
    sales_notes = Column(Text)  # Записи встреч по продаже (markdown)
    project_specifics = Column(Text)  # Особенности проекта от продавца

    # Integration
    google_drive_folder_id = Column(String(200))
    google_drive_folder_url = Column(Text)
    obsidian_path = Column(String(500))

    # Metadata
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    documents = relationship("ProjectDocument", back_populates="project", cascade="all, delete-orphan")
    methodology_selections = relationship("MethodologySelection", back_populates="project", cascade="all, delete-orphan")
    payment_stages = relationship("PaymentStage", back_populates="project", cascade="all, delete-orphan")
    deliverables = relationship("Deliverable", back_populates="project", cascade="all, delete-orphan")
    sprints = relationship("Sprint", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project {self.project_code}: {self.name}>"


class ProjectDocument(Base):
    """Документы проекта (договоры, коммерческие предложения)"""
    __tablename__ = "project_documents"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(50), nullable=False)  # contract, proposal, brief, other
    file_name = Column(String(200))
    file_url = Column(Text)
    google_drive_file_id = Column(String(200))
    extracted_text = Column(Text)
    ai_extracted_data = Column(JSON)  # JSON с извлеченными данными
    ai_processing_status = Column(String(50), default="pending")  # pending, processing, completed, error
    ai_confidence_score = Column(Integer)  # 0-100
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)

    # Relationships
    project = relationship("Project", back_populates="documents")

    def __repr__(self):
        return f"<ProjectDocument {self.type}: {self.file_name}>"


class Methodology(Base):
    """Справочник методологий БПМ/БПА"""
    __tablename__ = "methodologies"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False)  # БПМ1, БПМ2, БПА1, etc.
    name = Column(String(200), nullable=False)
    category = Column(String(10), nullable=False)  # БПМ или БПА
    description = Column(Text)
    typical_effort_hours = Column(Integer)
    requires_details = Column(Boolean, default=False)

    # Relationships
    selections = relationship("MethodologySelection", back_populates="methodology")

    def __repr__(self):
        return f"<Methodology {self.code}: {self.name}>"


class MethodologySelection(Base):
    """Выбор методологий для проекта"""
    __tablename__ = "methodology_selections"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    methodology_id = Column(Integer, ForeignKey("methodologies.id", ondelete="CASCADE"), nullable=False)
    is_selected = Column(Boolean, default=False)
    is_from_contract = Column(Boolean, default=False)  # Автоматически из договора
    quantity = Column(Integer)  # Например, количество интервью
    details = Column(Text)  # Дополнительные детали
    effort_hours = Column(Integer)  # Уточненная трудоемкость
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="methodology_selections")
    methodology = relationship("Methodology", back_populates="selections")

    def __repr__(self):
        return f"<MethodologySelection P{self.project_id} M{self.methodology_id}>"


class PaymentStage(Base):
    """Этапы оплаты проекта"""
    __tablename__ = "payment_stages"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    stage_number = Column(Integer, nullable=False)  # 1, 2, 3...
    amount = Column(Numeric(15, 2), nullable=False)  # Payment amount
    description = Column(Text)  # Stage description
    trigger = Column(Text)  # What triggers this payment (e.g., "Подписание договора")

    # Payment type and linking
    payment_type = Column(String(20), default="postpayment")  # prepayment, postpayment
    is_prepayment = Column(Boolean, default=False)
    linked_to_gate = Column(String(20))  # None, "Gate2", "Gate3", "Gate4", "Gate5"
    linked_to_phase = Column(String(20))  # None, "SETUP", "DISCOVER", "DEFINE", "DEVELOP", "DELIVER"

    # Status tracking
    status = Column(String(20), default="pending")  # pending, invoiced, paid, closed
    invoice_sent_date = Column(Date)
    payment_received_date = Column(Date)
    act_signed_date = Column(Date)

    is_from_contract = Column(Boolean, default=False)  # Automatically extracted from contract
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="payment_stages")

    def __repr__(self):
        return f"<PaymentStage P{self.project_id} Stage{self.stage_number}: {self.amount}>"


class Deliverable(Base):
    """Результаты работы / Пункты ТЗ проекта"""
    __tablename__ = "deliverables"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    number = Column(String(20))  # Номер пункта (3.1, 1, А, etc.)
    title = Column(String(500), nullable=False)  # Короткое название
    description = Column(Text)  # Полное описание пункта ТЗ
    suggested_methodologies = Column(JSON)  # Список кодов БПМ/БПА ["БПМ2", "БПМ4"]
    selected_methodologies = Column(JSON)  # Выбранные пользователем методологии ["БПМ2", "БПА1"]
    is_from_contract = Column(Boolean, default=False)  # Extracted from contract
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="deliverables")
    dependencies_as_successor = relationship("TaskDependency", back_populates="successor_task", foreign_keys="TaskDependency.successor_id")
    dependencies_as_predecessor = relationship("TaskDependency", back_populates="predecessor_task", foreign_keys="TaskDependency.predecessor_id")

    def __repr__(self):
        return f"<Deliverable P{self.project_id} {self.number}: {self.title[:30]}>"


class TaskDependency(Base):
    """Зависимости между Deliverable (контрактный уровень) для критического пути"""
    __tablename__ = "task_dependencies"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    predecessor_id = Column(Integer, ForeignKey("deliverables.id", ondelete="CASCADE"), nullable=False)  # Предшествующая задача
    successor_id = Column(Integer, ForeignKey("deliverables.id", ondelete="CASCADE"), nullable=False)  # Последующая задача
    dependency_type = Column(String(5), default="FS")  # FS, SS, FF, SF
    lag_days = Column(Integer, default=0)  # Задержка в днях (может быть отрицательной для опережения)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project")
    predecessor_task = relationship("Deliverable", back_populates="dependencies_as_predecessor", foreign_keys=[predecessor_id])
    successor_task = relationship("Deliverable", back_populates="dependencies_as_successor", foreign_keys=[successor_id])

    def __repr__(self):
        return f"<TaskDependency P{self.project_id}: Task{self.predecessor_id} -{self.dependency_type}-> Task{self.successor_id}>"


class MethodologyTask(Base):
    """Детальные задачи внутри методологий БПМ/БПА/БПВ (уровень декомпозиции)"""
    __tablename__ = "methodology_tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    deliverable_id = Column(Integer, ForeignKey("deliverables.id", ondelete="CASCADE"), nullable=False)  # К какому пункту ТЗ относится
    methodology_code = Column(String(10), nullable=False)  # БПМ1, БПА2, etc.

    # Task details
    title = Column(String(500), nullable=False)  # Название задачи
    description = Column(Text)  # Описание
    order = Column(Integer)  # Порядок выполнения внутри методологии

    # Time estimation
    estimated_hours = Column(Integer)  # Оценка трудоемкости
    start_date = Column(Date)  # Планируемая дата начала
    end_date = Column(Date)  # Планируемая дата окончания

    # Assignment
    assigned_to = Column(String(100))  # Кто выполняет

    # Status tracking
    status = Column(String(20), default="planned")  # planned, in_progress, completed, blocked
    completion_percentage = Column(Integer, default=0)  # 0-100

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project")
    deliverable = relationship("Deliverable")
    dependencies_as_successor = relationship("MethodologyTaskDependency", back_populates="successor_task", foreign_keys="MethodologyTaskDependency.successor_id")
    dependencies_as_predecessor = relationship("MethodologyTaskDependency", back_populates="predecessor_task", foreign_keys="MethodologyTaskDependency.predecessor_id")

    def __repr__(self):
        return f"<MethodologyTask {self.methodology_code}: {self.title[:30]}>"


class MethodologyTaskDependency(Base):
    """Зависимости между детальными задачами методологий (уровень декомпозиции)"""
    __tablename__ = "methodology_task_dependencies"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    predecessor_id = Column(Integer, ForeignKey("methodology_tasks.id", ondelete="CASCADE"), nullable=False)
    successor_id = Column(Integer, ForeignKey("methodology_tasks.id", ondelete="CASCADE"), nullable=False)
    dependency_type = Column(String(5), default="FS")  # FS, SS, FF, SF
    lag_days = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project")
    predecessor_task = relationship("MethodologyTask", back_populates="dependencies_as_predecessor", foreign_keys=[predecessor_id])
    successor_task = relationship("MethodologyTask", back_populates="dependencies_as_successor", foreign_keys=[successor_id])

    def __repr__(self):
        return f"<MethodologyTaskDependency: {self.predecessor_id} -{self.dependency_type}-> {self.successor_id}>"


class Sprint(Base):
    """Схватки (Sprints) - Paper Planes sprint methodology with CCPM"""
    __tablename__ = "sprints"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)

    # Sprint identification
    phase = Column(String(20), nullable=False)  # SETUP, DISCOVER, DEFINE, DEVELOP, DELIVER
    sprint_code = Column(String(20), nullable=False)  # S-1, S-2, D-1, D-2, DEF-1, DEV-1, DLV-1
    sprint_number = Column(Integer, nullable=False)  # Sequential number within project

    # Timing (relative to Day 0 = prepayment_date)
    start_day = Column(Integer, nullable=False)  # Days from Day 0
    end_day = Column(Integer, nullable=False)  # Days from Day 0
    duration_days = Column(Integer, nullable=False)  # Sprint duration (3-11 days)

    # Absolute dates (calculated from prepayment_date)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Decision day (last day of sprint - Wed/Sat)
    decision_day = Column(Date, nullable=False)  # День перегиба
    decision_day_name = Column(String(20))  # Wednesday, Saturday
    decision_point = Column(Text)  # Go/No-Go question for this sprint

    # Sprint content
    sprint_goal = Column(Text)  # Goal of this sprint
    deliverables = Column(JSON)  # List of expected deliverables

    # Status
    status = Column(String(20), default="planned")  # planned, active, completed, blocked
    actual_end_date = Column(Date)  # Actual completion date (may differ from planned)
    decision_outcome = Column(String(20))  # go, no_go, conditional

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="sprints")
    tasks = relationship("SprintTask", back_populates="sprint", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Sprint {self.sprint_code}: {self.phase} Day{self.start_day}-{self.end_day}>"


class SprintTask(Base):
    """Задачи внутри схваток (Sprint Tasks) - operational level"""
    __tablename__ = "sprint_tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    sprint_id = Column(Integer, ForeignKey("sprints.id", ondelete="CASCADE"), nullable=False, index=True)

    # Link to methodology task (optional - can be standalone)
    methodology_task_id = Column(Integer, ForeignKey("methodology_tasks.id", ondelete="SET NULL"))

    # Task type (from Paper Planes methodology)
    task_type = Column(String(20), nullable=False)  # deliverable, communication, process, product
    task_icon = Column(String(10))  # 📦, 💬, 🔄, 🎨

    # Task details
    title = Column(String(500), nullable=False)
    description = Column(Text)
    order = Column(Integer)  # Order within sprint

    # Assignment
    assigned_to = Column(String(100))

    # Status tracking
    status = Column(String(20), default="todo")  # todo, in_progress, done, blocked
    completion_percentage = Column(Integer, default=0)  # 0-100
    blocked_reason = Column(Text)  # Why blocked (if status=blocked)

    # Timing
    planned_hours = Column(Integer)
    actual_hours = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project")
    sprint = relationship("Sprint", back_populates="tasks")
    methodology_task = relationship("MethodologyTask")

    def __repr__(self):
        return f"<SprintTask {self.task_icon} {self.title[:30]}>"


class SetupChecklistItem(Base):
    """Setup Checklist - обязательные действия ДО открывающей сессии"""
    __tablename__ = "setup_checklist_items"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)

    # Item details
    item_number = Column(Integer, nullable=False)  # 1-10
    title = Column(String(500), nullable=False)  # Название пункта
    description = Column(Text)  # Описание и инструкции

    # Employee completion
    is_completed = Column(Boolean, default=False)  # Checkbox сотрудника
    completed_by = Column(String(100))  # Кто отметил выполнение
    completed_at = Column(DateTime)  # Когда отмечено

    # Manager approval (двухэтапная проверка)
    is_approved = Column(Boolean, default=False)  # Approval руководителя
    approved_by = Column(String(100))  # Кто одобрил (из списка APPROVERS)
    approved_at = Column(DateTime)  # Когда одобрено

    # Proof (ссылка или файл)
    proof_type = Column(String(20))  # "link" or "file"
    proof_url = Column(Text)  # Ссылка (Kaiten, Telegram, Miro, etc.)
    proof_file_id = Column(String(200))  # Google Drive file ID если скриншот

    # Additional info
    notes = Column(Text)  # Комментарии
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project")

    def __repr__(self):
        return f"<SetupChecklistItem P{self.project_id} #{self.item_number}: {self.title[:30]}>"


# Constants for Setup Checklist
SETUP_APPROVERS = [
    "Такаева Наташа",
    "Кудовеков Сергей",
    "Ротвилишвили Георгий",
    "Шагазатов Диер",
    "Балахнин Илья"
]

SETUP_CHECKLIST_ITEMS = [
    {
        "item_number": 1,
        "title": "Создание чата с клиентом и представление команды",
        "description": "Создать чат с клиентом в Telegram/WhatsApp, представить команду проекта"
    },
    {
        "item_number": 2,
        "title": "Выбор менеджера проекта",
        "description": "Выбрать менеджера проекта из рабочей группы"
    },
    {
        "item_number": 3,
        "title": "Получение и обработка оргструктуры",
        "description": "Получить файл оргструктуры клиента, добавить комментарии: кто важен, кто LPR и т.д."
    },
    {
        "item_number": 4,
        "title": "Отправить запрос стартовых материалов",
        "description": "Отправить клиенту ссылку на Google Spreadsheet шаблон для запроса материалов"
    },
    {
        "item_number": 5,
        "title": "Согласовать дату открывающей сессии",
        "description": "Согласовать с клиентом дату и время открывающей сессии"
    },
    {
        "item_number": 6,
        "title": "Создание Miro проекта",
        "description": "Создать Miro board для проекта"
    },
    {
        "item_number": 7,
        "title": "Добавить проект в финтаблицу",
        "description": "Добавить проект в финансовую таблицу Paper Planes"
    },
    {
        "item_number": 8,
        "title": "Добавить проект в таблицу Производства по деньгам",
        "description": "Добавить проект в таблицу отслеживания производства"
    },
    {
        "item_number": 9,
        "title": "Добавить проект в борд инициирования в Kaiten",
        "description": "Создать карточку проекта в борде инициирования Kaiten"
    },
    {
        "item_number": 10,
        "title": "Создан внутренний чат проекта в Telegram",
        "description": "Создать внутренний чат команды проекта в Telegram"
    }
]
