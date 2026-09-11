"""Unified Storage and Data Access Layer for AI Recruitment Platform.

Provides thread-safe file-based persistent repositories for:
- Candidates (`data/candidates/`)
- Jobs (`data/jobs/`)
- Applications (`data/applications/`)
"""
import os
import json
import uuid
import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CANDIDATES_DIR = os.path.join(BASE_DIR, "data", "candidates")
JOBS_DIR = os.path.join(BASE_DIR, "data", "jobs")
APPLICATIONS_DIR = os.path.join(BASE_DIR, "data", "applications")

os.makedirs(CANDIDATES_DIR, exist_ok=True)
os.makedirs(JOBS_DIR, exist_ok=True)
os.makedirs(APPLICATIONS_DIR, exist_ok=True)
