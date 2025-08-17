# modules/logger.py
import logging
import os
import datetime
import sys
import codecs
from modules.db_manager import get_connection, ConnectionContext
from modules.Login import current_user

# Set up file logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, 'app.log')

# Configure the logger
logger = logging.getLogger('SalesSystem')
logger.setLevel(logging.INFO)

# File handler for general logging - use UTF-8 encoding
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console handler with UTF-8 encoding
# This fixes encoding errors when logging non-Latin characters
class EncodedStdoutHandler(logging.StreamHandler):
    def __init__(self, stream=None):
        # Create a UTF-8 text wrapper for stdout if running on Windows
        if stream is None and sys.platform == 'win32':
            stream = codecs.getwriter('utf-8')(sys.stdout.buffer)
        super().__init__(stream)
        
# Add console handler if running in console mode
if not hasattr(sys, 'frozen'):  # Not a frozen executable
    console_handler = EncodedStdoutHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# Database logger for user activity
def log_activity(action, user_id=None):
    """
    Log user activity to the ActivityLog table in the database.
    
    Args:
        action (str): The action to log
        user_id (int, optional): User ID to log the action for. 
                                If None, gets the current logged-in user.
    
    Returns:
        bool: True if the log was successful, False otherwise
    """
    try:
        # Get current user ID if not provided
        if user_id is None:
            user = current_user.get("UserID")
            if not user:
                logger.warning(f"Could not log action '{action}' - No user logged in")
                return False
            user_id = user
            
        # Get current timestamp
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Use ConnectionContext for safe connection handling
        with ConnectionContext() as conn:
            cur = conn.cursor()
            
            # Insert the activity log
            cur.execute("""
                INSERT INTO ActivityLog (UserID, Action, DateTime)
                VALUES (?, ?, ?)
            """, (user_id, action, now))
            
            # Commit transaction
            conn.commit()
        
        # Also log to file
        logger.info(f"User {user_id}: {action}")
        
        return True
    except Exception as e:
        logger.error(f"Error logging activity: {e}")
        return False
