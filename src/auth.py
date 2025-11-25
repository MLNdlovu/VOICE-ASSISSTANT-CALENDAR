"""
Authentication and User Management Module

Handles user registration, login, password validation, and user storage.
"""

import re
import json
import sqlite3
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from typing import Optional, Tuple
from werkzeug.security import generate_password_hash, check_password_hash


@dataclass
class User:
    """User model."""
    id: int
    email: str
    password_hash: str
    timezone: str = 'UTC'
    preferences: dict = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AuthManager:
    """User authentication and storage manager."""
    
    def __init__(self, db_path: str = 'app.db'):
        """
        Initialize auth manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Create users table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                timezone TEXT DEFAULT 'UTC',
                preferences TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid, False otherwise
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r'[0-9]', password):
            return False, "Password must contain at least one digit"
        return True, "Valid"
    
    def register_user(
        self, 
        email: str, 
        password: str, 
        timezone: str = 'UTC'
    ) -> Tuple[bool, str, Optional[User]]:
        """
        Register new user.
        
        Args:
            email: User email
            password: User password (will be hashed)
            timezone: User timezone (default: UTC)
            
        Returns:
            Tuple of (success, message, user)
        """
        # Validate email
        if not self.validate_email(email):
            return False, "Invalid email format", None
        
        # Validate password
        valid, msg = self.validate_password(password)
        if not valid:
            return False, msg, None
        
        # Check if user exists
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE email = ?', (email,))
        if c.fetchone():
            conn.close()
            return False, "Email already registered", None
        
        # Hash password and create user
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        try:
            c.execute(
                'INSERT INTO users (email, password_hash, timezone) VALUES (?, ?, ?)',
                (email, password_hash, timezone)
            )
            conn.commit()
            user_id = c.lastrowid
            conn.close()
            
            user = User(user_id, email, password_hash, timezone)
            return True, "User registered successfully", user
        except Exception as e:
            conn.close()
            return False, f"Registration failed: {str(e)}", None
    
    def login_user(self, email: str, password: str) -> Tuple[bool, str, Optional[User]]:
        """
        Login user.
        
        Args:
            email: User email
            password: User password (will be verified)
            
        Returns:
            Tuple of (success, message, user)
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            'SELECT id, email, password_hash, timezone, preferences FROM users WHERE email = ?',
            (email,)
        )
        row = c.fetchone()
        conn.close()
        
        if not row:
            return False, "Invalid email or password", None
        
        user_id, email_db, password_hash, timezone, prefs_json = row
        
        if not check_password_hash(password_hash, password):
            return False, "Invalid email or password", None
        
        # Parse preferences JSON
        try:
            preferences = json.loads(prefs_json) if prefs_json else {}
        except:
            preferences = {}
        
        user = User(user_id, email_db, password_hash, timezone, preferences)
        return True, "Login successful", user
    
    def get_user(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User object or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            'SELECT id, email, password_hash, timezone, preferences FROM users WHERE id = ?',
            (user_id,)
        )
        row = c.fetchone()
        conn.close()
        
        if not row:
            return None
        
        user_id, email, password_hash, timezone, prefs_json = row
        
        try:
            preferences = json.loads(prefs_json) if prefs_json else {}
        except:
            preferences = {}
        
        return User(user_id, email, password_hash, timezone, preferences)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            email: User email
            
        Returns:
            User object or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            'SELECT id, email, password_hash, timezone, preferences FROM users WHERE email = ?',
            (email,)
        )
        row = c.fetchone()
        conn.close()
        
        if not row:
            return None
        
        user_id, email_db, password_hash, timezone, prefs_json = row
        
        try:
            preferences = json.loads(prefs_json) if prefs_json else {}
        except:
            preferences = {}
        
        return User(user_id, email_db, password_hash, timezone, preferences)
    
    def update_preferences(self, user_id: int, preferences: dict) -> bool:
        """
        Update user preferences.
        
        Args:
            user_id: User ID
            preferences: Preferences dict to store
            
        Returns:
            True if update successful
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            'UPDATE users SET preferences = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (json.dumps(preferences), user_id)
        )
        conn.commit()
        success = c.rowcount > 0
        conn.close()
        return success
    
    def update_timezone(self, user_id: int, timezone: str) -> bool:
        """
        Update user timezone.
        
        Args:
            user_id: User ID
            timezone: Timezone string (e.g., 'America/New_York')
            
        Returns:
            True if update successful
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            'UPDATE users SET timezone = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (timezone, user_id)
        )
        conn.commit()
        success = c.rowcount > 0
        conn.close()
        return success
    
    def change_password(
        self, 
        user_id: int, 
        old_password: str, 
        new_password: str
    ) -> Tuple[bool, str]:
        """
        Change user password.
        
        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password
            
        Returns:
            Tuple of (success, message)
        """
        # Get user
        user = self.get_user(user_id)
        if not user:
            return False, "User not found"
        
        # Verify old password
        if not check_password_hash(user.password_hash, old_password):
            return False, "Current password is incorrect"
        
        # Validate new password
        valid, msg = self.validate_password(new_password)
        if not valid:
            return False, msg
        
        # Update password
        new_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            'UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (new_hash, user_id)
        )
        conn.commit()
        success = c.rowcount > 0
        conn.close()
        
        return success, "Password changed successfully" if success else "Password update failed"
    
    def delete_user(self, user_id: int) -> bool:
        """
        Delete user account.
        
        Args:
            user_id: User ID
            
        Returns:
            True if deletion successful
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        success = c.rowcount > 0
        conn.close()
        return success
