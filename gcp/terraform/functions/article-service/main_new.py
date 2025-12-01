import json
import os
import time
import uuid
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import jwt
from google.cloud import firestore
import functions_framework
from flask import Request

# Initialize Firestore client
db = firestore.Client()

# Collections
ARTICLES_COLLECTION = "articles"
TAGS_COLLECTION = "tags"
PROFILES_COLLECTION = "profiles"
COMMENTS_COLLECTION = "comments"

# JWT Configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "secret")
JWT_ALGORITHM = "HS256"
JWT_EXP_DELTA_SECONDS = 86400  # 24 hours

# Pagination defaults
DEFAULT_LIMIT = 20
DEFAULT_OFFSET = 0
