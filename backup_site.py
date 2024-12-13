import os
import shutil
from datetime import datetime
import zipfile

def backup_website():
    # Create backup directory
    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    # Create timestamp for backup name
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f'reviewsphere_backup_{timestamp}'
    
    # Create zip file
    zip_path = os.path.join(backup_dir, f'{backup_name}.zip')
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Walk through all directories and files
        for root, dirs, files in os.walk(os.path.dirname(os.path.abspath(__file__))):
            # Skip the backups directory and __pycache__
            if 'backups' in root or '__pycache__' in root:
                continue
                
            for file in files:
                # Skip .pyc files and the database
                if file.endswith('.pyc') or file == 'blog.db':
                    continue
                    
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.dirname(os.path.abspath(__file__)))
                zipf.write(file_path, arcname)
    
    print(f'Backup created successfully: {zip_path}')

if __name__ == '__main__':
    backup_website()
