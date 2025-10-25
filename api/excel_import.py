"""
Excel import functionality for Paper Planes PM Tool
Imports existing projects from registry Excel file
"""
import pandas as pd
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from database.models import Project


def parse_google_drive_url(url_or_text: str) -> Optional[str]:
    """
    Extract Google Drive file/folder ID from URL or return URL as-is

    Args:
        url_or_text: URL string or plain text

    Returns:
        Google Drive URL or None
    """
    if pd.isna(url_or_text) or not url_or_text:
        return None

    url_str = str(url_or_text).strip()

    # If it's already a URL, return as-is
    if url_str.startswith('http'):
        return url_str

    # Otherwise return None (plain text, not a link)
    return None


def import_projects_from_excel(
    excel_path: str,
    sheet_name: str = ' Буферы и ссылки на все',
    db_session: Session = None,
    default_group: str = 'right'
) -> Dict[str, Any]:
    """
    Import projects from Excel registry

    Args:
        excel_path: Path to Excel file
        sheet_name: Sheet name to import from
        db_session: SQLAlchemy session
        default_group: Default group for projects ('left' or 'right')

    Returns:
        Dict with import statistics
    """
    # Read Excel
    df = pd.read_excel(excel_path, sheet_name=sheet_name)

    # Statistics
    stats = {
        'total_rows': len(df),
        'imported': 0,
        'skipped': 0,
        'errors': [],
        'projects': []
    }

    # Column mapping from Excel to database
    # Excel: 'Название', 'Ссылка на папку', 'Приложение', 'Карта проблем', 'Админ шкала', 'Перт',
    #        'Дата старта', 'Идеальная дата окончания этапа', 'Кол-во недель этап',
    #        'Дата окончания по договору (этапа)', 'Идеальная дата окончания проекта',
    #        'Кол-во недель', 'Дата окончания по договору (проекта)'

    for idx, row in df.iterrows():
        try:
            # Skip empty rows
            if pd.isna(row.get('Название')) or not str(row.get('Название')).strip():
                stats['skipped'] += 1
                continue

            project_name = str(row['Название']).strip()

            # Generate project code (simple version, can be enhanced)
            # For now, use name as basis for project_code
            project_code = f"IMPORT_{idx+1}_{project_name[:10].upper()}"

            # Check if project already exists
            if db_session:
                existing = db_session.query(Project).filter_by(name=project_name).first()
                if existing:
                    stats['skipped'] += 1
                    stats['errors'].append(f"Project '{project_name}' already exists, skipping")
                    continue

            # Parse dates
            start_date = row.get('Дата старта')
            if pd.notna(start_date):
                if isinstance(start_date, str):
                    start_date = pd.to_datetime(start_date).date()
                elif isinstance(start_date, pd.Timestamp):
                    start_date = start_date.date()
            else:
                start_date = date.today()

            ideal_phase_end = row.get('Идеальная дата окончания этапа')
            if pd.notna(ideal_phase_end) and isinstance(ideal_phase_end, pd.Timestamp):
                ideal_phase_end = ideal_phase_end.date()
            else:
                ideal_phase_end = None

            contract_phase_end = row.get('Дата окончания по договору (этапа)')
            if pd.notna(contract_phase_end) and isinstance(contract_phase_end, pd.Timestamp):
                contract_phase_end = contract_phase_end.date()
            else:
                contract_phase_end = None

            ideal_project_end = row.get('Идеальная дата окончания проекта')
            if pd.notna(ideal_project_end) and isinstance(ideal_project_end, pd.Timestamp):
                ideal_project_end = ideal_project_end.date()
            else:
                ideal_project_end = None

            contract_project_end = row.get('Дата окончания по договору (проекта)')
            if pd.notna(contract_project_end) and isinstance(contract_project_end, pd.Timestamp):
                contract_project_end = contract_project_end.date()
            else:
                contract_project_end = None

            # Parse integer fields
            phase_weeks = row.get('Кол-во недель этап')
            if pd.notna(phase_weeks):
                phase_weeks = int(float(phase_weeks))
            else:
                phase_weeks = None

            total_weeks = row.get('Кол-во недель')
            if pd.notna(total_weeks):
                total_weeks = int(float(total_weeks))
            else:
                total_weeks = None

            # Parse buffer fields
            days_to_real_phase_end = row.get('Дней до реального конца этапа')
            if pd.notna(days_to_real_phase_end):
                days_to_real_phase_end = int(float(days_to_real_phase_end))
            else:
                days_to_real_phase_end = None

            days_to_ideal_phase_end = row.get('Дней до идеального конца этапа')
            if pd.notna(days_to_ideal_phase_end):
                days_to_ideal_phase_end = int(float(days_to_ideal_phase_end))
            else:
                days_to_ideal_phase_end = None

            days_to_phase_no_buffer = row.get('Дней до конца времени этапа без буфера')
            if pd.notna(days_to_phase_no_buffer):
                days_to_phase_no_buffer = int(float(days_to_phase_no_buffer))
            else:
                days_to_phase_no_buffer = None

            phase_buffer = row.get('Буфер этапа от идеальной до предельной')
            if pd.notna(phase_buffer):
                phase_buffer = int(float(phase_buffer))
            else:
                phase_buffer = None

            project_buffer = row.get('Буфер проекта от идеальной до предельной')
            if pd.notna(project_buffer):
                project_buffer = int(float(project_buffer))
            else:
                project_buffer = None

            # Create project object
            project_data = {
                'project_code': project_code,
                'name': project_name,
                'client': project_name,  # Using name as client for now
                'group': default_group,
                'project_type': 'existing',
                'status': 'active',  # Assuming imported projects are active
                'start_date': start_date,
                'prepayment_date': start_date,
                'end_date': contract_project_end or start_date,

                # Document links
                'google_drive_folder_url': parse_google_drive_url(row.get('Ссылка на папку')),
                'contract_appendix_url': parse_google_drive_url(row.get('Приложение')),
                'problem_map_url': parse_google_drive_url(row.get('Карта проблем')),
                'adminscale_url': parse_google_drive_url(row.get('Админ шкала')),
                'pert_url': parse_google_drive_url(row.get('Перт')),

                # Timeline
                'ideal_phase_end_date': ideal_phase_end,
                'phase_duration_weeks': phase_weeks,
                'contract_phase_end_date': contract_phase_end,
                'ideal_project_end_date': ideal_project_end,
                'contract_project_end_date': contract_project_end,
                'duration_weeks': total_weeks,

                # Buffers
                'days_to_real_phase_end': days_to_real_phase_end,
                'days_to_ideal_phase_end': days_to_ideal_phase_end,
                'days_to_phase_end_no_buffer': days_to_phase_no_buffer,
                'phase_buffer_days': phase_buffer,
                'project_buffer_days': project_buffer,

                # Metadata
                'created_by': 'Excel Import',
                'created_at': datetime.utcnow(),
            }

            if db_session:
                # Create database record
                project = Project(**project_data)
                db_session.add(project)
                db_session.flush()  # Get ID without committing

                stats['imported'] += 1
                stats['projects'].append({
                    'id': project.id,
                    'name': project.name,
                    'code': project.project_code
                })
            else:
                # Just collect data (dry run)
                stats['imported'] += 1
                stats['projects'].append(project_data)

        except Exception as e:
            stats['errors'].append(f"Row {idx+1} ({row.get('Название', 'Unknown')}): {str(e)}")
            continue

    # Commit if using database
    if db_session and stats['imported'] > 0:
        try:
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            stats['errors'].append(f"Database commit failed: {str(e)}")
            stats['imported'] = 0

    return stats


def preview_excel_import(excel_path: str, sheet_name: str = ' Буферы и ссылки на все') -> pd.DataFrame:
    """
    Preview Excel data before import

    Args:
        excel_path: Path to Excel file
        sheet_name: Sheet name to preview

    Returns:
        DataFrame with preview data
    """
    df = pd.read_excel(excel_path, sheet_name=sheet_name)

    # Filter out empty rows
    df_filtered = df[df['Название'].notna() & (df['Название'].str.strip() != '')]

    # Select key columns for preview
    preview_cols = [
        'Название',
        'Ссылка на папку',
        'Дата старта',
        'Кол-во недель',
        'Дата окончания по договору (проекта)'
    ]

    available_cols = [col for col in preview_cols if col in df_filtered.columns]

    return df_filtered[available_cols]
