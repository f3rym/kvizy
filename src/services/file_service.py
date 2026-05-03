import os
from pathlib import Path
from typing import List, Dict, Optional
from src.utils.logger import logger


class FileService:
    """Service for safe file system operations"""

    def __init__(self):
        # Allowed directories (whitelist)
        self.allowed_dirs = [
            '/app/data',
            '/app/workspace'
        ]

        # Forbidden directories (blacklist)
        self.blacklist = [
            '/etc', '/sys', '/proc', '/root', '/boot',
            '/bin', '/sbin', '/usr', '/var', '/tmp'
        ]

        self.max_file_size = 20 * 1024 * 1024  # 20MB

    def validate_path(self, path: str) -> bool:
        """
        Validate that path is safe to access

        Args:
            path: Path to validate

        Returns:
            True if path is safe
        """
        try:
            # Normalize path (resolve .., symlinks, etc)
            real_path = os.path.realpath(path)

            # Check blacklist
            for forbidden in self.blacklist:
                if real_path.startswith(forbidden):
                    logger.warning(f"Path blocked by blacklist: {real_path}")
                    return False

            # Check whitelist
            allowed = any(real_path.startswith(allowed_dir) for allowed_dir in self.allowed_dirs)
            if not allowed:
                logger.warning(f"Path not in whitelist: {real_path}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating path: {e}")
            return False

    async def list_files(self, path: str) -> List[Dict]:
        """
        List files in directory

        Args:
            path: Directory path

        Returns:
            List of file info dicts
        """
        if not self.validate_path(path):
            raise PermissionError("Access denied")

        if not os.path.exists(path):
            raise FileNotFoundError(f"Path not found: {path}")

        if not os.path.isdir(path):
            raise NotADirectoryError(f"Not a directory: {path}")

        files = []
        for item in sorted(os.listdir(path)):
            full_path = os.path.join(path, item)
            try:
                stat = os.stat(full_path)
                files.append({
                    'name': item,
                    'path': full_path,
                    'is_dir': os.path.isdir(full_path),
                    'size': stat.st_size if os.path.isfile(full_path) else 0,
                    'modified': stat.st_mtime
                })
            except Exception as e:
                logger.error(f"Error getting info for {full_path}: {e}")

        return files

    async def read_file(self, path: str, max_chars: int = 5000) -> str:
        """
        Read file content

        Args:
            path: File path
            max_chars: Maximum characters to read

        Returns:
            File content
        """
        if not self.validate_path(path):
            raise PermissionError("Access denied")

        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")

        if not os.path.isfile(path):
            raise IsADirectoryError(f"Not a file: {path}")

        # Check file size
        size = os.path.getsize(path)
        if size > self.max_file_size:
            raise ValueError(f"File too large: {size} bytes (max {self.max_file_size})")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read(max_chars)

            logger.info(f"Read file: {path} ({len(content)} chars)")
            return content

        except UnicodeDecodeError:
            raise ValueError("File is not a text file")

    async def write_file(self, path: str, content: str) -> bool:
        """
        Write content to file

        Args:
            path: File path
            content: Content to write

        Returns:
            True if successful
        """
        if not self.validate_path(path):
            raise PermissionError("Access denied")

        # Check content size
        if len(content.encode('utf-8')) > self.max_file_size:
            raise ValueError(f"Content too large (max {self.max_file_size} bytes)")

        try:
            # Create parent directory if needed
            parent = os.path.dirname(path)
            if parent and not os.path.exists(parent):
                os.makedirs(parent, exist_ok=True)

            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"Wrote file: {path} ({len(content)} chars)")
            return True

        except Exception as e:
            logger.error(f"Error writing file: {e}")
            raise

    async def delete_file(self, path: str) -> bool:
        """
        Delete file

        Args:
            path: File path

        Returns:
            True if successful
        """
        if not self.validate_path(path):
            raise PermissionError("Access denied")

        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")

        if os.path.isdir(path):
            raise IsADirectoryError("Cannot delete directory (use rmdir)")

        try:
            os.remove(path)
            logger.info(f"Deleted file: {path}")
            return True

        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            raise

    async def create_directory(self, path: str) -> bool:
        """
        Create directory

        Args:
            path: Directory path

        Returns:
            True if successful
        """
        if not self.validate_path(path):
            raise PermissionError("Access denied")

        try:
            os.makedirs(path, exist_ok=True)
            logger.info(f"Created directory: {path}")
            return True

        except Exception as e:
            logger.error(f"Error creating directory: {e}")
            raise

    async def get_file_info(self, path: str) -> Dict:
        """Get detailed file information"""
        if not self.validate_path(path):
            raise PermissionError("Access denied")

        if not os.path.exists(path):
            raise FileNotFoundError(f"Path not found: {path}")

        stat = os.stat(path)

        return {
            'path': path,
            'name': os.path.basename(path),
            'is_dir': os.path.isdir(path),
            'is_file': os.path.isfile(path),
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'created': stat.st_ctime,
            'permissions': oct(stat.st_mode)[-3:]
        }


# Global file service instance
file_service = FileService()
