"""
Google Drive API client for Paper Planes PM Tool
Manages project folders and files in Google Drive
"""
import os
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, List
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv

load_dotenv()

# Google Drive API scopes
SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']


class GoogleDriveClient:
    """Client for interacting with Google Drive API"""

    def __init__(self, credentials_path: str = None, token_path: str = None, shared_drive_id: str = None):
        """
        Initialize Google Drive client

        Args:
            credentials_path: Path to OAuth credentials JSON
            token_path: Path to token pickle file
            shared_drive_id: ID of Shared Drive (Team Drive) to use instead of personal drive
        """
        # Try to load shared_drive_id from Streamlit Secrets first
        if shared_drive_id is None:
            try:
                import streamlit as st
                if hasattr(st, 'secrets') and 'GOOGLE_SHARED_DRIVE_ID' in st.secrets:
                    shared_drive_id = st.secrets['GOOGLE_SHARED_DRIVE_ID']
            except (ImportError, KeyError):
                pass

        # Fall back to environment variables
        if credentials_path is None:
            credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
        if token_path is None:
            token_path = os.getenv("GOOGLE_TOKEN_PATH", "token.pickle")
        if shared_drive_id is None:
            shared_drive_id = os.getenv("GOOGLE_SHARED_DRIVE_ID")

        self.credentials_path = credentials_path
        self.token_path = token_path
        self.shared_drive_id = shared_drive_id
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Drive API"""
        creds = None

        # Try to load from Streamlit Secrets first (for cloud deployment)
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and 'google_oauth' in st.secrets:
                secrets = st.secrets['google_oauth']
                creds = Credentials(
                    token=None,
                    refresh_token=secrets['refresh_token'],
                    token_uri='https://oauth2.googleapis.com/token',
                    client_id=secrets['client_id'],
                    client_secret=secrets['client_secret'],
                    scopes=SCOPES
                )
                # Refresh to get access token
                creds.refresh(Request())
                self.service = build('drive', 'v3', credentials=creds)
                return
        except (ImportError, KeyError):
            # Streamlit not available or secrets not configured, fall back to file-based auth
            pass

        # Load token if exists
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)

        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Google credentials file not found: {self.credentials_path}\n"
                        "Please download OAuth credentials from Google Cloud Console"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save credentials
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('drive', 'v3', credentials=creds)

    def find_folder_by_name(self, folder_name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """
        Find folder by name, optionally within a parent folder

        Args:
            folder_name: Name of the folder to find
            parent_id: Parent folder ID (optional, if None uses shared_drive_id)

        Returns:
            Folder ID if found, None otherwise
        """
        # If no parent specified, use Shared Drive root if available
        if parent_id is None and self.shared_drive_id:
            parent_id = self.shared_drive_id

        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"

        try:
            list_params = {
                'q': query,
                'spaces': 'drive',
                'fields': 'files(id, name)'
            }

            # Add Shared Drive support if using Shared Drive
            if self.shared_drive_id:
                list_params['supportsAllDrives'] = True
                list_params['includeItemsFromAllDrives'] = True
                list_params['corpora'] = 'drive'
                list_params['driveId'] = self.shared_drive_id

            results = self.service.files().list(**list_params).execute()

            items = results.get('files', [])
            if items:
                return items[0]['id']
            return None
        except Exception as e:
            raise Exception(f"Error finding folder '{folder_name}': {str(e)}")

    def create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> Dict[str, str]:
        """
        Create a folder in Google Drive

        Args:
            folder_name: Name of the folder to create
            parent_id: Parent folder ID (optional, if None uses shared_drive_id)

        Returns:
            Dict with 'id' and 'webViewLink'
        """
        # If no parent specified, use Shared Drive root if available
        if parent_id is None and self.shared_drive_id:
            parent_id = self.shared_drive_id

        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }

        if parent_id:
            file_metadata['parents'] = [parent_id]

        try:
            create_params = {
                'body': file_metadata,
                'fields': 'id, webViewLink'
            }

            # Add Shared Drive support if using Shared Drive
            if self.shared_drive_id:
                create_params['supportsAllDrives'] = True

            folder = self.service.files().create(**create_params).execute()

            return {
                'id': folder.get('id'),
                'url': folder.get('webViewLink')
            }
        except Exception as e:
            raise Exception(f"Error creating folder '{folder_name}': {str(e)}")

    def get_or_create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> Dict[str, str]:
        """
        Get existing folder or create if doesn't exist

        Args:
            folder_name: Name of the folder
            parent_id: Parent folder ID (optional)

        Returns:
            Dict with 'id' and 'url'
        """
        folder_id = self.find_folder_by_name(folder_name, parent_id)

        if folder_id:
            # Get webViewLink for existing folder
            try:
                get_params = {
                    'fileId': folder_id,
                    'fields': 'webViewLink'
                }

                # Add Shared Drive support
                if self.shared_drive_id:
                    get_params['supportsAllDrives'] = True

                folder = self.service.files().get(**get_params).execute()
                return {
                    'id': folder_id,
                    'url': folder.get('webViewLink')
                }
            except Exception as e:
                raise Exception(f"Error getting folder info: {str(e)}")
        else:
            return self.create_folder(folder_name, parent_id)

    def create_project_folder_structure(
        self,
        project_code: str,
        project_name: str,
        group: str
    ) -> Dict[str, Any]:
        """
        Create complete project folder structure in Google Drive

        Structure:
        04-Engagement/
          ├── Правая группа/ or Левая группа/
          │   └── 2169.CLI Название клиента/
          │       ├── 01-inbox/
          │       ├── 02-research/
          │       ├── 03-meetings/
          │       ├── 04-project-docs/
          │       └── 05-deliverables/

        Args:
            project_code: Project code (e.g., "2169.CLI.client")
            project_name: Client name
            group: 'left' or 'right'

        Returns:
            Dict with folder IDs and URLs
        """
        # Extract ticker
        ticker = project_code.split(".")[1] if "." in project_code else "XXX"

        # Get or create root folder: 04-Engagement
        root = self.get_or_create_folder("04-Engagement")

        # Get or create group folder
        group_name = "Правая группа" if group == "right" else "Левая группа"
        group_folder = self.get_or_create_folder(group_name, root['id'])

        # Create project folder: "2169.CLI Название клиента"
        project_folder_name = f"{project_code.upper()} {project_name}"
        project_folder = self.create_folder(project_folder_name, group_folder['id'])

        # Create subfolders
        subfolders = [
            f"{ticker}.01-inbox",
            f"{ticker}.02-research",
            f"{ticker}.03-meetings",
            f"{ticker}.04-project-docs",
            f"{ticker}.05-deliverables"
        ]

        subfolder_ids = {}
        for subfolder_name in subfolders:
            subfolder = self.create_folder(subfolder_name, project_folder['id'])
            subfolder_ids[subfolder_name] = subfolder

        return {
            'root': root,
            'group_folder': group_folder,
            'project_folder': project_folder,
            'subfolders': subfolder_ids
        }

    def upload_file(
        self,
        file_path: Path,
        folder_id: str,
        file_name: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Upload a file to Google Drive

        Args:
            file_path: Path to file to upload
            folder_id: Destination folder ID
            file_name: Custom file name (optional, uses original if not provided)

        Returns:
            Dict with 'id' and 'webViewLink'
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if file_name is None:
            file_name = file_path.name

        # Determine MIME type
        mime_types = {
            '.md': 'text/markdown',
            '.txt': 'text/plain',
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        }
        file_extension = file_path.suffix.lower()
        mime_type = mime_types.get(file_extension, 'application/octet-stream')

        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }

        try:
            media = MediaFileUpload(str(file_path), mimetype=mime_type)

            create_params = {
                'body': file_metadata,
                'media_body': media,
                'fields': 'id, webViewLink'
            }

            # Add Shared Drive support
            if self.shared_drive_id:
                create_params['supportsAllDrives'] = True

            file = self.service.files().create(**create_params).execute()

            return {
                'id': file.get('id'),
                'url': file.get('webViewLink')
            }
        except Exception as e:
            raise Exception(f"Error uploading file '{file_name}': {str(e)}")

    def upload_project_files(
        self,
        files_dict: Dict[str, Path],
        folder_structure: Dict[str, Any],
        ticker: str
    ) -> Dict[str, Dict[str, str]]:
        """
        Upload all project files to appropriate folders

        Args:
            files_dict: Dict from save_project_files() with file paths
            folder_structure: Dict from create_project_folder_structure()
            ticker: Project ticker

        Returns:
            Dict with uploaded file info
        """
        uploaded = {}

        # Upload adminscale to project root
        if 'adminscale' in files_dict:
            uploaded['adminscale'] = self.upload_file(
                files_dict['adminscale'],
                folder_structure['project_folder']['id']
            )

        # Upload README to project root
        if 'readme' in files_dict:
            uploaded['readme'] = self.upload_file(
                files_dict['readme'],
                folder_structure['project_folder']['id']
            )

        # Upload PERT to 04-project-docs
        if 'pert' in files_dict:
            project_docs_folder = folder_structure['subfolders'][f"{ticker}.04-project-docs"]['id']
            uploaded['pert'] = self.upload_file(
                files_dict['pert'],
                project_docs_folder
            )

        # Upload contract to 01-inbox
        if 'contract' in files_dict:
            inbox_folder = folder_structure['subfolders'][f"{ticker}.01-inbox"]['id']
            uploaded['contract'] = self.upload_file(
                files_dict['contract'],
                inbox_folder
            )

        return uploaded


# Singleton instance
_google_drive_client = None


def get_google_drive_client(credentials_path: str = None, token_path: str = None, shared_drive_id: str = None) -> GoogleDriveClient:
    """Get Google Drive client singleton"""
    global _google_drive_client
    if _google_drive_client is None:
        _google_drive_client = GoogleDriveClient(credentials_path, token_path, shared_drive_id)
    return _google_drive_client
