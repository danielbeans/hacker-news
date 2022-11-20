"""
Creates better access to functions within utilities module
"""
from .login_manager import (
    session_login,
    login_manager,
    oauth,
    init_oauth,
    admin_required,
)
from .news_api import *
