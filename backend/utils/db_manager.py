"""
Centralized Database Manager for ChromaDB Storage
Standardizes locations and management of all vector databases
"""

import logging
from pathlib import Path
from typing import Dict, Optional, List
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Centralized manager for all ChromaDB vector databases
    Provides standardized locations and management
    """
    
    # Standard database locations
    BASE_DB_DIR = Path("./db/chroma")
    ANALYSIS_DB_DIR = Path("../analysis_databases")
    
    # Database types and their standard subdirectories
    DB_TYPES = {
        'classification': 'classification',
        'risk_analysis': 'risk_analysis', 
        'validation': 'validation',
        'comparison': 'comparison',
        'proposal_comparison': 'proposal_comparison',
        'extraction': 'extraction'
    }
    
    def __init__(self):
        """Initialize the database manager and create directory structure"""
        self.ensure_directory_structure()
        
    def ensure_directory_structure(self):
        """Ensure all standard directories exist"""
        try:
            # Create base ChromaDB directory
            self.BASE_DB_DIR.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories for each database type
            for db_type, subdir in self.DB_TYPES.items():
                db_path = self.BASE_DB_DIR / subdir
                db_path.mkdir(parents=True, exist_ok=True)
            
            # Create analysis databases directory
            self.ANALYSIS_DB_DIR.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Database directory structure created at {self.BASE_DB_DIR}")
            
        except Exception as e:
            logger.error(f"Error creating database directories: {e}")
    
    def get_db_path(self, db_type: str, document_id: Optional[str] = None) -> Path:
        """
        Get standardized path for a database
        
        Args:
            db_type: Type of database (classification, risk_analysis, etc.)
            document_id: Optional document ID for document-specific databases
            
        Returns:
            Standardized path for the database
        """
        if db_type not in self.DB_TYPES:
            raise ValueError(f"Unknown database type: {db_type}. Available types: {list(self.DB_TYPES.keys())}")
        
        base_path = self.BASE_DB_DIR / self.DB_TYPES[db_type]
        
        if document_id:
            # Document-specific database
            return base_path / document_id
        else:
            # Global database
            return base_path / "global"
    
    def get_analysis_db_path(self, document_id: str) -> Path:
        """Get path for analysis results storage"""
        return self.ANALYSIS_DB_DIR / document_id
    
    def list_databases(self, db_type: Optional[str] = None) -> Dict[str, List[str]]:
        """
        List all databases by type
        
        Args:
            db_type: Optional filter by database type
            
        Returns:
            Dictionary with database types and their instances
        """
        databases = {}
        
        types_to_check = [db_type] if db_type else self.DB_TYPES.keys()
        
        for dtype in types_to_check:
            if dtype in self.DB_TYPES:
                db_path = self.BASE_DB_DIR / self.DB_TYPES[dtype]
                if db_path.exists():
                    # List all subdirectories (document IDs)
                    subdirs = [d.name for d in db_path.iterdir() if d.is_dir()]
                    databases[dtype] = subdirs
                else:
                    databases[dtype] = []
        
        return databases
    
    def cleanup_old_databases(self, days_old: int = 30) -> Dict[str, int]:
        """
        Clean up databases older than specified days
        
        Args:
            days_old: Remove databases older than this many days
            
        Returns:
            Dictionary with cleanup statistics
        """
        cleanup_stats = {'removed': 0, 'errors': 0, 'total_checked': 0}
        
        try:
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            
            for db_type in self.DB_TYPES:
                db_base_path = self.BASE_DB_DIR / self.DB_TYPES[db_type]
                
                if not db_base_path.exists():
                    continue
                
                for db_dir in db_base_path.iterdir():
                    if db_dir.is_dir():
                        cleanup_stats['total_checked'] += 1
                        
                        try:
                            # Check modification time
                            mod_time = db_dir.stat().st_mtime
                            
                            if mod_time < cutoff_time:
                                # Remove old database
                                import shutil
                                shutil.rmtree(db_dir)
                                cleanup_stats['removed'] += 1
                                logger.info(f"Removed old database: {db_dir}")
                                
                        except Exception as e:
                            cleanup_stats['errors'] += 1
                            logger.error(f"Error cleaning up {db_dir}: {e}")
            
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Error during database cleanup: {e}")
            cleanup_stats['errors'] += 1
            return cleanup_stats
    
    def get_database_info(self) -> Dict[str, any]:
        """Get comprehensive information about all databases"""
        
        info = {
            'base_directory': str(self.BASE_DB_DIR),
            'analysis_directory': str(self.ANALYSIS_DB_DIR),
            'database_types': self.DB_TYPES,
            'databases': {},
            'total_size_mb': 0,
            'total_databases': 0
        }
        
        try:
            # Calculate sizes and counts
            total_size = 0
            total_count = 0
            
            for db_type in self.DB_TYPES:
                db_path = self.BASE_DB_DIR / self.DB_TYPES[db_type]
                
                if db_path.exists():
                    # Calculate size
                    size = sum(f.stat().st_size for f in db_path.rglob('*') if f.is_file())
                    
                    # Count databases
                    count = len([d for d in db_path.iterdir() if d.is_dir()])
                    
                    info['databases'][db_type] = {
                        'path': str(db_path),
                        'size_mb': round(size / (1024 * 1024), 2),
                        'count': count,
                        'exists': True
                    }
                    
                    total_size += size
                    total_count += count
                else:
                    info['databases'][db_type] = {
                        'path': str(db_path),
                        'size_mb': 0,
                        'count': 0,
                        'exists': False
                    }
            
            info['total_size_mb'] = round(total_size / (1024 * 1024), 2)
            info['total_databases'] = total_count
            
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            info['error'] = str(e)
        
        return info
    
    def migrate_old_databases(self) -> Dict[str, int]:
        """
        Migrate databases from old locations to standardized locations
        
        Returns:
            Migration statistics
        """
        migration_stats = {'migrated': 0, 'errors': 0, 'skipped': 0}
        
        try:
            # Look for old database patterns
            current_dir = Path(".")
            old_patterns = [
                "*classification*",
                "*risk*",
                "*validation*", 
                "*comparison*",
                "*db"
            ]
            
            for pattern in old_patterns:
                for old_db_path in current_dir.glob(pattern):
                    if old_db_path.is_dir() and old_db_path != self.BASE_DB_DIR:
                        try:
                            # Determine database type from name
                            db_name = old_db_path.name.lower()
                            db_type = None
                            
                            for dtype in self.DB_TYPES:
                                if dtype in db_name or dtype.replace('_', '') in db_name:
                                    db_type = dtype
                                    break
                            
                            if db_type:
                                # Move to standardized location
                                new_path = self.get_db_path(db_type, "migrated_" + old_db_path.name)
                                
                                if not new_path.exists():
                                    import shutil
                                    shutil.move(str(old_db_path), str(new_path))
                                    migration_stats['migrated'] += 1
                                    logger.info(f"Migrated {old_db_path} -> {new_path}")
                                else:
                                    migration_stats['skipped'] += 1
                                    logger.warning(f"Target exists, skipped: {new_path}")
                            else:
                                migration_stats['skipped'] += 1
                                logger.warning(f"Could not determine type for: {old_db_path}")
                                
                        except Exception as e:
                            migration_stats['errors'] += 1
                            logger.error(f"Error migrating {old_db_path}: {e}")
            
            return migration_stats
            
        except Exception as e:
            logger.error(f"Error during database migration: {e}")
            migration_stats['errors'] += 1
            return migration_stats

# Global instance
db_manager = DatabaseManager()

def get_standard_db_path(db_type: str, document_id: Optional[str] = None) -> Path:
    """
    Convenience function to get standardized database path
    
    Args:
        db_type: Type of database 
        document_id: Optional document ID
        
    Returns:
        Standardized database path
    """
    return db_manager.get_db_path(db_type, document_id)

def get_analysis_path(document_id: str) -> Path:
    """
    Convenience function to get analysis results path
    
    Args:
        document_id: Document ID
        
    Returns:
        Analysis results path
    """
    return db_manager.get_analysis_db_path(document_id)
