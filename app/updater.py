"""
Update checker and self-update module for Tonys Onvif-RTSP Server
Handles checking GitHub for updates, downloading releases, and applying updates
"""

import os
import sys
import json
import shutil
import zipfile
import tempfile
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Callable

from app.version import CURRENT_VERSION, is_newer_version

# GitHub repository information
GITHUB_OWNER = "BigTonyTones"
GITHUB_REPO = "Tonys-Onvf-RTSP-Server"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"

# Directories and files to exclude from updates
EXCLUDE_FROM_UPDATE = [
    'camera_config.json',
    'mediamtx.yml',
    'mediamtx',
    'mediamtx.exe',
    'ffmpeg',
    'venv',
    'backups',
    '.git',
    '__pycache__',
    '*.pyc',
    '.env'
]

class UpdateChecker:
    """Handles checking for and applying updates from GitHub"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent.absolute()
        self.backup_dir = self.base_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
    
    def check_for_updates(self) -> Optional[Dict]:
        """
        Check GitHub for available updates
        
        Returns:
            Dictionary with update info if available, None otherwise
            {
                'update_available': bool,
                'current_version': str,
                'latest_version': str,
                'release_notes': str,
                'download_url': str,
                'published_at': str
            }
        """
        try:
            response = requests.get(GITHUB_API_URL, timeout=10)
            response.raise_for_status()
            
            release_data = response.json()
            latest_version = release_data.get('tag_name', '').lstrip('v')
            
            if not latest_version:
                return None
            
            update_available = is_newer_version(CURRENT_VERSION, latest_version)
            
            # Get download URL for the zipball
            download_url = release_data.get('zipball_url')
            
            return {
                'update_available': update_available,
                'current_version': CURRENT_VERSION,
                'latest_version': latest_version,
                'release_notes': release_data.get('body', 'No release notes available.'),
                'download_url': download_url,
                'published_at': release_data.get('published_at', ''),
                'release_name': release_data.get('name', f'v{latest_version}')
            }
            
        except requests.RequestException as e:
            print(f"Error checking for updates: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error checking for updates: {e}")
            return None
    
    def download_update(self, download_url: str, progress_callback: Optional[Callable] = None) -> Optional[Path]:
        """
        Download update ZIP from GitHub
        
        Args:
            download_url: URL to download the release ZIP
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Path to downloaded ZIP file, or None on failure
        """
        try:
            # Create temporary file for download
            temp_dir = Path(tempfile.gettempdir())
            zip_path = temp_dir / f"tonys_onvif_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            
            # Download with progress tracking
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            progress_callback('downloading', progress)
            
            return zip_path
            
        except Exception as e:
            print(f"Error downloading update: {e}")
            return None
    
    def create_backup(self) -> Optional[Path]:
        """
        Create backup of current installation
        
        Returns:
            Path to backup directory, or None on failure
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.backup_dir / f"backup_v{CURRENT_VERSION}_{timestamp}"
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Backup app directory
            app_backup = backup_path / "app"
            shutil.copytree(self.base_dir / "app", app_backup, 
                          ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            
            # Backup startup scripts
            for script in ['start_onvif_server.bat', 'start_ubuntu_25.sh', 'run.py']:
                script_path = self.base_dir / script
                if script_path.exists():
                    shutil.copy2(script_path, backup_path / script)
            
            # Save backup metadata
            metadata = {
                'version': CURRENT_VERSION,
                'timestamp': timestamp,
                'backup_date': datetime.now().isoformat()
            }
            
            with open(backup_path / 'backup_info.json', 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"Backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            print(f"Error creating backup: {e}")
            return None
    
    def apply_update(self, zip_path: Path, progress_callback: Optional[Callable] = None) -> bool:
        """
        Apply update from downloaded ZIP file
        
        Args:
            zip_path: Path to downloaded ZIP file
            progress_callback: Optional callback for progress updates
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Create backup first
            if progress_callback:
                progress_callback('backing_up', 0)
            
            backup_path = self.create_backup()
            if not backup_path:
                return False
            
            # Extract ZIP to temporary directory
            if progress_callback:
                progress_callback('extracting', 0)
            
            temp_extract = Path(tempfile.gettempdir()) / f"tonys_onvif_extract_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            temp_extract.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_extract)
            
            # Find the extracted directory (GitHub zips have a root folder)
            extracted_dirs = [d for d in temp_extract.iterdir() if d.is_dir()]
            if not extracted_dirs:
                print("Error: No directory found in extracted ZIP")
                return False
            
            source_dir = extracted_dirs[0]
            
            # Apply updates
            if progress_callback:
                progress_callback('applying', 0)
            
            # Update app directory
            app_source = source_dir / "app"
            if app_source.exists():
                # Remove old app files (except excluded ones)
                app_dest = self.base_dir / "app"
                for item in app_dest.iterdir():
                    if item.name not in EXCLUDE_FROM_UPDATE and not item.name.startswith('.'):
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir() and item.name == '__pycache__':
                            shutil.rmtree(item)
                
                # Copy new app files
                for item in app_source.iterdir():
                    if item.name not in EXCLUDE_FROM_UPDATE:
                        dest = app_dest / item.name
                        if item.is_file():
                            shutil.copy2(item, dest)
                        elif item.is_dir() and item.name != '__pycache__':
                            if dest.exists():
                                shutil.rmtree(dest)
                            shutil.copytree(item, dest, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            
            # Update startup scripts
            for script in ['start_onvif_server.bat', 'start_ubuntu_25.sh', 'run.py']:
                script_source = source_dir / script
                if script_source.exists():
                    dest_script = self.base_dir / script
                    shutil.copy2(script_source, dest_script)
                    
                    # Set executable permissions on Linux for shell scripts
                    if sys.platform.startswith('linux') and script.endswith('.sh'):
                        os.chmod(dest_script, 0o755)
            
            # Update README if exists
            readme_source = source_dir / "README.md"
            if readme_source.exists():
                shutil.copy2(readme_source, self.base_dir / "README.md")
            
            # Cleanup
            shutil.rmtree(temp_extract, ignore_errors=True)
            zip_path.unlink(missing_ok=True)
            
            if progress_callback:
                progress_callback('complete', 100)
            
            print("Update applied successfully!")
            return True
            
        except Exception as e:
            print(f"Error applying update: {e}")
            return False
    
    def rollback_update(self, backup_path: Path) -> bool:
        """
        Rollback to a previous backup
        
        Args:
            backup_path: Path to backup directory
            
        Returns:
            True if rollback successful, False otherwise
        """
        try:
            if not backup_path.exists():
                print(f"Backup not found: {backup_path}")
                return False
            
            # Restore app directory
            app_backup = backup_path / "app"
            if app_backup.exists():
                app_dest = self.base_dir / "app"
                
                # Remove current app files
                for item in app_dest.iterdir():
                    if item.name not in EXCLUDE_FROM_UPDATE and not item.name.startswith('.'):
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir() and item.name == '__pycache__':
                            shutil.rmtree(item)
                
                # Restore from backup
                for item in app_backup.iterdir():
                    dest = app_dest / item.name
                    if item.is_file():
                        shutil.copy2(item, dest)
                    elif item.is_dir():
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.copytree(item, dest)
            
            # Restore startup scripts
            for script in ['start_onvif_server.bat', 'start_ubuntu_25.sh', 'run.py']:
                script_backup = backup_path / script
                if script_backup.exists():
                    dest_script = self.base_dir / script
                    shutil.copy2(script_backup, dest_script)
                    
                    # Set executable permissions on Linux for shell scripts
                    if sys.platform.startswith('linux') and script.endswith('.sh'):
                        os.chmod(dest_script, 0o755)
            
            print(f"Rollback successful from backup: {backup_path}")
            return True
            
        except Exception as e:
            print(f"Error during rollback: {e}")
            return False
    
    def list_backups(self) -> list:
        """
        List available backups
        
        Returns:
            List of backup information dictionaries
        """
        backups = []
        
        try:
            for backup_dir in self.backup_dir.iterdir():
                if backup_dir.is_dir() and backup_dir.name.startswith('backup_'):
                    info_file = backup_dir / 'backup_info.json'
                    if info_file.exists():
                        with open(info_file, 'r') as f:
                            info = json.load(f)
                            info['path'] = str(backup_dir)
                            backups.append(info)
        except Exception as e:
            print(f"Error listing backups: {e}")
        
        return sorted(backups, key=lambda x: x.get('timestamp', ''), reverse=True)


# Convenience functions
def check_for_updates() -> Optional[Dict]:
    """Check for available updates"""
    checker = UpdateChecker()
    return checker.check_for_updates()

def download_and_apply_update(download_url: str, progress_callback: Optional[Callable] = None) -> bool:
    """Download and apply an update"""
    checker = UpdateChecker()
    
    zip_path = checker.download_update(download_url, progress_callback)
    if not zip_path:
        return False
    
    return checker.apply_update(zip_path, progress_callback)
