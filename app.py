"""AI Recruitment Platform - Module 1: Resume Information Extraction
Streamlit Web Interface

Provides an interactive user interface to upload resumes (PDF, DOCX, TXT, JSON),
analyze and extract structured candidate profiles, inspect categorized skills,
review work experience and education timelines, and export structured JSON data.
"""
import os
import re
import json
import html
import hashlib
import time
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
load_dotenv(override=False)
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np

from services.llm.llm_factory import llm_config
from src.resume.pipeline import ResumeExtractionPipeline
from src.resume.profile_schema import (
    ParsingStatus,
    ExtractionConfidence,
    EmploymentStatus,
    EducationStatus,
    classify_education_record,
    classify_education,
    get_education_counts,
    get_education_classification,
    get_education_category,
    getEducationCategory,
    validate_education_consistency,
    get_education_display_title,
    normalize_education_record,
    normalize_publication,
    format_publication_metadata,
    join_publication_metadata,
    clean_publication_detail,
    normalize_profile_url,
    ProfileLink,
)
from src.validation.resume_validator import ResumeValidator
from src.recommendation.job_recommender import JobRoleRecommender
from src.classification.resume_classifier import ResumeClassifier
from src.matching.job_matcher import ResumeJobMatcher
from src.skills.skill_gap_analyzer import SkillGapAnalyzer
from src.ranking.candidate_ranker import CandidateRanker
from src.advanced_insights import (
    InterviewPerformancePredictor,
    CandidateSuccessPredictor,
    SalaryRangePredictor,
)


def make_href(url: Optional[str]) -> Optional[str]:
    """Return safe clickable href for UI presentation without altering source data."""
    if not url:
        return None
    url_s = str(url).strip()
    if re.search(r'\s', url_s):
        return None
    if url_s.startswith(("http://", "https://", "mailto:")):
        return url_s
    return f"https://{url_s}"


def render_profile_entry(platform_title: str, platform_key: str, p: Any) -> Optional[str]:
    """Renders a safe clickable profile link or clean plain text."""
    profiles_dict = getattr(p, "profiles", {}) or {}
    prof_entry = profiles_dict.get(platform_key)
    if not prof_entry:
        val = getattr(p, platform_key, None)
        if val:
            link_obj = normalize_profile_url(platform_key, val)
            prof_entry = link_obj.to_dict()
            
    if not prof_entry or not isinstance(prof_entry, dict):
        return None
        
    url = prof_entry.get("url")
    label = prof_entry.get("label") or prof_entry.get("display") or url
    if not label and not url:
        return None
        
    disp_label = re.sub(r'^(?:LeetCode|LinkedIn|GitHub|Kaggle|Portfolio|Personal\s+Website|Website)\s*[:\-]\s*', '', str(label), flags=re.IGNORECASE).strip()
    disp_label = disp_label or str(label)

    if url and prof_entry.get("valid_format", True):
        return f'**{platform_title}:** <a href="{html.escape(url)}" target="_blank" rel="noopener noreferrer" style="color: #60A5FA; text-decoration: underline; font-weight: 500;">{html.escape(disp_label)}</a>'
    elif disp_label:
        return f"**{platform_title}:** {html.escape(disp_label)}"
    return None


# Set Streamlit page configuration
st.set_page_config(
    page_title="AI Recruitment Platform | Resume Intelligence",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS styling inspired by NextRaise modern SaaS aesthetic
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

    /* =========================================================================
       1. GLOBAL DESIGN TOKENS & HIGH-CONTRAST CANVAS
       ========================================================================= */
    :root {
        --bg: #F8FAFC;
        --surface: #FFFFFF;
        --surface-soft: #F4F7FF;
        --navy: #172554;
        --text: #1E293B;
        --muted: #64748B;
        --border: #DBE4F0;
        --primary: #315EFB;
        --secondary: #5146E5;
        --success: #16A34A;
        --warning: #F59E0B;
        --danger: #EF4444;
    }

    /* Global Canvas & Typography */
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        background-color: #F8FAFC !important;
        color: #1E293B !important;
    }

    .stApp {
        background-image: radial-gradient(ellipse at 50% -10%, #EEF2FF 0%, #F8FAFC 60%) !important;
    }

    /* =========================================================================
       2. HIDE STREAMLIT BRANDING, TOOLBAR, FORK/GITHUB ICONS & CLOUD BADGES
       ========================================================================= */
    /* 1. Completely hide Streamlit default header toolbar, GitHub icon, Fork, Deploy, and Menu */
    #MainMenu,
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    .stAppDeployButton,
    header[data-testid="stHeader"] [data-testid="stToolbar"],
    header[data-testid="stHeader"] a[href*="github.com"],
    header[data-testid="stHeader"] button[title*="GitHub"],
    header[data-testid="stHeader"] button[title*="Fork"],
    div[class*="viewerBadge"],
    div[class*="ProfileBadge"],
    div[class*="manage-app"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        height: 0 !important;
        width: 0 !important;
        pointer-events: none !important;
    }

    /* 2. Streamlit Header - Make completely transparent and non-intrusive */
    header[data-testid="stHeader"],
    [data-testid="stHeader"],
    .stAppHeader {
        background-color: transparent !important;
        background: transparent !important;
        border-bottom: none !important;
        box-shadow: none !important;
        height: 0 !important;
        min-height: 0 !important;
        padding: 0 !important;
        pointer-events: none !important;
    }

    /* Keep the sidebar expand/collapse chevron accessible if sidebar is closed */
    header[data-testid="stHeader"] [data-testid="stSidebarCollapseButton"],
    header[data-testid="stHeader"] [data-testid="collapsedControl"],
    [data-testid="collapsedControl"] {
        pointer-events: auto !important;
        display: flex !important;
        visibility: visible !important;
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08) !important;
        z-index: 99999 !important;
    }

    /* 3. Hide Streamlit Footer and Cloud "Hosted with Streamlit" ribbon / avatar */
    footer,
    [data-testid="stFooter"],
    footer[data-testid="stFooter"],
    .reportview-container footer,
    a[href*="streamlit.io"],
    a[href*="share.streamlit.io"],
    div[class*="viewerBadge"],
    div[class*="floatingBadge"],
    div[data-testid="stBottomRight"],
    div:has(> a[href*="streamlit.io"]),
    div:has(> a[href*="share.streamlit.io"]),
    div[style*="bottom: 0px"][style*="right: 0px"],
    div[style*="bottom: 0"][style*="right: 0"],
    div[style*="bottom: 1rem"][style*="right: 1rem"],
    div[style*="bottom: 16px"][style*="right: 16px"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        height: 0 !important;
        pointer-events: none !important;
    }

    /* Adjust main content block top spacing cleanly */
    div[data-testid="stAppViewBlockContainer"] {
        padding-top: 1.5rem !important;
    }

    /* Custom top breadcrumb bar */
    .nr-top-bar {
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        gap: 16px !important;
        padding: 0.85rem 1.4rem !important;
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 14px !important;
        margin-top: 0.5rem !important;
        margin-bottom: 1.5rem !important;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03) !important;
        box-sizing: border-box !important;
        width: 100% !important;
        min-height: 58px !important;
    }

    .nr-top-bar p {
        margin: 0 !important;
        padding: 0 !important;
    }

    .nr-breadcrumb {
        font-size: 0.92rem !important;
        font-weight: 500 !important;
        color: #64748B !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        white-space: nowrap !important;
        min-width: 0 !important;
        flex: 1 1 auto !important;
        margin: 0 !important;
        line-height: 1.3 !important;
    }

    .nr-breadcrumb b {
        color: #0F172A !important;
        font-weight: 700 !important;
    }

    /* Status badge with flex, no-wrap, proper padding and vertical centering */
    .nr-status-badge {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 8px !important;
        padding: 0.45rem 1.15rem !important;
        border-radius: 9999px !important;
        font-size: 0.82rem !important;
        font-weight: 700 !important;
        line-height: 1.2 !important;
        white-space: nowrap !important;
        flex-shrink: 0 !important;
        box-sizing: border-box !important;
        min-width: fit-content !important;
        margin: 0 !important;
        margin-top: 2px !important; /* Moves badge slightly downward so it sits comfortably and vertically centered */
        align-self: center !important;
    }

    .nr-status-badge.ready {
        background: #EFF6FF !important;
        color: #2563EB !important;
        border: 1px solid #DBEAFE !important;
    }

    .nr-status-badge.verified {
        background: #ECFDF5 !important;
        color: #065F46 !important;
        border: 1px solid #A7F3D0 !important;
    }

    /* =========================================================================
       3. MODERN LIGHT SIDEBAR
       ========================================================================= */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        border-right: 1px solid #E2E8F0 !important;
        box-shadow: 2px 0 12px rgba(15, 23, 42, 0.02) !important;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span {
        color: #334155 !important;
    }

    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: #0F172A !important;
        font-weight: 800 !important;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] > div {
        gap: 6px;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        background: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 0.6rem 0.9rem !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        color: #475569 !important;
        transition: all 0.2s ease !important;
        margin-bottom: 2px !important;
        display: flex !important;
        align-items: center !important;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
        background: #EFF6FF !important;
        border-color: #BFDBFE !important;
        color: #1D4ED8 !important;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"],
    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.08) 0%, rgba(79, 70, 229, 0.06) 100%) !important;
        border-color: #3B82F6 !important;
        color: #1D4ED8 !important;
        font-weight: 700 !important;
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.1) !important;
    }

    /* =========================================================================
       4. JOB DESCRIPTION TEXTAREA & INPUTS (HIGH CONTRAST)
       ========================================================================= */
    .stTextArea textarea,
    div[data-baseweb="textarea"],
    div[data-baseweb="textarea"] textarea,
    div[data-baseweb="base-input"] textarea,
    [data-testid="stTextArea"] textarea {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        color: #172554 !important;
        border: 1.5px solid #DBE4F0 !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        font-size: 0.95rem !important;
        line-height: 1.6 !important;
        font-family: 'Inter', sans-serif !important;
        box-shadow: 0 1px 4px rgba(15, 23, 42, 0.04) !important;
    }

    .stTextArea textarea::placeholder,
    div[data-baseweb="textarea"] textarea::placeholder {
        color: #94A3B8 !important;
    }

    .stTextArea textarea:focus,
    div[data-baseweb="textarea"]:focus-within {
        border-color: #315EFB !important;
        box-shadow: 0 0 0 3px rgba(49, 94, 251, 0.15) !important;
        outline: none !important;
    }

    .stTextInput input,
    div[data-baseweb="input"] input,
    div[data-baseweb="base-input"] input,
    [data-testid="stTextInput"] input {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        color: #172554 !important;
        border: 1.5px solid #DBE4F0 !important;
        border-radius: 10px !important;
        padding: 0.65rem 0.9rem !important;
        font-size: 0.95rem !important;
    }

    .stTextInput input:focus,
    div[data-baseweb="input"]:focus-within {
        border-color: #315EFB !important;
        box-shadow: 0 0 0 3px rgba(49, 94, 251, 0.15) !important;
        outline: none !important;
    }

    /* Labels */
    label[data-testid="stWidgetLabel"],
    label[data-testid="stWidgetLabel"] p,
    .stTextArea label,
    .stTextInput label,
    .stSelectbox label {
        color: #0F172A !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
        letter-spacing: -0.01em !important;
        margin-bottom: 0.35rem !important;
    }

    /* =========================================================================
       5. RESUME UPLOAD AREA & UPLOADED FILE DISPLAY
       ========================================================================= */
    [data-testid="stFileUploader"],
    [data-testid="stFileUploader"] > section,
    [data-testid="stFileUploaderDropzone"],
    div[data-testid="stFileUploader"] section {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        border: 2px dashed #CBD5E1 !important;
        border-radius: 16px !important;
        padding: 1.75rem !important;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03) !important;
        transition: all 0.2s ease !important;
        box-sizing: border-box !important;
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
    }

    [data-testid="stFileUploader"] section:hover {
        border-color: #315EFB !important;
        background-color: #F8FAFC !important;
    }

    [data-testid="stFileUploader"] span,
    [data-testid="stFileUploader"] small,
    [data-testid="stFileUploader"] p,
    [data-testid="stFileUploaderDropzoneInstructions"],
    [data-testid="stFileUploaderDropzoneInstructions"] span {
        color: #475569 !important;
        font-weight: 500 !important;
    }

    [data-testid="stFileUploader"] svg {
        fill: #315EFB !important;
        color: #315EFB !important;
    }

    /* Uploaded File Pill / Record */
    [data-testid="stFileUploaderFile"],
    [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"],
    ul[data-testid="stFileUploaderFileList"] li,
    div[data-testid="stFileUploaderFileData"] {
        background-color: #F8FAFC !important;
        background: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        color: #0F172A !important;
        padding: 0.6rem 0.9rem !important;
    }

    [data-testid="stFileUploaderFileName"],
    [data-testid="stFileUploader"] [data-testid="stFileUploaderFileName"],
    [data-testid="stFileUploader"] [data-testid="stFileUploaderFileName"] span,
    ul[data-testid="stFileUploaderFileList"] li span {
        color: #0F172A !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
    }

    [data-testid="stFileUploader"] small,
    [data-testid="stFileUploader"] div[data-testid="stFileUploaderFileData"] small {
        color: #64748B !important;
        font-weight: 500 !important;
    }

    /* Browse Files button inside uploader */
    [data-testid="stFileUploader"] button {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        color: #315EFB !important;
        border: 1.5px solid #315EFB !important;
        border-radius: 9999px !important;
        font-weight: 700 !important;
        font-size: 0.88rem !important;
        padding: 0.45rem 1.3rem !important;
        transition: all 0.2s ease !important;
    }

    [data-testid="stFileUploader"] button:hover {
        background-color: #EFF6FF !important;
        background: #EFF6FF !important;
        border-color: #1D4ED8 !important;
        color: #1D4ED8 !important;
    }

    /* =========================================================================
       6. PRIMARY ACTION BUTTONS (BLUE-PURPLE GRADIENT, PURE WHITE TEXT)
       ========================================================================= */
    .stButton > button[kind="primary"],
    .stButton > button[type="primary"],
    div.stButton > button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #315EFB 0%, #5146E5 100%) !important;
        color: #FFFFFF !important;
        border-radius: 9999px !important;
        border: none !important;
        font-weight: 700 !important;
        font-size: 0.98rem !important;
        padding: 0.7rem 2rem !important;
        box-shadow: 0 4px 14px 0 rgba(49, 94, 251, 0.38) !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button[kind="primary"]:hover,
    .stButton > button[type="primary"]:hover,
    div.stButton > button[data-testid="baseButton-primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px 0 rgba(49, 94, 251, 0.48) !important;
        color: #FFFFFF !important;
    }

    .stButton > button[kind="primary"] p,
    .stButton > button[kind="primary"] span,
    .stButton > button[type="primary"] p,
    .stButton > button[type="primary"] span,
    div.stButton > button[data-testid="baseButton-primary"] p {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    /* Secondary action buttons */
    .stButton > button[kind="secondary"],
    .stButton > button:not([kind="primary"]):not([type="primary"]),
    div.stButton > button[data-testid="baseButton-secondary"] {
        background: #FFFFFF !important;
        background-color: #FFFFFF !important;
        color: #2563EB !important;
        border: 1.5px solid #DBEAFE !important;
        border-radius: 9999px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 0.55rem 1.4rem !important;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.03) !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button:not([kind="primary"]):not([type="primary"]):hover {
        background: #EFF6FF !important;
        background-color: #EFF6FF !important;
        border-color: #2563EB !important;
        color: #1D4ED8 !important;
    }

    .stButton > button:not([kind="primary"]):not([type="primary"]) p,
    .stButton > button:not([kind="primary"]):not([type="primary"]) span {
        color: #2563EB !important;
        font-weight: 600 !important;
    }

    /* =========================================================================
       7. NATIVE BORDERED CONTAINERS & EXPANDERS
       ========================================================================= */
    [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        border: 1px solid #DBE4F0 !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.03) !important;
        color: #0F172A !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"] p,
    [data-testid="stVerticalBlockBorderWrapper"] span,
    [data-testid="stVerticalBlockBorderWrapper"] div {
        color: #1E293B !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"] h1,
    [data-testid="stVerticalBlockBorderWrapper"] h2,
    [data-testid="stVerticalBlockBorderWrapper"] h3,
    [data-testid="stVerticalBlockBorderWrapper"] h4 {
        color: #0F172A !important;
        font-weight: 800 !important;
    }

    /* Expanders: Crisp White Cards */
    [data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 16px !important;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03) !important;
        overflow: hidden !important;
        margin-bottom: 0.75rem !important;
    }

    [data-testid="stExpander"] summary {
        font-weight: 700 !important;
        color: #0F172A !important;
        padding: 0.85rem 1.25rem !important;
    }

    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] summary span {
        color: #0F172A !important;
        font-weight: 700 !important;
    }

    /* =========================================================================
       8. METRICS CONTRAST (HIGH READABILITY)
       ========================================================================= */
    [data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 14px !important;
        padding: 0.85rem 1rem !important;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.02) !important;
    }

    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] > div {
        color: #0F172A !important;
        font-weight: 800 !important;
        font-size: 1.6rem !important;
    }

    [data-testid="stMetricLabel"],
    [data-testid="stMetricLabel"] > div,
    [data-testid="stMetricLabel"] p {
        color: #64748B !important;
        font-weight: 700 !important;
        font-size: 0.78rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }

    /* =========================================================================
       9. DROPDOWNS & SELECTBOXES
       ========================================================================= */
    div[data-baseweb="select"],
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        border: 1.5px solid #DBE4F0 !important;
        border-radius: 10px !important;
        color: #0F172A !important;
    }

    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div {
        color: #0F172A !important;
    }

    div[data-baseweb="select"] svg {
        fill: #64748B !important;
    }

    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div,
    ul[data-testid="stSelectboxVirtualDropdown"] {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        box-shadow: 0 10px 25px rgba(15, 23, 42, 0.1) !important;
    }

    li[role="option"] {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        color: #0F172A !important;
        font-weight: 500 !important;
        padding: 0.6rem 1rem !important;
    }

    li[role="option"]:hover,
    li[role="option"][aria-selected="true"] {
        background-color: #EFF6FF !important;
        background: #EFF6FF !important;
        color: #2563EB !important;
        font-weight: 700 !important;
    }

    /* =========================================================================
       10. SKILL CHIPS / BADGES
       ========================================================================= */
    code, .stMarkdown code {
        background-color: #EFF6FF !important;
        color: #1D4ED8 !important;
        border: 1px solid #BFDBFE !important;
        border-radius: 9999px !important;
        padding: 0.22rem 0.68rem !important;
        font-size: 0.84rem !important;
        font-weight: 600 !important;
        display: inline-block !important;
        margin: 2px !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* Tabs: Modern Pill Navigation */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #F1F5F9 !important;
        border-radius: 9999px !important;
        padding: 4px !important;
        border: 1px solid #E2E8F0 !important;
        gap: 4px !important;
        display: inline-flex !important;
        width: auto !important;
        max-width: 100% !important;
        overflow-x: auto !important;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        border-radius: 9999px !important;
        border: none !important;
        color: #64748B !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        padding: 7px 18px !important;
        transition: all 0.2s ease !important;
    }

    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #2563EB !important;
        font-weight: 700 !important;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08) !important;
    }

    /* Headings Hierarchy */
    h1, .nr-hero-title {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        color: #0F172A !important;
        letter-spacing: -0.01em !important;
        word-spacing: normal !important;
        line-height: 1.25 !important;
    }

    h2 {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 1.55rem !important;
        font-weight: 800 !important;
        color: #0F172A !important;
        letter-spacing: -0.02em !important;
    }

    h3 {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 1.22rem !important;
        font-weight: 700 !important;
        color: #0F172A !important;
        letter-spacing: -0.01em !important;
    }

    h4 {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        color: #1E293B !important;
    }

    p, span, label {
        color: #475569 !important;
    }

    /* Hero Badges & Subtitle */
    .nr-hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #EFF6FF;
        color: #2563EB;
        border: 1px solid #BFDBFE;
        padding: 0.35rem 0.85rem;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.75rem;
    }

    /* Streamlit captions & subtitles */
    [data-testid="stCaptionContainer"] p,
    .stCaption {
        color: #64748B !important;
        font-weight: 500 !important;
    }

    /* Paragraphs and general text readability */
    .stMarkdown p, .stMarkdown span, .stMarkdown li {
        color: #1E293B !important;
        font-size: 0.95rem !important;
        line-height: 1.6 !important;
    }
    .stMarkdown strong, .stMarkdown b {
        color: #0F172A !important;
        font-weight: 700 !important;
    }

    /* Preformatted Code Blocks */
    pre {
        background-color: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        color: #0F172A !important;
    }
    pre code {
        background-color: transparent !important;
        border: none !important;
        color: #0F172A !important;
        border-radius: 0 !important;
        padding: 0 !important;
    }
    /* =========================================================================
       11. FUNCTIONAL SIDEBAR IN-PAGE NAVIGATION (HIGH CONTRAST, SAAS LIGHT)
       ========================================================================= */
    .rec-sidebar-nav {
        display: flex;
        flex-direction: column;
        gap: 6px;
        margin-bottom: 1.25rem;
    }

    .rec-nav-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 0.65rem 0.95rem;
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        color: #334155 !important;
        text-decoration: none !important;
        font-size: 0.88rem;
        font-weight: 600;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        position: relative;
        user-select: none;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.02);
    }

    .rec-nav-item:hover {
        background-color: #F8FAFC;
        border-color: #CBD5E1;
        color: #0F172A !important;
        transform: translateX(2px);
    }

    .rec-nav-item.active {
        background: linear-gradient(135deg, rgba(49, 94, 251, 0.08) 0%, rgba(81, 70, 229, 0.06) 100%) !important;
        border-color: #315EFB !important;
        color: #1D4ED8 !important;
        font-weight: 700 !important;
        box-shadow: 0 2px 8px rgba(49, 94, 251, 0.08) !important;
    }

    .rec-nav-item.active::before {
        content: "";
        position: absolute;
        left: -1px;
        top: 6px;
        bottom: 6px;
        width: 3.5px;
        background: linear-gradient(180deg, #315EFB 0%, #5146E5 100%);
        border-radius: 0 4px 4px 0;
    }

    .rec-nav-icon {
        font-size: 1.15rem;
        flex-shrink: 0;
        line-height: 1;
    }

    .rec-nav-text {
        flex-grow: 1;
        white-space: nowrap;
        overflow: visible;
        font-size: 0.88rem;
    }

    .rec-nav-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: #315EFB;
        opacity: 0;
        transition: opacity 0.2s ease;
    }

    .rec-nav-item.active .rec-nav-dot {
        opacity: 1;
    }

    .rec-nav-badge {
        font-size: 0.68rem;
        padding: 0.15rem 0.45rem;
        border-radius: 9999px;
        background: #ECFDF5;
        color: #065F46;
        border: 1px solid #A7F3D0;
        font-weight: 700;
        letter-spacing: 0.02em;
    }

    /* Target Section Anchors & Header Offset */
    html {
        scroll-behavior: smooth !important;
    }

    .nav-section-anchor,
    [id="candidate-portal"],
    [id="job-recommendations"],
    [id="jd-matching"],
    [id="skill-gap-analysis"],
    [id="all-modules"] {
        scroll-margin-top: 95px !important;
        position: relative;
        display: block;
    }

    /* Hidden component iframes */
    iframe[title="streamlit.components.v1.html"],
    iframe[data-testid="stIFrame"],
    .stIFrame {
        position: absolute !important;
        height: 0px !important;
        width: 0px !important;
        opacity: 0 !important;
        pointer-events: none !important;
        border: none !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* =========================================================================
       12. APP SHELL LAYOUT ENGINE (TWO-COLUMN, ZERO OVERLAP)
       ========================================================================= */
    /* Outer AppShell flex container */
    [data-testid="stAppViewContainer"],
    .stAppViewContainer {
        display: flex !important;
        flex-direction: row !important;
        width: 100vw !important;
        max-width: 100vw !important;
        min-height: 100vh !important;
        overflow-x: hidden !important;
        position: relative !important;
        box-sizing: border-box !important;
    }

    /* Column 1: Sidebar stays in normal flex flow, perfectly sticky & separate */
    [data-testid="stSidebar"],
    section[data-testid="stSidebar"],
    .stSidebar {
        position: relative !important;
        height: 100vh !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        flex: 0 0 auto !important;
        box-sizing: border-box !important;
        z-index: 50 !important;
    }

    /* Column 2: Main Content occupies 100% of remaining width AFTER the sidebar */
    [data-testid="stMain"],
    section[data-testid="stMain"],
    section.main,
    .stMain {
        flex: 1 1 0% !important;
        min-width: 0 !important;
        height: 100vh !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        box-sizing: border-box !important;
        display: flex !important;
        flex-direction: column !important;
        position: relative !important;
    }

    /* Page Content inside Main Column */
    .block-container,
    [data-testid="stMainBlockContainer"],
    .stMainBlockContainer {
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
        padding-left: 2.25rem !important;
        padding-right: 2.25rem !important;
        padding-top: 3.5rem !important; /* Moves top breadcrumb bar comfortably down below header */
        padding-bottom: 6rem !important;
        box-sizing: border-box !important;
        flex: 1 0 auto !important;
    }

    /* Action Buttons Row */
    [data-testid="stHorizontalBlock"]:has([data-testid="stBaseButton-primary"]) {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 12px !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }

    [data-testid="stHorizontalBlock"]:has([data-testid="stBaseButton-primary"]) > [data-testid="column"]:first-child {
        flex: 3 1 280px !important;
        min-width: 220px !important;
    }

    [data-testid="stHorizontalBlock"]:has([data-testid="stBaseButton-primary"]) > [data-testid="column"]:last-child {
        flex: 1 1 160px !important;
        min-width: 130px !important;
    }

    /* Prevent any label truncation or horizontal overflow */
    [data-testid="stFileUploader"] label,
    [data-testid="stFileUploader"] label p,
    [data-testid="stWidgetLabel"] p {
        white-space: normal !important;
        word-break: break-word !important;
        overflow-wrap: break-word !important;
        max-width: 100% !important;
    }

    /* Responsive adjustments for mobile and tablet */
    @media (max-width: 768px) {
        .block-container,
        [data-testid="stMainBlockContainer"] {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-top: 2.75rem !important;
        }

        [data-testid="stHorizontalBlock"]:has([data-testid="stBaseButton-primary"]) > [data-testid="column"] {
            flex: 1 1 100% !important;
            width: 100% !important;
        }
    }
</style>
""", unsafe_allow_html=True)


SAMPLE_RESUMES_DIR = os.path.join(os.path.dirname(__file__), "data", "sample_resumes")


@st.cache_resource
def get_job_recommender():
    return JobRoleRecommender()


@st.cache_resource
def get_resume_classifier():
    return ResumeClassifier()


def get_job_matcher():
    return ResumeJobMatcher()


def get_candidate_ranker():
    return CandidateRanker()


def get_interview_predictor():
    return InterviewPerformancePredictor()


def get_candidate_success_predictor():
    return CandidateSuccessPredictor()


def get_salary_predictor():
    return SalaryRangePredictor()


def render_jd_match_result(active_match):
    """Render Job Description match result card and scoring breakdown."""
    st.markdown("### 📋 Job Description Match Result")
    
    # Display Match Card
    cand_display_name = active_match.candidate_name
    score_color = "#86EFAC" if active_match.overall_match_pct >= 75 else ("#FCD34D" if active_match.overall_match_pct > 0 else "#F87171")
    
    cand_status_label = getattr(active_match, "match_status_label", None)
    if not cand_status_label:
        if active_match.overall_match_pct >= 75 and getattr(active_match, "experience_status", "") != "Below Requirement":
            cand_status_label = "Strong Match"
        elif active_match.overall_match_pct > 0:
            cand_status_label = "Partial Match"
        else:
            cand_status_label = "Poor Match"

    with st.container(border=True):
        jd_hdr1, jd_hdr2 = st.columns([3, 1])
        with jd_hdr1:
            st.caption("TARGET ROLE EVALUATION")
            st.subheader(active_match.job_title)
            st.markdown(f"Candidate: **{cand_display_name}**")
            st.markdown(f"Overall Fit: **{active_match.match_status_label}** ({active_match.overall_match_pct}%)")
        with jd_hdr2:
            st.metric(
                "OVERALL CANDIDATE MATCH",
                f"{active_match.overall_match_pct}%",
                active_match.match_status_label,
                help="Overall Match combines multiple matching factors (Skills: 70%, Experience: 20%, Education: 10%). Individual category scores may be 100% even when the overall composite score is lower."
            )

        st.caption("ℹ️ **Overall Match** combines multiple matching factors. Individual category scores may be 100% even when the overall score is lower.")
        st.markdown("---")
        c_skl_m, c_exp_m = st.columns(2)
        with c_skl_m:
            st.markdown("#### Skill Match")
            if active_match.skill_match_pct == 100.0 and not active_match.missing_skills:
                st.caption("✓ All required skills matched.")
            elif active_match.matched_skills:
                st.caption(f"✓ {len(active_match.matched_skills)} of {len(active_match.matched_skills) + len(active_match.missing_skills)} required skills matched.")
            else:
                st.caption("No direct skills matched (0%).")

            if active_match.matched_skills:
                st.markdown(" ".join([f"`{ms}`" for ms in active_match.matched_skills]))

            if active_match.missing_skills:
                st.markdown("<br>**Skills to Improve:**", unsafe_allow_html=True)
                st.markdown(" ".join([f"`{mis}`" for mis in active_match.missing_skills]))

        with c_exp_m:
            st.markdown("#### Experience Match")
            exp_req_label = "Met" if active_match.experience_status == "Meets Requirement" else ("Not Met" if active_match.experience_status == "Below Requirement" else active_match.experience_status)
            st.markdown(f"• **Required:** `{active_match.required_experience_display}`")
            st.markdown(f"• **Candidate:** `{active_match.candidate_experience_display}`")
            st.markdown(f"• **Experience Requirement:** `{exp_req_label}`")
            if active_match.experience_status == "Below Requirement":
                st.warning(f"⚠ Experience requirement not met ({active_match.candidate_experience_display} vs {active_match.required_experience_display})")
            elif active_match.experience_status == "Meets Requirement":
                st.success("✓ Experience Requirement: Met")

    # Transparent Score Audit Expander
    with st.expander("🔍 View Transparent Score Calculation & Audit", expanded=False):
        bd = getattr(active_match, "score_breakdown", {}) or {}
        is_zero = getattr(active_match, "is_zero_skill", False) or active_match.overall_match_pct == 0
        hard_rule_note = "> **Hard Zero-Skill Rule Active:** Candidate has 0 matched technical skills. Overall Match is locked strictly to 0.0%." if is_zero else ""
        formula_latex = r"$$\text{Overall Match} = \frac{(\text{Skill Match} \times W_{\text{skill}}) + (\text{Experience Match} \times W_{\text{exp}}) + (\text{Education Match} \times W_{\text{edu}})}{W_{\text{active total}}}$$"
        edu_source = getattr(active_match, 'education_summary', '') or ('Not specified in JD (0% weight)' if not bd.get('requires_education') else 'Required in JD')
        st.markdown(
            f"""
            **Deterministic Mathematical Formula:**
            {formula_latex}
            
            {hard_rule_note}
            
            | Evaluation Component | Component Score | Active Weight | Weighted Points Earned | Requirement Source |
            | :--- | :--- | :--- | :--- | :--- |
            | **Skill Match** | `{bd.get('skill_match_pct', active_match.skill_match_pct)}%` | `{round(bd.get('skill_weight', 0.7)*100, 1)}%` | **{bd.get('weighted_skill_pts', 0.0)}%** | {len(active_match.matched_skills)} of {len(active_match.matched_skills) + len(active_match.missing_skills)} JD skills matched |
            | **Experience Match** | `{bd.get('experience_match_pct', active_match.experience_match_pct)}%` | `{round(bd.get('experience_weight', 0.2)*100, 1)}%` | **{bd.get('weighted_exp_pts', 0.0)}%** | Required: {active_match.required_experience_display} \| Candidate: {active_match.candidate_experience_display} |
            | **Education Match** | `{bd.get('education_match_pct', active_match.education_match_pct)}%` | `{round(bd.get('education_weight', 0.0)*100, 1)}%` | **{bd.get('weighted_edu_pts', 0.0)}%** | {edu_source} |
            | **Final Overall Score** | — | — | **{bd.get('final_score', active_match.overall_match_pct)}%** | Mathematically Verified (No hidden points) |
            """
        )

    st.markdown("<br>", unsafe_allow_html=True)
    col_why, col_how = st.columns([1, 1])
    with col_why:
        why_hdr = getattr(active_match, "why_matches_header", "")
        is_zero_cand = getattr(active_match, "is_zero_skill", False) or active_match.overall_match_pct == 0 or len(active_match.matched_skills) == 0
        if "Does Not Match" in why_hdr or is_zero_cand:
            st.markdown("#### ✗ Why This Candidate Does Not Match")
        else:
            st.markdown("#### 💡 Why This Candidate Matches")
        st.markdown(active_match.why_matches)

    with col_how:
        st.markdown("#### 🚀 Primary Required Skills & Gaps")
        is_zero_skills = getattr(active_match, "is_zero_skill", False) or active_match.overall_match_pct == 0 or len(active_match.matched_skills) == 0
        sat_msg = getattr(active_match, "skills_satisfaction_msg", "")
        if not sat_msg:
            if is_zero_skills:
                sat_msg = "✗ No required skills matched."
            elif active_match.missing_skills:
                sat_msg = f"⚠ {len(active_match.matched_skills)} of {len(active_match.matched_skills) + len(active_match.missing_skills)} required skills matched."
            else:
                sat_msg = "✓ Candidate satisfies all primary required technical skills."

        if is_zero_skills:
            st.error(sat_msg)
        elif active_match.missing_skills:
            st.warning(sat_msg)
        else:
            st.success(sat_msg)

        if active_match.how_to_improve:
            st.markdown("**Actionable Suggestions for JD Gaps:**")
            for gap in active_match.how_to_improve:
                st.markdown(f"• **`{gap['skill']}`**: {gap['how']}")


def render_candidate_ranking(ranked_list, cand_display_name):
    """Render Candidate Ranking leaderboard."""
    st.markdown("---")
    st.markdown("### 🏆 Candidate Ranking")
    st.caption("Multiple candidate profiles ranked against this Job Description using multi-signal scoring (Skills, Experience, Education, Projects).")

    for cr in ranked_list:
        is_active_cand = (cr.candidate_name.lower() == cand_display_name.lower())
        cand_badge = " (Current Analyzed Profile)" if is_active_cand else ""
        cr_label = getattr(cr, "match_status_label", "Match")

        with st.container(border=True):
            rk_col1, rk_col2 = st.columns([3, 1])
            with rk_col1:
                st.markdown(f"#### Rank #{cr.rank}: **{cr.candidate_name}**{cand_badge}")
                st.caption(cr.ranking_reason)
            with rk_col2:
                st.metric(
                    "OVERALL CANDIDATE MATCH",
                    f"{cr.overall_match_pct}%",
                    cr_label,
                    help="Overall Match combines multiple matching factors (Skills, Experience, Education, Projects). Individual category scores may be 100% even when the overall score is lower."
                )

            with st.expander(f"View Detailed Match Breakdown — {cr.candidate_name}", expanded=False):
                st.caption("ℹ️ **Overall Match** combines multiple matching factors. Individual category scores may be 100% even when the overall score is lower.")
                r_c1, r_c2 = st.columns(2)
                with r_c1:
                    st.markdown("#### Skill Match")
                    if cr.skill_match_pct == 100.0 and not cr.missing_skills:
                        st.caption("✓ All required skills matched.")
                    elif cr.matched_skills:
                        st.caption(f"✓ {len(cr.matched_skills)} of {len(cr.matched_skills) + len(cr.missing_skills)} required skills matched.")
                    else:
                        st.caption("No direct skills matched (0%).")
                    if cr.matched_skills:
                        st.markdown(" ".join([f"`{s}`" for s in cr.matched_skills]))
                    if cr.missing_skills:
                        st.markdown("<br>**Missing Skills from JD:**", unsafe_allow_html=True)
                        st.markdown(" ".join([f"`{s}`" for s in cr.missing_skills]))
                with r_c2:
                    st.markdown("#### Experience Match")
                    cr_exp_req_label = "Met" if cr.experience_status == "Meets Requirement" else ("Not Met" if cr.experience_status == "Below Requirement" else cr.experience_status)
                    st.markdown(f"• **Required:** `{cr.required_experience_display}`")
                    st.markdown(f"• **Candidate:** `{cr.candidate_experience_display}`")
                    st.markdown(f"• **Experience Requirement:** `{cr_exp_req_label}`")
                    if cr.experience_status == "Meets Requirement":
                        st.success("✓ Experience Requirement: Met")
                    elif cr.experience_status == "Below Requirement":
                        st.warning(f"⚠ Experience requirement not met ({cr.candidate_experience_display} vs {cr.required_experience_display})")

                if cr.how_to_improve:
                    st.markdown("<br>**Actionable Improvement Suggestions:**", unsafe_allow_html=True)
                    for imp in cr.how_to_improve[:3]:
                        st.markdown(f"• **`{imp['skill']}`**: {imp['how']}")


def render_advanced_ai_insights(profile, active_match, recs=None):
    """Render Advanced AI Insights (Interview Performance, Candidate Success & Grounded Salary)."""
    st.markdown("<hr style='border: none; border-top: 1px solid #E2E8F0; margin: 2rem 0;'>", unsafe_allow_html=True)
    st.markdown('<div id="advanced-insights" class="nav-section-anchor"></div>', unsafe_allow_html=True)

    adv_header_col1, adv_header_col2 = st.columns([3, 1])
    with adv_header_col1:
        st.markdown("## 🚀 Advanced AI Insights")
        st.caption("Deep predictive intelligence powered by validated Machine Learning models trained on real candidate screening records.")
    with adv_header_col2:
        st.markdown(
            """
            <div style="text-align: right; padding-top: 0.5rem;">
                <span style="background: #EEF2FF; color: #4338CA; border: 1px solid #C7D2FE; padding: 4px 12px; border-radius: 9999px; font-size: 0.75rem; font-weight: 700;">
                    ✓ 3 TRAINED MODELS ACTIVE
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Determine default target role from extracted JD title, fallback to recommendations or candidate title
    default_role = active_match.job_title if (active_match and getattr(active_match, "job_title", None)) else "Software Engineer"
    role_options = ["Software Engineer", "Data Scientist", "AI Researcher", "Cybersecurity Analyst", "Frontend Developer", "Backend Developer"]
    if default_role not in role_options:
        role_options.insert(0, default_role)
    if recs:
        rec_titles = [r.role_title for r in recs]
        for rt in rec_titles:
            if rt not in role_options:
                role_options.append(rt)

    col_target_role, _ = st.columns([2, 2])
    with col_target_role:
        selected_insight_role = st.selectbox(
            "🎯 Evaluate Against Target Role:",
            options=role_options,
            index=0 if default_role not in role_options else role_options.index(default_role),
            help="Select the target role for interview readiness, hiring probability, and grounded market salary prediction."
        )

    # 3 Advanced AI Insight Tabs
    tab_interview, tab_success, tab_salary = st.tabs([
        "🎤 Interview Performance",
        "🏆 Candidate Success Prediction",
        "💰 Salary Prediction (LPA)",
    ])

    # -------------------------------------------------------------
    # TAB 1: INTERVIEW PERFORMANCE PREDICTION
    # -------------------------------------------------------------
    with tab_interview:
        st.markdown("### 🎤 Estimated Interview Performance & Readiness")
        st.caption("Machine learning assessment of interview preparedness calibrated against technical screening benchmarks.")

        interview_pred = get_interview_predictor()

        # Interactive assessment signals container
        with st.expander("🧪 Interactive Assessment Signals & Simulation (Optional)", expanded=False):
            st.caption("Inject live test results or simulated scores to evaluate candidate readiness under assessment conditions.")
            sim_c1, sim_c2, sim_c3 = st.columns(3)
            with sim_c1:
                use_assessments = st.checkbox("Enable Live Assessment Signals", value=False, help="Blend direct test results with ML resume profile features.")
                prep_level = st.selectbox("Preparation Level", ["Medium", "High", "Low"], index=0)
            with sim_c2:
                tech_score = st.slider("Technical Test Score (%)", 0, 100, 75, disabled=not use_assessments)
                coding_score = st.slider("Coding Challenge Score (%)", 0, 100, 80, disabled=not use_assessments)
            with sim_c3:
                comm_score = st.slider("Communication Score (%)", 0, 100, 70, disabled=not use_assessments)
                prob_score = st.slider("Problem-Solving Score (%)", 0, 100, 75, disabled=not use_assessments)

        t_val = float(tech_score) if use_assessments else None
        c_val = float(coding_score) if use_assessments else None
        cm_val = float(comm_score) if use_assessments else None
        p_val = float(prob_score) if use_assessments else None
        prep_val = prep_level if use_assessments else None

        int_res = interview_pred.predict(
            profile,
            target_role=selected_insight_role,
            technical_score=t_val,
            coding_score=c_val,
            communication_score=cm_val,
            problem_solving_score=p_val,
            preparation_level=prep_val,
        )

        if int_res.get("status") == "unavailable":
            st.warning("⚠️ Prediction model requires additional validated training data.")
        elif int_res.get("status") == "error":
            st.error(f"⚠️ {int_res.get('message')}")
        else:
            readiness_pct = int_res["overall_readiness_pct"]
            r_badge = int_res["readiness_badge"]
            r_label = int_res["readiness_label"]
            r_color = int_res["readiness_color"]

            with st.container(border=True):
                r_c1, r_c2 = st.columns([3, 1])
                with r_c1:
                    st.markdown(f"#### Overall Interview Readiness: <span style='color: {r_color}; font-weight: 800;'>{readiness_pct}%</span>", unsafe_allow_html=True)
                    st.markdown(f"Status: **{r_label}** · Evaluated for: **{selected_insight_role}**")
                    st.caption(f"💡 {int_res['explanation']}")
                with r_c2:
                    st.metric(
                        "READINESS SCORE",
                        f"{readiness_pct}%",
                        r_badge,
                        help="Composite readiness score derived from ML model features and assessment signals."
                    )

                st.markdown("---")
                st.markdown("##### 📊 Sub-Dimension Readiness Breakdown")
                sub_c1, sub_c2, sub_c3 = st.columns(3)
                with sub_c1:
                    tech_r = int_res["sub_scores"]["technical_readiness"]
                    st.markdown(f"**Technical Readiness: `{tech_r}%`**")
                    st.progress(min(1.0, tech_r / 100.0))
                with sub_c2:
                    comm_r = int_res["sub_scores"]["communication_readiness"]
                    st.markdown(f"**Communication Readiness: `{comm_r}%`**")
                    st.progress(min(1.0, comm_r / 100.0))
                with sub_c3:
                    prob_r = int_res["sub_scores"]["problem_solving_readiness"]
                    st.markdown(f"**Problem-Solving Readiness: `{prob_r}%`**")
                    st.progress(min(1.0, prob_r / 100.0))

            # Actionable Weaknesses / Improvement Areas
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 🎯 Identified Actionable Weaknesses & Improvement Areas")
            for imp in int_res["improvement_areas"]:
                with st.container(border=True):
                    st.markdown(f"**📌 {imp['area']}**")
                    st.markdown(f"• {imp['detail']}")

            # Model Transparency Box
            with st.expander("🔍 Model Transparency & Scientific Validation", expanded=False):
                m_metrics = int_res.get("metrics", {})
                st.markdown(
                    f"""
                    | Attribute | Specification |
                    | :--- | :--- |
                    | **Model Type** | `{m_metrics.get('model_type', 'GradientBoostingRegressor')}` |
                    | **Mean Absolute Error (MAE)** | `{m_metrics.get('mae')} points` |
                    | **Root Mean Squared Error (RMSE)** | `{m_metrics.get('rmse')} points` |
                    | **Goodness-of-Fit (R² Score)** | `{m_metrics.get('r2')}` |
                    | **Training Dataset** | `1,000 real candidate screening records (AI_Resume_Screening.csv)` |
                    | **Ethical Guardrail** | Demographic and protected personal attributes are completely omitted. |
                    """
                )

    # -------------------------------------------------------------
    # TAB 2: CANDIDATE SUCCESS PREDICTION
    # -------------------------------------------------------------
    with tab_success:
        st.markdown("### 🏆 Candidate Success & Role Fit Prediction")
        st.caption("Calibrated probabilistic model estimating candidate suitability and multi-pillar role alignment.")

        success_pred = get_candidate_success_predictor()

        # Check if JD matching is active to provide JD alignment signal
        jd_match_signal = float(active_match.overall_match_pct) if (active_match and hasattr(active_match, "overall_match_pct")) else None
        matched_skills_signal = active_match.matched_skills if (active_match and hasattr(active_match, "matched_skills")) else None

        succ_res = success_pred.predict(
            profile,
            target_role=selected_insight_role,
            jd_match_pct=jd_match_signal,
            matched_skills=matched_skills_signal,
        )

        if succ_res.get("status") == "unavailable":
            st.warning("⚠️ Prediction model requires additional validated training data.")
        elif succ_res.get("status") == "error":
            st.error(f"⚠️ {succ_res.get('message')}")
        else:
            succ_score = succ_res["candidate_success_score"]
            hire_p = succ_res["hire_probability"]
            rec_badge = succ_res["recommendation"]
            rec_desc = succ_res["recommendation_desc"]
            b_color = succ_res["badge_color"]

            with st.container(border=True):
                sc_c1, sc_c2 = st.columns([3, 1])
                with sc_c1:
                    st.markdown(f"#### Estimated Role Fit Score: <span style='color: {b_color}; font-weight: 800;'>{succ_score}%</span>", unsafe_allow_html=True)
                    st.markdown(f"Recommendation: **{rec_badge}** (Hire Probability: **{hire_p}%**)")
                    st.caption(rec_desc)
                with sc_c2:
                    st.metric(
                        "SUCCESS FIT",
                        f"{succ_score}%",
                        rec_badge,
                        help="Calibrated composite fit combining 5 structural evaluation pillars."
                    )

                st.markdown("---")
                st.markdown("##### 🏛️ 5-Pillar Alignment Breakdown")
                pills = succ_res["five_pillars"]
                pil_cols = st.columns(5)
                pil_data = [
                    ("1. Skill Alignment", pills["skill_alignment"]),
                    ("2. Experience Alignment", pills["experience_alignment"]),
                    ("3. Education Alignment", pills["education_alignment"]),
                    ("4. Project Relevance", pills["project_relevance"]),
                    ("5. JD Alignment", pills["jd_alignment"]),
                ]
                for p_col, (p_name, p_val) in zip(pil_cols, pil_data):
                    with p_col:
                        st.markdown(f"**{p_name}**")
                        st.markdown(f"`{p_val}%`")
                        st.progress(min(1.0, p_val / 100.0))

            # Strengths & Risk Areas
            st.markdown("<br>", unsafe_allow_html=True)
            col_str, col_risk = st.columns(2)
            with col_str:
                st.markdown("#### 🌟 Key Candidate Strengths")
                for st_item in succ_res["key_strengths"]:
                    st.success(f"✓ {st_item}")
            with col_risk:
                st.markdown("#### ⚠️ Potential Risk Factors & Gaps")
                for rk_item in succ_res["improvement_areas"]:
                    st.warning(f"• {rk_item}")

            # Ethical guardrail disclaimer
            st.markdown(
                f"""
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; margin-top: 12px; font-size: 0.82rem; color: #475569;">
                    🛡️ <b>Ethical AI Compliance:</b> {succ_res['ethical_guardrail']}
                </div>
                """,
                unsafe_allow_html=True
            )

            # Model Transparency Box
            with st.expander("🔍 Model Transparency & Scientific Validation", expanded=False):
                s_metrics = succ_res.get("metrics", {})
                st.markdown(
                    f"""
                    | Evaluation Metric | Value | Metric Description |
                    | :--- | :--- | :--- |
                    | **Model Architecture** | `{s_metrics.get('model_type')}` | Calibrated Classifier Ensemble + Regressor |
                    | **Classification Accuracy** | `{round(s_metrics.get('accuracy', 0)*100, 2)}%` | Verified test accuracy on candidate hiring outcomes |
                    | **F1 Score** | `{s_metrics.get('f1')}` | Balanced harmonic mean of precision and recall |
                    | **Precision** | `{s_metrics.get('precision')}` | High confidence against false-positive hiring predictions |
                    | **Recall** | `{s_metrics.get('recall')}` | Broad coverage capturing viable qualified talent |
                    | **ROC-AUC Score** | `{s_metrics.get('roc_auc')}` | Discriminative ability across decision thresholds |
                    | **Score MAE** | `{s_metrics.get('score_mae')} pts` | Continuous suitability score average error |
                    | **Training Dataset** | `1,000 real candidate screening records (AI_Resume_Screening.csv)` | Verified multi-factor screening dataset |
                    """
                )

    # -------------------------------------------------------------
    # TAB 3: SALARY PREDICTION (LPA)
    # -------------------------------------------------------------
    with tab_salary:
        st.markdown("### 💰 Realistic Market Salary Range Prediction (LPA)")
        st.caption("Quantile Machine Learning regressor estimating conservative, expected, and top-tier compensation in Lakhs Per Annum.")

        salary_pred = get_salary_predictor()
        sal_res = salary_pred.predict(profile, target_role=selected_insight_role)

        if sal_res.get("status") == "unavailable":
            st.warning("⚠️ Prediction model requires additional validated training data.")
        elif sal_res.get("status") == "error":
            st.error(f"⚠️ {sal_res.get('message')}")
        else:
            with st.container(border=True):
                sal_c1, sal_c2 = st.columns([3, 1])
                with sal_c1:
                    st.markdown(f"#### Estimated Compensation: <span style='color: #059669; font-weight: 800;'>{sal_res['salary_range_display']}</span>", unsafe_allow_html=True)
                    st.markdown(f"Target Role: **{sal_res['target_role']}** · Location Benchmark: **{sal_res['location']}**")
                    st.caption("Ground-truth compensation calibrated against Indian tech ecosystem entry and mid-tier bands.")
                with sal_c2:
                    st.metric(
                        "EXPECTED MEDIAN",
                        sal_res["expected_display"],
                        "Market Expected",
                        help="Median statistical expected offer based on candidate qualifications."
                    )

                st.markdown("---")
                st.markdown("##### 💵 Three-Tier Compensation Estimates")
                b_c1, b_c2, b_c3 = st.columns(3)
                with b_c1:
                    st.markdown("**🥉 Lower Estimate (15th %ile)**")
                    st.markdown(f"### ₹{sal_res['lower_lpa']} LPA")
                    st.caption("Conservative base / entry offer")
                with b_c2:
                    st.markdown("**🥈 Expected Median (50th %ile)**")
                    st.markdown(f"### <span style='color: #059669;'>₹{sal_res['expected_lpa']} LPA</span>", unsafe_allow_html=True)
                    st.caption("Market standard for this profile")
                with b_c3:
                    st.markdown("**🥇 Upper Estimate (85th %ile)**")
                    st.markdown(f"### ₹{sal_res['upper_lpa']} LPA")
                    st.caption("Top-tier / strong negotiation tier")

            # Contributing Factors Breakdown
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 📈 Key Factors Driving This Salary Estimate")
            for fac in sal_res["contributing_factors"]:
                with st.container(border=True):
                    st.markdown(f"**• {fac['factor']}**: {fac['impact']}")

            # Disclaimer
            st.info("ℹ️ **Compensation Notice:** Salary predictions reflect real-world Indian tech hiring benchmarks for decision guidance. Actual compensation varies based on company tier, individual negotiation, equity components, and interview performance.")

            # Model Transparency Box
            with st.expander("🔍 Model Transparency & Scientific Validation", expanded=False):
                sal_m = sal_res.get("metrics", {})
                st.markdown(
                    f"""
                    | Metric | Value | Details |
                    | :--- | :--- | :--- |
                    | **Model Architecture** | `{sal_m.get('model_type')}` | Gradient Boosting Quantile Estimators (α=0.15, 0.50, 0.85) |
                    | **Mean Absolute Error (MAE)** | `{sal_m.get('mae_lpa')} LPA` | Average error in Lakhs Per Annum |
                    | **Root Mean Squared Error (RMSE)** | `{sal_m.get('rmse_lpa')} LPA` | Standard deviation of residual errors |
                    | **Goodness-of-Fit (R² Score)** | `{sal_m.get('r2')}` | High variance explanation across candidate experience bands |
                    | **Dataset & Currency** | `{sal_m.get('dataset')}` | Standardized in Indian Rupees ({sal_m.get('currency')}) |
                    """
                )



def get_available_samples():
    """Retrieve list of preloaded sample resumes."""
    if os.path.exists(SAMPLE_RESUMES_DIR):
        files = [f for f in sorted(os.listdir(SAMPLE_RESUMES_DIR)) if f.endswith((".pdf", ".docx", ".txt", ".json"))]
        return files
    return []


def get_all_unique_skills(skills) -> list:
    """Collect all unique skills across all categories without double-counting."""
    if not skills:
        return []
    if hasattr(skills, "all_unique_skills"):
        return skills.all_unique_skills
    all_raw = []
    for cat in [
        getattr(skills, "programming_languages", []),
        getattr(skills, "databases", []),
        getattr(skills, "frameworks", []),
        getattr(skills, "libraries", []),
        getattr(skills, "ui_ux_tools", []),
        getattr(skills, "office_productivity", []),
        getattr(skills, "tools", []),
        getattr(skills, "cloud", []),
        getattr(skills, "platforms", []),
        getattr(skills, "frontend", []),
        getattr(skills, "backend", []),
        getattr(skills, "apis", []),
        getattr(skills, "technical", []),
        getattr(skills, "other_technical_skills", []),
        getattr(skills, "soft_skills", []),
        getattr(skills, "business_skills", []),
        getattr(skills, "other", []),
    ]:
        if cat:
            for item in cat:
                if item and str(item).strip():
                    all_raw.append(str(item).strip())
    
    seen = set()
    unique = []
    for sk in all_raw:
        k = sk.lower()
        if k not in seen:
            seen.add(k)
            unique.append(sk)
    return unique


# Initialize pipeline in session state
if "pipeline" not in st.session_state:
    st.session_state.pipeline = ResumeExtractionPipeline()


# Sidebar Configuration
with st.sidebar:
    # Clean Brand Header (Section 4)
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 12px; padding: 0.25rem 0 1rem 0; border-bottom: 1px solid #E2E8F0; margin-bottom: 1.25rem;">
            <div style="width: 44px; height: 44px; border-radius: 12px; background: linear-gradient(135deg, #2563EB 0%, #4F46E5 100%); display: flex; align-items: center; justify-content: center; color: white; font-size: 1.3rem; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25); flex-shrink: 0;">
                💼
            </div>
            <div>
                <div style="font-size: 1.18rem; font-weight: 800; color: #0F172A; letter-spacing: -0.02em; line-height: 1.15;">AI Recruitment</div>
                <div style="font-size: 0.75rem; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;">Career Intelligence</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<div style='font-size: 0.75rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;'>Navigation</div>", unsafe_allow_html=True)
    
    # Requirement 13: Central navigation configuration
    NAVIGATION_ITEMS = [
        {"label": "Candidate Portal", "target": "candidate-portal", "icon": "👤", "desc": "Resume upload & candidate profile"},
        {"label": "Job Recommendations", "target": "job-recommendations", "icon": "🎯", "desc": "AI matched roles"},
        {"label": "JD Matching", "target": "jd-matching", "icon": "📋", "desc": "Target role evaluation & ranking"},
        {"label": "Skill Gap Analysis", "target": "skill-gap-analysis", "icon": "🔬", "desc": "Missing competencies & gap diagnostics"},
        {"label": "Advanced AI Insights", "target": "advanced-insights", "icon": "🚀", "desc": "Interview, Success & Salary Prediction"},
        {"label": "All Modules (Overview)", "target": "all-modules", "icon": "📊", "desc": "Platform summary"},
    ]

    nav_links_html = []
    for idx, item in enumerate(NAVIGATION_ITEMS):
        active_cls = " active" if idx == 0 else ""

        nav_links_html.append(
            f'<a href="#{item["target"]}" class="rec-nav-item{active_cls}" '
            f'data-target="{item["target"]}" data-available="true" '
            f'title="{html.escape(item["desc"])}">'
            f'<span class="rec-nav-icon">{item["icon"]}</span>'
            f'<span class="rec-nav-text">{html.escape(item["label"])}</span>'
            f'<span class="rec-nav-dot"></span></a>'
        )

    sidebar_nav_html = f'<nav class="rec-sidebar-nav" id="rec-sidebar-nav">{"".join(nav_links_html)}</nav>'
    st.markdown(sidebar_nav_html, unsafe_allow_html=True)
    
    nav_scroll_js = """
<script>
(function() {
    var win = (window.parent && window.parent.document) ? window.parent : window;
    var doc = win.document;

    // 1. Single Source of Truth for Active Section
    if (!win._recActiveSection) {
        try {
            var hashVal = win.location.hash ? win.location.hash.replace('#', '') : null;
            win._recActiveSection = hashVal || sessionStorage.getItem('rec_active_nav') || 'candidate-portal';
        } catch (e) {
            win._recActiveSection = 'candidate-portal';
        }
    }

    // 2. Central Active State Applier
    function applyActiveSection(targetId) {
        if (!targetId) return;
        win._recActiveSection = targetId;
        try { sessionStorage.setItem('rec_active_nav', targetId); } catch (e) {}

        var links = doc.querySelectorAll('.rec-nav-item');
        if (links && links.length > 0) {
            links.forEach(function(link) {
                if (link.getAttribute('data-target') === targetId) {
                    link.classList.add('active');
                } else {
                    link.classList.remove('active');
                }
            });
        }

        // Synchronize breadcrumb
        var bcrumb = doc.getElementById('rec-current-breadcrumb');
        if (bcrumb) {
            var activeLink = doc.querySelector('.rec-nav-item.active .rec-nav-text');
            if (activeLink) {
                bcrumb.innerText = activeLink.innerText.trim();
            }
        }
    }
    win._recApplyActiveSection = applyActiveSection;

    // 3. Global Delegated Click Handler (capture phase on document)
    if (!win._recNavDelegated) {
        win._recNavDelegated = true;

        doc.addEventListener('click', function(e) {
            var link = e.target.closest ? e.target.closest('.rec-nav-item') : null;
            if (!link) return;

            e.preventDefault();
            e.stopPropagation();

            var targetId = link.getAttribute('data-target');
            if (!targetId) return;

            // Immediately switch active state (strictly this button active, all others inactive)
            applyActiveSection(targetId);

            // Lock scroll spy during smooth scroll animation
            win._recIsClickScrolling = true;
            clearTimeout(win._recClickScrollTimeout);
            win._recClickScrollTimeout = setTimeout(function() {
                win._recIsClickScrolling = false;
            }, 900);

            // Scroll to target element
            var targetEl = doc.getElementById(targetId);
            var mainEl = doc.querySelector('section[data-testid="stMain"]') || doc.querySelector('.stMain');
            if (mainEl && targetEl) {
                var mainRect = mainEl.getBoundingClientRect();
                var targetRect = targetEl.getBoundingClientRect();
                var offset = targetRect.top - mainRect.top + mainEl.scrollTop - 75;
                mainEl.scrollTo({ top: Math.max(0, offset), behavior: 'smooth' });
            } else if (targetEl) {
                targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }

            // Auto-expand skill gap if applicable
            if (targetId === 'skill-gap-analysis') {
                var expanders = doc.querySelectorAll('[data-testid="stExpander"] details');
                if (expanders && expanders.length > 0) {
                    expanders[0].open = true;
                }
            }

            try {
                win.history.replaceState(null, null, '#' + targetId);
            } catch (err) {}
        }, true);
    }

    // 4. Scroll Spy (attaches to Streamlit's actual scroll container stMain AND window)
    function checkScrollPosition() {
        if (win._recIsClickScrolling) return;

        var sectionIds = ['all-modules', 'candidate-portal', 'job-recommendations', 'skill-gap-analysis', 'jd-matching', 'advanced-insights'];
        var activeFound = null;

        for (var i = 0; i < sectionIds.length; i++) {
            var sid = sectionIds[i];
            var el = doc.getElementById(sid);
            if (!el) continue;

            var rect = el.getBoundingClientRect();
            if (rect.top <= 260) {
                activeFound = sid;
            }
        }

        if (activeFound && activeFound !== win._recActiveSection) {
            applyActiveSection(activeFound);
            try {
                win.history.replaceState(null, null, '#' + activeFound);
            } catch (err) {}
        }
    }

    if (!win._recScrollSpyInstalled) {
        win._recScrollSpyInstalled = true;

        var ticking = false;
        function onScroll() {
            if (!ticking) {
                requestAnimationFrame(function() {
                    checkScrollPosition();
                    ticking = false;
                });
                ticking = true;
            }
        }

        win.addEventListener('scroll', onScroll, { passive: true });

        function attachToMain() {
            var mainEl = doc.querySelector('section[data-testid="stMain"]') || doc.querySelector('.stMain');
            if (mainEl && !mainEl._recScrollBound) {
                mainEl._recScrollBound = true;
                mainEl.addEventListener('scroll', onScroll, { passive: true });
            }
        }
        attachToMain();
        setInterval(attachToMain, 1000);
    }

    // 5. DOM Reconciliation Guard: Run multiple times to overcome any Streamlit re-render diffing
    applyActiveSection(win._recActiveSection);
    setTimeout(function() { applyActiveSection(win._recActiveSection); }, 50);
    setTimeout(function() { applyActiveSection(win._recActiveSection); }, 200);
    setTimeout(function() { applyActiveSection(win._recActiveSection); }, 500);

    // Initial URL hash navigation on fresh page load
    if (win.location.hash) {
        var hashId = win.location.hash.replace('#', '');
        var targetEl = doc.getElementById(hashId);
        if (targetEl) {
            setTimeout(function() {
                targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
                applyActiveSection(hashId);
            }, 300);
        }
    }

    // 6. Platform Brand Hardening: Aggressively eliminate Streamlit Cloud host overlays
    function cleanBranding() {
        var docs = [doc];
        try {
            if (window.document && window.document !== doc) {
                docs.push(window.document);
            }
        } catch (e) {}

        docs.forEach(function(d) {
            if (!d) return;

            // Remove Toolbar / Fork / GitHub buttons
            var toolbars = d.querySelectorAll('[data-testid="stToolbar"], #MainMenu, .stAppDeployButton, [data-testid="stDecoration"]');
            toolbars.forEach(function(el) {
                el.style.setProperty('display', 'none', 'important');
                el.style.setProperty('visibility', 'hidden', 'important');
            });

            // Remove any header elements with "Fork" or GitHub references
            var headerItems = d.querySelectorAll('header a, header button, div[class*="toolbar"] a, div[class*="toolbar"] button');
            headerItems.forEach(function(el) {
                if (el.getAttribute('data-testid') === 'stSidebarCollapseButton' || el.getAttribute('data-testid') === 'collapsedControl') {
                    return;
                }
                var txt = (el.innerText || '').toLowerCase().trim();
                var href = (el.getAttribute('href') || '').toLowerCase();
                var title = (el.getAttribute('title') || '').toLowerCase();
                if (txt === 'fork' || txt.includes('fork') || href.includes('github.com') || title.includes('github') || title.includes('fork')) {
                    el.style.setProperty('display', 'none', 'important');
                    el.style.setProperty('visibility', 'hidden', 'important');
                }
            });

            // Remove "Hosted with Streamlit" ribbon and avatar badge at bottom right
            var bottomBadges = d.querySelectorAll('footer, [data-testid="stFooter"], [class*="viewerBadge"], [class*="floatingBadge"], [class*="ProfileBadge"], a[href*="streamlit.io"]');
            bottomBadges.forEach(function(el) {
                var container = el.closest ? (el.closest('div[style*="fixed"]') || el.closest('div[style*="z-index"]') || el.parentElement) : el.parentElement;
                if (container && container !== d.body) {
                    container.style.setProperty('display', 'none', 'important');
                    container.style.setProperty('visibility', 'hidden', 'important');
                }
                el.style.setProperty('display', 'none', 'important');
                el.style.setProperty('visibility', 'hidden', 'important');
            });

            // Deep text-content inspection for floating Streamlit Cloud ribbons
            var allElements = d.querySelectorAll('div, a, span');
            allElements.forEach(function(el) {
                var t = (el.innerText || '').trim();
                if (t === 'Hosted with Streamlit' || t.includes('Hosted with Streamlit') || t === 'Fork') {
                    var c = el.closest ? (el.closest('div[style*="fixed"]') || el.closest('div[style*="bottom"]') || el) : el;
                    if (c && c !== d.body && c !== d.documentElement) {
                        c.style.setProperty('display', 'none', 'important');
                    }
                }
            });
        });
    }

    cleanBranding();
    setInterval(cleanBranding, 400);
})();
</script>
"""
    st.html(nav_scroll_js, unsafe_allow_javascript=True)
    components.html(nav_scroll_js, height=0)

    st.markdown("<div style='margin-top: 1.25rem; border-top: 1px solid #E2E8F0; padding-top: 1rem;'></div>", unsafe_allow_html=True)
    
    # Pre-Loaded Test Resumes Section
    st.markdown("<div style='font-size: 0.75rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;'>📁 Pre-Loaded Test Resumes</div>", unsafe_allow_html=True)
    
    sample_files = get_available_samples()
    selected_sample = st.selectbox(
        "Choose sample resume:",
        options=["-- None (Upload Custom) --"] + sample_files,
        index=0,
        label_visibility="collapsed",
    )

    demo_mode = False




# Clean Top Header Bar (Section 5)
active_cand_name = None
active_cand_info = ""
if "current_profile" in st.session_state and st.session_state.current_profile is not None:
    cp = st.session_state.current_profile
    active_cand_name = getattr(cp.personal_info, "name", None) or "Candidate"
    exp_disp = getattr(cp.experience, "employment_status", "")
    if cp.experience.internships:
        exp_disp = cp.experience.internships[0].duration_display
    elif cp.experience.total_display:
        exp_disp = cp.experience.total_display
    active_cand_info = f"✓ Ready: {active_cand_name} ({exp_disp})"

cand_pill_html = (
    f'<div class="nr-status-badge verified"><span>✓</span> <span>{html.escape(active_cand_info)}</span></div>'
    if active_cand_name else
    '<div class="nr-status-badge ready"><span>⚡</span> <span>Ready for Resume Upload</span></div>'
)

nav_label_clean = "Candidate Portal"
header_bar_html = (
    '<div id="all-modules" class="nav-section-anchor"></div>'
    '<div class="nr-top-bar">'
    f'<div class="nr-breadcrumb">AI Recruitment / <b id="rec-current-breadcrumb">{html.escape(nav_label_clean)}</b></div>'
    f'{cand_pill_html}'
    '</div>'
)
st.markdown(header_bar_html, unsafe_allow_html=True)

# Hero Title Block (NextRaise style)
st.markdown(
    """
    <div style="margin-bottom: 1.5rem;">
        <div class="nr-hero-badge">⚡ AI-Powered • Resumes Scored 35,000+ • Live Job Matching</div>
        <h1 class="nr-hero-title">AI JOB MATCHING &amp; CAREER INTELLIGENCE</h1>
        <p class="nr-hero-subtitle">Deterministic resume intelligence, skill gap diagnostics, and algorithmic matching powered by structured profiling.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# File Upload Section
st.markdown('<div id="candidate-portal" class="nav-section-anchor"></div>', unsafe_allow_html=True)
st.markdown("### 📤 Upload Candidate Resume")


uploaded_file = st.file_uploader(
    "Choose a resume file (Supported formats: PDF, DOCX, TXT, JSON):",
    type=["pdf", "docx", "txt", "json"],
    help="Upload candidate resume in PDF, DOCX, TXT, or JSON format.",
)

file_to_process = None
file_name_to_process = ""

if uploaded_file is not None:
    file_to_process = uploaded_file
    file_name_to_process = uploaded_file.name
elif selected_sample != "-- None (Upload Custom) --":
    sample_path = os.path.join(SAMPLE_RESUMES_DIR, selected_sample)
    if os.path.exists(sample_path):
        file_to_process = sample_path
        file_name_to_process = selected_sample

def reset_jd_and_insights_session_state():
    """Resets all JD extraction, ranking, and downstream Advanced AI Insights states."""
    st.session_state.jd_analysis_submitted = False
    st.session_state.analyzed_jd_text = None
    st.session_state.jd_extraction_status = "idle"
    st.session_state.jd_ranking_status = "idle"
    st.session_state.current_jd_id = None
    st.session_state.extraction_jd_id = None
    st.session_state.ranking_jd_id = None
    st.session_state.extracted_jd_data = None
    st.session_state.active_jd_match = None
    st.session_state.ranked_candidates_list = None
    st.session_state.jd_extraction_error = None
    st.session_state.jd_ranking_error = None


# Session state initialization
if "last_analyzed_file" not in st.session_state:
    st.session_state.last_analyzed_file = None
if "current_profile" not in st.session_state:
    st.session_state.current_profile = None

for k, default_val in [
    ("jd_extraction_status", "idle"),
    ("jd_ranking_status", "idle"),
    ("current_jd_id", None),
    ("extraction_jd_id", None),
    ("ranking_jd_id", None),
    ("extracted_jd_data", None),
    ("active_jd_match", None),
    ("ranked_candidates_list", None),
    ("jd_extraction_error", None),
    ("jd_ranking_error", None),
]:
    if k not in st.session_state:
        st.session_state[k] = default_val

# If user selected/uploaded a different file, reset the previous profile and JD insights
if file_name_to_process != st.session_state.last_analyzed_file:
    st.session_state.current_profile = None
    st.session_state.current_file_name = None
    reset_jd_and_insights_session_state()

has_file = file_to_process is not None
is_analyzed = (
    st.session_state.current_profile is not None
    and st.session_state.last_analyzed_file == file_name_to_process
)

# Status prompt when a file is staged but waiting for user to click Analyze
if has_file and not is_analyzed:
    st.info(f"📄 **{file_name_to_process}** loaded and ready for analysis. Click **'🚀 Analyze Resume'** below to begin.")
elif selected_sample != "-- None (Upload Custom) --" and is_analyzed:
    st.success(f"Selected sample resume: **{selected_sample}**")

# Analyze Action Buttons
col_b1, col_b2 = st.columns([4, 1])
with col_b1:
    analyze_button = st.button(
        "🚀 Analyze Resume",
        type="primary",
        use_container_width=True,
        disabled=not has_file,
        help="Click to start full candidate extraction, profiling, and job matching." if has_file else "Please upload or select a resume file first."
    )
with col_b2:
    reanalyze_button = st.button("🔄 Fresh Re-Scan", use_container_width=True)

# 1. Fresh Re-Scan: Reset state ONLY — NEVER automatically starts analysis
if reanalyze_button:
    st.session_state.current_profile = None
    st.session_state.pipeline = None
    st.session_state.current_file_name = None
    st.session_state.last_analyzed_file = None
    reset_jd_and_insights_session_state()
    try:
        from services.llm.llm_extractor import LLMExtractor
        LLMExtractor.clear_cache()
    except Exception:
        pass
    if has_file:
        st.info(f"🔄 Analysis state reset for **{file_name_to_process}**. Click **'🚀 Analyze Resume'** to start a fresh scan.")
    else:
        st.info("🔄 System reset to ready state.")

# 2. Analyze Resume: The SOLE trigger that starts the processing pipeline
if analyze_button:
    if not has_file:
        st.warning("⚠️ Please upload a resume or select a sample resume from the sidebar first.")
    else:
        with st.spinner(f"Extracting and structuring candidate data from '{file_name_to_process}'..."):
            pipeline = ResumeExtractionPipeline()
            profile = pipeline.process(file_to_process, file_name_to_process)
            st.session_state.pipeline = pipeline
            st.session_state.current_profile = profile
            st.session_state.current_file_name = file_name_to_process
            st.session_state.last_analyzed_file = file_name_to_process
            reset_jd_and_insights_session_state()
            st.rerun()


# Render Extracted Profile if available
if "current_profile" in st.session_state and st.session_state.current_profile is not None:
    profile = st.session_state.current_profile
    meta = profile.metadata

    st.markdown("---")

    # Internal Validation Check (always executes backend integrity validation)
    val_report = ResumeValidator.validate_profile(profile, raw_text=getattr(meta, "raw_text", "") or "")

    # Check for genuine extraction failure vs clean completion
    if meta.status != ParsingStatus.SUCCESS.value:
        st.error(f"⚠️ **Unable to process resume:** {meta.status_message or 'Please try uploading a standard PDF, DOCX, or TXT file.'}")
    else:
        # Professional Product-Facing Status Banner
        st.success("✓ **Resume Analysis Completed** — Candidate profile generated successfully.")

        loss_warnings = getattr(meta, "information_loss_warnings", [])
        if loss_warnings:
            with st.expander(f"⚠️ **{len(loss_warnings)} Information Loss Warning(s) Detected** — click to review", expanded=False):
                for w in loss_warnings:
                    if w.startswith("[ERROR]"):
                        st.error(w)
                    else:
                        st.warning(w)

    unique_skills_list = get_all_unique_skills(profile.skills)
    total_skills = len(unique_skills_list)
    
    edu_counts = get_education_counts(profile.education)
    degree_count = edu_counts["degree_count"]
    school_count = edu_counts["school_count"]
    
    cand_name = profile.personal_info.name or "Candidate Profile"
    prof_title = getattr(profile.personal_info, "professional_title", None) or "Technology Professional"
    status_label = profile.experience.employment_status or "Fresher"
    if profile.experience.internships:
        intern_dur = profile.experience.internships[0].duration_display
        card2_val = f"Internship: {intern_dur}" if intern_dur and intern_dur != "Duration not specified" else "Internship Experience"
    else:
        card2_val = profile.experience.total_display or "0 yrs"

    edu_summary_text = (
        profile.education[0].degree or profile.education[0].institution or "Academic Degree"
        if profile.education else "Education Record"
    )

    # Section 7: Compact Candidate Overview Card (Native Streamlit Components)
    top_skills_slice = unique_skills_list[:14]
    with st.container(border=True):
        ov_col1, ov_col2 = st.columns([3, 1])
        with ov_col1:
            st.caption("CANDIDATE PROFILE · VERIFIED")
            st.subheader(cand_name)
            st.markdown(f"🎓 **{edu_summary_text}** · 💼 **{card2_val}** · 📍 **{getattr(profile.personal_info, 'location', '') or 'India'}**")
        with ov_col2:
            st.metric("IDENTIFIED SKILLS", total_skills)

        st.markdown("**Extracted Candidate Skills:**")
        st.markdown(" ".join([f"`{s}`" for s in top_skills_slice]))
        if len(unique_skills_list) > 14:
            st.caption(f"+{len(unique_skills_list)-14} more skills extracted from profile")

    # 4 High-Level Metric Cards (Native Streamlit)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Candidate Name", cand_name)
    with col2:
        st.metric("Experience", card2_val, status_label)
    with col3:
        st.metric("Identified Skills", total_skills)
    with col4:
        edu_card_val = f"{degree_count} Degree | {school_count} Rec"
        st.metric("Education", edu_card_val)

    st.markdown("<br>", unsafe_allow_html=True)

    # Clean Tab Navigation (Separate Demo Tabs from Developer Tabs)
    if demo_mode:
        tab_personal, tab_skills, tab_exp, tab_edu, tab_proj_certs, tab_meta_json = st.tabs([
            "👤 Candidate Profile & Summary",
            "🛠️ Categorized Skills",
            "💼 Work & Internships",
            "🎓 Education",
            "📂 Projects & Credentials",
            "📄 Structured Data & Export",
        ])
        tab_dev_debug = None
    else:
        tab_personal, tab_skills, tab_exp, tab_edu, tab_proj_certs, tab_meta_json, tab_dev_debug = st.tabs([
            "👤 Candidate Profile & Summary",
            "🛠️ Categorized Skills",
            "💼 Work & Internships",
            "🎓 Education",
            "📂 Projects & Credentials",
            "📄 Structured Data & Export",
            "🔬 Developer & Diagnostics",
        ])

    # Tab 1: Personal Info & Complete Professional Summary
    with tab_personal:
        st.subheader("Candidate Identity & Contact Information")
        p = profile.personal_info
        
        c1, c2 = st.columns(2)
        with c1:
            name = getattr(p, "name", None)
            prof_title = getattr(p, "professional_title", None)
            email = getattr(p, "email", None)
            phone = getattr(p, "phone", None)
            loc = getattr(p, "location", None)
            emp_status = getattr(profile.experience, "employment_status", None)

            if name:
                st.markdown(f"**Full Name:** {name}")
            if prof_title:
                st.markdown(f"**Professional Title:** `{prof_title}`")
            if email:
                st.markdown(f"**Email Address:** {email}")
            if phone:
                st.markdown(f"**Phone Number:** {phone}")
            if loc:
                st.markdown(f"**Location:** {loc}")
            if emp_status:
                st.markdown(f"**Employment Status:** `{emp_status}`")
        with c2:
            for plat_title, plat_key in [
                ("LinkedIn", "linkedin"),
                ("GitHub", "github"),
                ("LeetCode", "leetcode"),
                ("Kaggle", "kaggle"),
                ("Portfolio", "portfolio"),
                ("Personal Website", "personal_website"),
            ]:
                if plat_key == "personal_website" and getattr(p, "personal_website", None) == getattr(p, "portfolio", None):
                    continue
                rendered = render_profile_entry(plat_title, plat_key, p)
                if rendered:
                    st.markdown(rendered, unsafe_allow_html=True)
            
        # Complete Professional Summary (Zero truncation / character limits)
        if profile.summary:
            st.markdown("---")
            st.markdown("### 🎯 Professional Summary")
            st.markdown(
                f'<div class="summary-box">{html.escape(profile.summary)}</div>',
                unsafe_allow_html=True
            )

        clean_langs = list(dict.fromkeys([str(l).strip() for l in (profile.languages or []) if str(l).strip()]))
        if clean_langs:
            st.markdown("---")
            st.markdown(f"#### 🌐 Spoken Languages ({len(clean_langs)})")
            st.markdown(", ".join(clean_langs))

        all_interests = list(dict.fromkeys([str(i).strip() for i in (profile.interests or []) + (profile.hobbies or []) if str(i).strip()]))
        if all_interests:
            st.markdown("---")
            st.markdown(f"#### 🎯 Interests & Hobbies ({len(all_interests)})")
            st.markdown(", ".join(all_interests))

        strengths_list = getattr(profile, "strengths", []) or []
        clean_strengths = list(dict.fromkeys([str(s).strip() for s in strengths_list if str(s).strip()]))
        if clean_strengths:
            st.markdown("---")
            st.markdown(f"#### 💡 Core Strengths ({len(clean_strengths)})")
            st.markdown(", ".join(clean_strengths))

        if profile.additional_qualifications:
            st.markdown("---")
            st.markdown(f"#### 🌟 Additional Qualifications ({len(profile.additional_qualifications)})")
            for aq in profile.additional_qualifications:
                st.markdown(f"• {aq}")

        if profile.declaration:
            st.markdown("---")
            st.markdown("#### ✍️ Declaration")
            decl_txt = profile.declaration.get("text", "")
            decl_place = profile.declaration.get("place")
            decl_date = profile.declaration.get("date")
            decl_sig = profile.declaration.get("signature")
            if decl_txt:
                st.caption(f'"{decl_txt}"')
            col_d1, col_d2, col_d3 = st.columns(3)
            with col_d1:
                if decl_place:
                    st.markdown(f"📍 **Place:** {decl_place}")
            with col_d2:
                if decl_date:
                    st.markdown(f"📅 **Date:** {decl_date}")
            with col_d3:
                if decl_sig:
                    st.markdown(f"✍️ **Signature:** `{decl_sig}`")

    # Tab 2: Categorized Skills
    with tab_skills:
        st.subheader("Extracted & Categorized Skills")
        s = profile.skills
        
        skill_groups = [
            ("Programming Languages", s.programming_languages),
            ("Frameworks", s.frameworks),
            ("Libraries", s.libraries),
            ("Databases", s.databases),
            ("UI / UX Design Tools", getattr(s, "ui_ux_tools", [])),
            ("Office / Productivity Tools", getattr(s, "office_productivity", [])),
            ("Development Tools", getattr(s, "tools", [])),
            ("Cloud Technologies", getattr(s, "cloud", [])),
            ("Platforms & Operating Systems", getattr(s, "platforms", [])),
            ("Frontend Technologies", s.frontend),
            ("Backend Technologies", s.backend),
            ("APIs & Protocols", s.apis),
            ("Business & Management Skills", getattr(s, "business_skills", [])),
            ("Technical Disciplines", getattr(s, "technical_disciplines", []) or getattr(s, "other_technical_skills", []) or s.technical),
            ("Soft Skills", s.soft_skills),
            ("Other Skills", s.other),
        ]
        
        has_any_skills = False
        for group_name, raw_skills_list in skill_groups:
            skills_list = list(dict.fromkeys([str(sk).strip() for sk in (raw_skills_list or []) if str(sk).strip()]))
            if skills_list:
                has_any_skills = True
                st.markdown(f"##### {group_name} ({len(skills_list)})")
                st.markdown(", ".join(skills_list))
                st.markdown("<br>", unsafe_allow_html=True)

        if not has_any_skills:
            st.info("ℹ️ No categorized skills identified in the candidate profile.")

    # Tab 3: Experience & Internships
    with tab_exp:
        st.subheader("Work & Internship Experience")
        e = profile.experience
        
        col_st1, col_st2, col_st3 = st.columns(3)
        with col_st1:
            st.markdown(f"**Employment Status:** `{e.employment_status or 'Fresher'}`")
        with col_st2:
            full_time_disp = f"{e.total_years} yrs" if e.full_time and e.total_years is not None else "0 yrs"
            st.markdown(f"**Full-Time Experience:** `{full_time_disp}`")
        with col_st3:
            if e.internships:
                intern_disp = e.internships[0].duration_display
                st.markdown(f"**Internship Experience:** `{intern_disp}`")
            else:
                st.markdown("**Internship Experience:** `None`")
            
        if e.companies:
            st.markdown(f"**Associated Organizations:** {', '.join(e.companies)}")
            
        st.markdown("---")
        
        # Internships
        if e.internships:
            st.markdown("#### 🎯 Internship Experience")
            for idx, intern in enumerate(e.internships, 1):
                role_label = intern.role or intern.title or "Intern"
                dur_disp = intern.duration_display
                dur_suffix = f" ({dur_disp})" if dur_disp and dur_disp != "Duration not specified" else ""
                with st.expander(f"📌 {role_label} @ {intern.company or 'Company'}{dur_suffix}", expanded=True):
                    col_i1, col_i2 = st.columns(2)
                    with col_i1:
                        if intern.location:
                            st.markdown(f"📍 **Location:** {intern.location}")
                        if dur_disp and dur_disp != "Duration not specified":
                            st.markdown(f"⏱️ **Duration:** {dur_disp}")
                    with col_i2:
                        if intern.start_date or intern.end_date:
                            dur_label = f" (Duration: {dur_disp})" if dur_disp and dur_disp != "Duration not specified" else ""
                            st.markdown(f"📅 **Timeline:** {intern.start_date or 'N/A'} – {intern.end_date or 'N/A'}{dur_label}")
                    if intern.description:
                        st.markdown(f"**Description:** {intern.description}")
                    if intern.responsibilities:
                        st.markdown("**Key Responsibilities & Highlights:**")
                        for r in intern.responsibilities:
                            st.markdown(f"- {r}")
                    if intern.technologies:
                        st.markdown("**Technologies:** " + ", ".join([f"`{t}`" for t in intern.technologies]))
                    if getattr(intern, "details", None):
                        st.markdown("**Details:**")
                        for d in intern.details:
                            st.markdown(f"- {d}")
            st.markdown("<br>", unsafe_allow_html=True)

        # Full-time Experience
        if e.full_time:
            st.markdown("#### 💼 Full-Time Professional Experience")
            for idx, exp in enumerate(e.full_time, 1):
                with st.expander(f"📌 {exp.title or 'Role'} @ {exp.company or 'Company'} {f'({exp.duration})' if exp.duration else ''}", expanded=True):
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        if exp.location:
                            st.markdown(f"📍 **Location:** {exp.location}")
                        if exp.duration:
                            st.markdown(f"⏱️ **Duration:** {exp.duration}")
                    with col_f2:
                        if exp.start_date or exp.end_date:
                            st.markdown(f"📅 **Timeline:** {exp.start_date or 'N/A'} – {exp.end_date or 'N/A'}")
                    if getattr(exp, "description", None):
                        st.markdown(f"**Description:** {exp.description}")
                    if exp.responsibilities:
                        st.markdown("**Key Responsibilities:**")
                        for r in exp.responsibilities:
                            st.markdown(f"- {r}")
                    if exp.technologies:
                        st.markdown("**Technologies:** " + ", ".join([f"`{t}`" for t in exp.technologies]))
                    if getattr(exp, "details", None):
                        st.markdown("**Details:**")
                        for d in exp.details:
                            st.markdown(f"- {d}")

        # General / Additional Work Experience
        rendered_keys = {(getattr(x, 'title', None) or getattr(x, 'role', None), getattr(x, 'company', None)) for x in list(e.internships or []) + list(e.full_time or [])}
        other_exp = [
            d for d in (e.details or []) 
            if d not in (e.full_time or []) 
            and getattr(d, 'experience_type', '') != 'internship'
            and (getattr(d, 'title', None) or getattr(d, 'role', None), getattr(d, 'company', None)) not in rendered_keys
        ]
        if other_exp:
            st.markdown("#### 💼 Additional Work Experience")
            for idx, exp in enumerate(other_exp, 1):
                exp_title = getattr(exp, 'title', None) or getattr(exp, 'role', 'Role')
                exp_comp = getattr(exp, 'company', None) or 'Organization'
                exp_dur = getattr(exp, 'duration', None)
                with st.expander(f"📌 {exp_title} @ {exp_comp} {f'({exp_dur})' if exp_dur else ''}", expanded=True):
                    if getattr(exp, 'start_date', None) or getattr(exp, 'end_date', None):
                        st.caption(f"📅 Timeline: {getattr(exp, 'start_date', 'N/A')} – {getattr(exp, 'end_date', 'N/A')}")
                    if getattr(exp, 'responsibilities', None):
                        st.markdown("**Key Responsibilities:**")
                        for r in exp.responsibilities:
                            st.markdown(f"- {r}")
                    if getattr(exp, 'technologies', None):
                        st.markdown("**Technologies:** " + ", ".join([f"`{t}`" for t in exp.technologies]))

        if not e.internships and not e.full_time and not other_exp:
            st.info("ℹ️ No formal employment entries detected. Academic and personal projects are listed under Projects.")

    # Tab 4: Education
    with tab_edu:
        st.subheader("Educational Qualifications & Academic Hierarchy")
        if profile.education:
            for idx, edu in enumerate(profile.education, 1):
                vm = normalize_education_record(edu)
                icon = "🎓" if vm["is_degree"] else "🏫"
                with st.expander(f"{icon} {vm['title']}", expanded=True):
                    col_e1, col_e2 = st.columns([3, 1])
                    with col_e1:
                        st.markdown(f"#### {icon} {vm['qualification'] or 'Qualification'}")
                        st.markdown(f"🏛️ **Institution / School:** {vm['institution'] or '_Not specified_'}")
                        if vm.get("university"):
                            st.markdown(f"🏛️ **Affiliated University:** {vm['university']}")
                        if getattr(edu, "field_of_study", None) and getattr(edu, "field_of_study", "") not in (vm["qualification"] or ""):
                            st.markdown(f"🔬 **Field of Study:** {edu.field_of_study}")
                        if getattr(edu, "specialization", None) and getattr(edu, "specialization", "") != getattr(edu, "field_of_study", ""):
                            st.markdown(f"🔬 **Specialization / Stream:** {edu.specialization}")
                        elif getattr(edu, "stream", None):
                            st.markdown(f"🔬 **Stream:** {edu.stream}")
                        if vm.get("location"):
                            st.markdown(f"📍 **Location:** {vm['location']}")
                        
                        qual_label = (vm.get("category") or ("Degree" if vm["is_degree"] else "School")).replace("_", " ").title()
                        derived_type = vm.get("type") or ("College/University" if vm["is_degree"] else "School")
                        st.caption(f"Category: **{qual_label}** | Type: **{derived_type}**")
                    with col_e2:
                        if vm.get("status"):
                            status_cls = "status-badge-student" if "Pursuing" in str(vm["status"]) else "status-badge-completed"
                            st.markdown(f"<span class='{status_cls}'>{vm['status']}</span>", unsafe_allow_html=True)
                        else:
                            st.markdown("<span style='background: #F1F5F9; color: #64748B; padding: 0.2rem 0.6rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 600;'>Not specified</span>", unsafe_allow_html=True)
                        if vm.get("start_year") and (vm.get("expected_year") or vm.get("end_year")):
                            end_disp = vm.get("expected_year") or vm.get("end_year")
                            year_label = "Timeline (Expected)" if "Pursuing" in str(vm.get("status") or "") else "Timeline"
                            st.markdown(f"🗓️ **{year_label}:** {vm['start_year']} – {end_disp}")
                        elif vm.get("expected_year") or vm.get("end_year"):
                            y = vm.get("expected_year") or vm.get("end_year")
                            year_label = "Expected Year" if "Pursuing" in str(vm.get("status") or "") else "Year"
                            st.markdown(f"🗓️ **{year_label}:** {y}")
                        if vm.get("score"):
                            st_label = f"⭐ **{vm.get('score_type') or 'Academic Score'}:**"
                            st.markdown(f"{st_label} `{vm['score']}`")
                    
                    if vm.get("details"):
                        st.markdown("---")
                        st.markdown("**Academic Achievements & Details:**")
                        all_edu_details = list(dict.fromkeys(vm["details"]))
                        for d in all_edu_details:
                            st.markdown(f"• {d}")

            if not demo_mode:
                st.markdown("<br>", unsafe_allow_html=True)
                with st.expander("🔍 Education Classification & Provenance Trace", expanded=False):
                    val_edu = validate_education_consistency(profile)
                    st.markdown(f"**Total Records:** `{val_edu['total_records']}` | **Degree Count:** `{val_edu['degree_count']}` | **School Count:** `{val_edu['school_count']}` | **Integrity Status:** `{'VALID' if val_edu['valid'] else 'MISMATCH'}`")
                    if val_edu['trace']:
                        trace_df = pd.DataFrame(val_edu['trace'])
                        trace_df.columns = ["#", "Extracted Degree / Level", "Institution", "Canonical Category", "Classification"]
                        st.dataframe(trace_df, use_container_width=True, hide_index=True)
                    if val_edu['issues']:
                        for iss in val_edu['issues']:
                            st.error(iss)
        else:
            st.caption("_No educational qualifications identified._")

    # Tab 5: Projects & Certifications
    with tab_proj_certs:
        st.subheader("Projects & Verified Credentials")
        
        col_p, col_c = st.columns([1, 1])
        with col_p:
            st.markdown(f"#### 🚀 Projects ({len(profile.projects)})")
            if profile.projects:
                for proj in profile.projects:
                    proj_name = proj.name or proj.title or "Project"
                    with st.expander(f"📦 {proj_name} {f'({proj.project_type})' if proj.project_type else ''}", expanded=True):
                        if proj.description:
                            st.markdown(f"<p style='font-size: 0.95rem; line-height: 1.55; margin: 0.25rem 0 0.5rem 0; word-wrap: break-word; white-space: normal;'>{proj.description}</p>", unsafe_allow_html=True)
                        if proj.technologies:
                            st.markdown("**Technologies:** " + ", ".join([f"`{t}`" for t in proj.technologies]))
                        
                        tech_subgroups = []
                        if proj.programming_languages: tech_subgroups.append(f"Languages: {', '.join(proj.programming_languages)}")
                        if proj.frontend: tech_subgroups.append(f"Frontend: {', '.join(proj.frontend)}")
                        if proj.backend: tech_subgroups.append(f"Backend: {', '.join(proj.backend)}")
                        if proj.database: tech_subgroups.append(f"Database: {', '.join(proj.database)}")
                        if proj.tools: tech_subgroups.append(f"Tools: {', '.join(proj.tools)}")
                        if tech_subgroups:
                            st.caption(" | ".join(tech_subgroups))

                        if proj.url:
                            st.markdown(f"🔗 [Project Link]({proj.url})")
                        if getattr(proj, "details", None):
                            for d in proj.details:
                                st.markdown(f"- {d}")
            else:
                st.caption("_No projects found._")
                
        with col_c:
            st.markdown(f"#### 📜 Certifications ({len(profile.certifications)})")
            if profile.certifications:
                for cert in profile.certifications:
                    cert_line = f"• **{cert.name}**"
                    if cert.issuer:
                        cert_line += f" ({cert.issuer})"
                    if cert.date:
                        cert_line += f" – {cert.date}"
                    if cert.credential_id:
                        cert_line += f" (ID: `{cert.credential_id}`)"
                    st.markdown(cert_line)
                    if cert.url:
                        st.markdown(f"  [Verify Credential]({cert.url})")
                    if getattr(cert, "details", None):
                        st.caption(cert.details)
            else:
                st.caption("_No certifications found._")
                
            all_achievements = list(dict.fromkeys([str(a).strip() for a in (profile.achievements or []) + (profile.awards_achievements or []) if str(a).strip()]))
            if all_achievements:
                st.markdown("---")
                st.markdown(f"#### 🏆 Awards & Achievements ({len(all_achievements)})")
                for ach in all_achievements:
                    st.markdown(f"• {ach}")

            valid_pubs = []
            for raw_pub in (getattr(profile, "publications", None) or []):
                norm_p = normalize_publication(raw_pub)
                if norm_p:
                    valid_pubs.append(norm_p)

            if valid_pubs:
                st.markdown("---")
                st.markdown(f"#### 📚 Research Publications & Papers ({len(valid_pubs)})")
                for p_dict in valid_pubs:
                    pub_title = p_dict.get("title") or "Research Publication"
                    pub_authors = p_dict.get("authors") or []
                    pub_url = p_dict.get("url")
                    pub_desc = p_dict.get("description")
                    pub_details = p_dict.get("details") or []
                    
                    st.markdown(f"• **{pub_title}**")
                    if pub_authors:
                        authors_str = ", ".join(pub_authors) if isinstance(pub_authors, list) else str(pub_authors)
                        if authors_str.strip():
                            st.caption(f"Authors: _{authors_str.strip()}_")
                            
                    meta_lines = format_publication_metadata(p_dict)
                    for m_line in meta_lines:
                        st.markdown(f"  🏛️ _{m_line}_")
                        
                    if pub_url:
                        st.markdown(f"  🔗 [Read Publication / Link]({pub_url})")
                        
                    if pub_desc and isinstance(pub_desc, str) and pub_desc.strip():
                        st.markdown(f"  {pub_desc.strip()}")
                    elif pub_desc and isinstance(pub_desc, list):
                        for d in pub_desc:
                            if d and str(d).strip():
                                st.markdown(f"  • {str(d).strip()}")
                                
                    if pub_details and isinstance(pub_details, list):
                        for d in pub_details:
                            cleaned_d = clean_publication_detail(
                                d,
                                conference=p_dict.get("conference"),
                                publisher=p_dict.get("publisher"),
                                journal=p_dict.get("journal"),
                                description=pub_desc,
                            )
                            if cleaned_d:
                                st.markdown(f"  • {cleaned_d}")

            if profile.additional_qualifications:
                st.markdown("---")
                st.markdown(f"#### 🌟 Additional Qualifications ({len(profile.additional_qualifications)})")
                for aq in profile.additional_qualifications:
                    st.markdown(f"• {aq}")

    # Tab 6: Structured Data & Export
    with tab_meta_json:
        st.subheader("📄 Structured Candidate Profile & Intelligence")
        st.caption("Authoritative structured data ready for candidate evaluation and downstream pipeline processing.")
        
        profile_dict = profile.to_dict()
        json_output = json.dumps(profile_dict, indent=2)
        
        st.download_button(
            label="⬇️ Download Structured Candidate JSON",
            data=json_output,
            file_name=f"candidate_profile_{profile.personal_info.name or 'extracted'}.json".replace(" ", "_").lower(),
            mime="application/json",
            type="primary",
            use_container_width=True,
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("👁️ View Structured JSON Payload", expanded=False):
            st.json(profile_dict)
        


    # Tab 7: Developer & Debug Mode (Only visible when Demo Mode is toggled off)
    if not demo_mode and tab_dev_debug is not None:
        with tab_dev_debug:
            st.subheader("🔬 Developer & Debug Mode: Full 9-Stage Pipeline Diagnostics")
            st.caption("End-to-end provenance inspection across all 9 stages: Raw Text ➔ Blocks ➔ Columns ➔ Sections ➔ Deterministic ➔ LLM Pass 1 ➔ LLM Pass 2 ➔ Merged JSON ➔ Mismatches.")
            
            dtab1, dtab2, dtab3, dtab4, dtab5, dtab6, dtab7, dtab8, dtab9 = st.tabs([
                "1️⃣ Raw Text",
                "2️⃣ Layout Blocks",
                "3️⃣ Detected Columns",
                "4️⃣ Detected Sections",
                "5️⃣ Deterministic JSON",
                "6️⃣ LLM Pass 1",
                "7️⃣ LLM Pass 2",
                "8️⃣ Final Merged JSON",
                "9️⃣ Source vs Final Mismatches",
            ])

            with dtab1:
                st.markdown("#### 📜 Stage 1: Raw Document Text")
                st.info(f"**Extraction Method:** `{meta.extraction_method.upper()}` | **File Format:** `{meta.file_type}` | **Total Characters:** `{meta.character_count}`")
                if meta.raw_text:
                    st.code(meta.raw_text, language="text")
                else:
                    st.caption("Raw text not cached in metadata.")

            with dtab2:
                st.markdown("#### 🧱 Stage 2: Canonical Layout Blocks & Bounding Boxes")
                if meta.ocr_blocks:
                    st.markdown(f"**Raw Bounding Blocks ({len(meta.ocr_blocks)} blocks):**")
                    st.json(meta.ocr_blocks[:30])
                elif profile.source_spans:
                    st.markdown("**Structured Source Spans & Blocks:**")
                    st.json(profile.source_spans)
                else:
                    st.caption("No spatial bounding boxes recorded.")

            with dtab3:
                st.markdown("#### 🏛️ Stage 3: Detected Columns & Reading Order Bands")
                st.markdown(f"**Layout Mode:** `{'Multi-Column / Sidebar' if meta.character_count > 100 else 'Single Column'}`")
                if meta.raw_text:
                    preview_lines = [l for l in meta.raw_text.split('\n') if l.strip()][:25]
                    st.dataframe(pd.DataFrame({"Line Number": range(1, len(preview_lines) + 1), "Reconstructed Line": preview_lines}), use_container_width=True)

            with dtab4:
                st.markdown("#### 📑 Stage 4: Detected Section Boundaries & Text Blocks")
                detected_sec_list = []
                if profile.summary: detected_sec_list.append(("Summary / Objective", profile.summary))
                if profile.education: detected_sec_list.append(("Education", f"{len(profile.education)} qualifications extracted"))
                if profile.projects: detected_sec_list.append(("Projects", f"{len(profile.projects)} projects extracted"))
                if profile.skills: detected_sec_list.append(("Skills", f"{total_skills} skills extracted"))
                if profile.experience.internships or profile.experience.full_time: detected_sec_list.append(("Experience / Internships", f"{len(profile.experience.internships)} internships, {len(profile.experience.full_time)} full-time"))
                if profile.certifications: detected_sec_list.append(("Certifications", f"{len(profile.certifications)} certifications extracted"))
                if profile.achievements: detected_sec_list.append(("Achievements", f"{len(profile.achievements)} items"))
                if profile.languages: detected_sec_list.append(("Languages", f"{len(profile.languages)} languages"))
                if profile.interests: detected_sec_list.append(("Interests", f"{len(profile.interests)} items"))
                if profile.declaration: detected_sec_list.append(("Declaration", str(profile.declaration)))
                
                for sec_name, sec_summary in detected_sec_list:
                    with st.expander(f"📌 Section: {sec_name}", expanded=False):
                        st.write(sec_summary)

            with dtab5:
                st.markdown("#### ⚙️ Stage 5: Deterministic Extraction JSON")
                if "diagnostic_trace" in st.session_state and st.session_state.diagnostic_trace.get("stage_deterministic"):
                    st.json(st.session_state.diagnostic_trace["stage_deterministic"])
                else:
                    st.json(profile.to_dict())

            with dtab6:
                st.markdown("#### 🤖 Stage 6: LLM Pass 1 Structured Extraction Output")
                if "diagnostic_trace" in st.session_state and st.session_state.diagnostic_trace.get("stage_llm_pass1"):
                    st.json(st.session_state.diagnostic_trace["stage_llm_pass1"])
                else:
                    st.info("LLM Pass 1 was not invoked or LLM extraction is disabled in configuration.")

            with dtab7:
                st.markdown("#### 🔍 Stage 7: LLM Pass 2 Validation & Refinement Output")
                if "diagnostic_trace" in st.session_state and st.session_state.diagnostic_trace.get("stage_llm_pass2"):
                    st.json(st.session_state.diagnostic_trace["stage_llm_pass2"])
                else:
                    st.info("LLM Pass 2 was not invoked or single-pass mode was used.")

            with dtab8:
                st.markdown("#### 💾 Stage 8: Final Merged Candidate Profile JSON")
                st.json(profile.to_dict())

            with dtab9:
                st.markdown("#### 🛡️ Stage 9: Source vs Final Evidence & Mismatches")
                from services.llm.information_loss import InformationLossDetector
                loss_rep = InformationLossDetector.check(profile, meta.raw_text or "")
                
                val_col1, val_col2 = st.columns(2)
                with val_col1:
                    st.metric(label="Loss Check Status", value="CLEAN" if not loss_rep.has_issues() else "WARNINGS")
                with val_col2:
                    st.metric(label="Issues Detected", value=len(loss_rep.errors) + len(loss_rep.warnings))

                if loss_rep.errors:
                    st.markdown("##### 🔴 High-Severity Information Loss Errors:")
                    for err in loss_rep.errors:
                        st.error(f"**{err.field.upper()}**: {err.message} (Evidence: `{err.source_evidence}`)")
                
                if loss_rep.warnings:
                    st.markdown("##### 🟡 Information Loss & Alignment Warnings:")
                    for warn in loss_rep.warnings:
                        st.warning(f"**{warn.field.upper()}**: {warn.message}")
                
                if not loss_rep.has_issues():
                    st.success("✅ Zero information loss detected: all source document fields are fully preserved in the final JSON.")

    # =========================================================================
    # PART 1: AI JOB ROLE RECOMMENDATIONS (TOP 5 SUITABLE ROLES)
    # =========================================================================
    st.markdown("<hr style='border: none; border-top: 1px solid #E2E8F0; margin: 2rem 0;'>", unsafe_allow_html=True)
    st.markdown('<div id="job-recommendations" class="nav-section-anchor"></div>', unsafe_allow_html=True)
    st.markdown('<div id="skill-gap-analysis" class="nav-section-anchor"></div>', unsafe_allow_html=True)
    st.markdown("## 🎯 AI Job Role Recommendations & Skill Gap Diagnostics")
    st.caption("Top 5 suitable job roles dynamically recommended based primarily on the candidate's actual extracted skills.")

    rec_engine = get_job_recommender()
    recs = rec_engine.recommend(unique_skills_list, candidate_profile=profile, top_k=5)

    if not recs:
        st.info("ℹ️ No matching job roles found for the extracted skills profile.")
    else:
        for r in recs:
            match_pct = r.match_percentage
            if match_pct >= 80:
                tag_text = "Strong Match"
            elif match_pct >= 60:
                tag_text = "Good Match"
            elif match_pct >= 30:
                tag_text = "Partial Match"
            else:
                tag_text = "Low Match"

            with st.container(border=True):
                rec_col1, rec_col2 = st.columns([3, 1])
                with rec_col1:
                    st.subheader(f"{r.icon}  {r.role_title}")
                    st.caption(f"Domain: **{r.category}** · Experience Req: **{r.min_experience_years}+ years** · Salary: **{r.salary_range}**")
                with rec_col2:
                    st.metric("MATCH SCORE", f"{int(match_pct)}%", tag_text)

                st.markdown("---")
                c_mat, c_gap = st.columns(2)
                with c_mat:
                    st.markdown(f"**✓ Matched Skills ({len(r.matched_skills)})**")
                    if r.matched_skills:
                        st.markdown(" ".join([f"`{ms}`" for ms in r.matched_skills[:8]]))
                    else:
                        st.caption("None demonstrated")
                with c_gap:
                    st.markdown(f"**△ Skills to Improve ({len(r.top_skills_to_improve)})**")
                    if r.top_skills_to_improve:
                        st.markdown(" ".join([f"`{imp}`" for imp in r.top_skills_to_improve[:5]]))
                    else:
                        st.caption("No critical gaps identified")

                with st.expander(f"🔍 View Skill Gap Breakdown — {r.role_title}", expanded=False):
                    st.markdown(f"#### 📋 Skill Gap Breakdown: {r.role_title} ({r.match_percentage}% Match)")
                    
                    tab_core, tab_imp, tab_rec, tab_prof, tab_bonus, tab_summary = st.tabs([
                        f"🚨 Missing Core ({len(r.missing_core_skills)})",
                        f"⚡ Important ({len(r.important_skills_to_improve)})",
                        f"⭐ Recommended ({len(r.recommended_skills)})",
                        f"👥 Professional ({len(r.professional_development)})",
                        f"🚀 Bonus / Advanced ({len(r.bonus_advanced_skills)})",
                        "📋 Demonstrated Skills",
                    ])

                    with tab_core:
                        st.markdown("##### 🚨 Critical Technical Core Skills Missing")
                        st.caption("Foundational must-have competencies for this role.")
                        if r.missing_core_skills:
                            for gap in r.missing_core_skills:
                                st.markdown(f"**`{gap['skill']}`**")
                                st.markdown(f"• **Why learn it:** {gap['why']}")
                                st.markdown(f"• **How to improve:** {gap['how']}")
                                st.markdown("<br>", unsafe_allow_html=True)
                        else:
                            st.success("✅ Zero core technical skill gaps! Candidate demonstrates all essential foundations.")

                    with tab_imp:
                        st.markdown("##### ⚡ Important Production Competencies to Improve")
                        st.caption("High-value technical skills expected in modern production environments.")
                        if r.important_skills_to_improve:
                            for gap in r.important_skills_to_improve:
                                st.markdown(f"**`{gap['skill']}`**")
                                st.markdown(f"• **Why learn it:** {gap['why']}")
                                st.markdown(f"• **How to improve:** {gap['how']}")
                                st.markdown("<br>", unsafe_allow_html=True)
                        else:
                            st.success("✅ Candidate demonstrates all secondary technical competencies for this role.")

                    with tab_rec:
                        st.markdown("##### ⭐ Recommended Technical Enhancements")
                        st.caption("Valuable capabilities that elevate candidate competitiveness and engineering depth.")
                        if r.recommended_skills:
                            for gap in r.recommended_skills:
                                st.markdown(f"**`{gap['skill']}`**")
                                st.markdown(f"• **Why learn it:** {gap['why']}")
                                st.markdown(f"• **How to improve:** {gap['how']}")
                                st.markdown("<br>", unsafe_allow_html=True)
                        else:
                            st.info("ℹ️ Candidate satisfies all recommended technical enhancements.")

                    with tab_prof:
                        st.markdown("##### 👥 Professional & Methodological Development")
                        st.caption("Engineering processes, methodologies, and soft skills.")
                        if r.professional_development:
                            for gap in r.professional_development:
                                st.markdown(f"• **`{gap['skill']}`**: {gap['how']}")
                        else:
                            st.success("✅ Professional methodologies and soft skills well-demonstrated.")

                    with tab_bonus:
                        st.markdown("##### 🚀 Bonus & Advanced Technologies (Optional)")
                        st.caption("Emerging tools and advanced specializations that provide competitive advantages.")
                        if r.bonus_advanced_skills:
                            st.markdown(" ".join([f"`{s}`" for s in r.bonus_advanced_skills]))
                        else:
                            st.caption("_None specified._")

                    with tab_summary:
                        st.markdown("##### 📋 Candidate Demonstrated Skills vs Role Requirements")
                        col_ov1, col_ov2 = st.columns(2)
                        with col_ov1:
                            st.markdown(f"**Demonstrated Skills ({len(r.demonstrated_skills)}):**")
                            for ds in r.demonstrated_skills:
                                st.markdown(f"✓ `{ds}`")
                        with col_ov2:
                            st.markdown(f"**Total Required Technical Competencies ({len(r.required_skills)}):**")
                            for rq in r.required_skills:
                                st.markdown(f"• `{rq}`")

    # =========================================================================
    # PART 2: JOB DESCRIPTION MATCHING & CANDIDATE RANKING
    # =========================================================================
    st.markdown("<hr style='border: none; border-top: 1px solid #E2E8F0; margin: 2rem 0;'>", unsafe_allow_html=True)
    st.markdown('<div id="jd-matching" class="nav-section-anchor"></div>', unsafe_allow_html=True)
    st.markdown("## 📊 Job Description Matching & Candidate Ranking")
    st.caption("Compare Job Description requirements directly against candidate profile data from Module 1 and rank multiple candidates.")

    SAMPLE_JDS = {
        "Python Developer (2+ yrs)": (
            "Python Developer required.\n"
            "2+ years experience.\n"
            "Strong Python programming.\n"
            "Django experience.\n"
            "REST API development.\n"
            "SQL knowledge.\n"
            "Git.\n"
            "Good problem-solving skills."
        ),
        "Frontend Developer (React, 1+ yr)": (
            "Frontend Developer required.\n"
            "1+ years experience in building responsive web applications.\n"
            "Strong skills in HTML5, CSS3, JavaScript, and React.\n"
            "REST API integration.\n"
            "Git and browser DevTools.\n"
            "Knowledge of responsive design and web accessibility."
        ),
        "Full Stack Developer (React/Node, 2+ yrs)": (
            "Full Stack Developer opening.\n"
            "2+ years experience across frontend and backend systems.\n"
            "Proficiency with React, Node.js, Express, and REST APIs.\n"
            "Relational database design and SQL (PostgreSQL or MySQL).\n"
            "Git version control and Docker containerization basics."
        ),
        "Data Analyst (SQL/Python/BI, 1+ yr)": (
            "Data Analyst position.\n"
            "1+ years experience in analytical querying and reporting.\n"
            "Strong SQL and Python (Pandas, NumPy).\n"
            "Experience with Power BI or Tableau dashboards.\n"
            "Statistical analysis, data cleaning, and executive reporting."
        ),
        "-- Custom Job Description (Enter below) --": ""
    }

    # Session state initialization for JD matching
    if "last_selected_sample_jd" not in st.session_state:
        st.session_state.last_selected_sample_jd = "-- Custom Job Description (Enter below) --"
    if "jd_text_content" not in st.session_state:
        st.session_state.jd_text_content = ""
    if "jd_analysis_submitted" not in st.session_state:
        st.session_state.jd_analysis_submitted = False
    if "analyzed_jd_text" not in st.session_state:
        st.session_state.analyzed_jd_text = None
    if "jd_input_key" not in st.session_state:
        st.session_state.jd_input_key = 0

    jd_sel_col1, jd_sel_col2 = st.columns([1, 1])
    with jd_sel_col1:
        custom_idx = list(SAMPLE_JDS.keys()).index("-- Custom Job Description (Enter below) --")
        selected_sample_jd = st.selectbox(
            "Select Pre-configured Benchmark Job Description:",
            options=list(SAMPLE_JDS.keys()),
            index=custom_idx,
            help="Choose a preloaded JD to test instant matching or enter custom JD below."
        )

    with jd_sel_col2:
        uploaded_jd_file = st.file_uploader(
            "Or upload Job Description file (PDF, DOCX, TXT):",
            type=["pdf", "docx", "txt"],
            key="jd_file_uploader",
            help="Upload a Job Description document to extract requirements automatically."
        )

    # Handle dropdown selection changes cleanly without running auto-analysis
    # Handle dropdown selection changes cleanly without running auto-analysis
    if selected_sample_jd != st.session_state.last_selected_sample_jd:
        st.session_state.last_selected_sample_jd = selected_sample_jd
        st.session_state.jd_text_content = SAMPLE_JDS.get(selected_sample_jd, "")
        reset_jd_and_insights_session_state()
        st.session_state.jd_input_key += 1

    # Handle uploaded JD file cleanly without running auto-analysis
    if uploaded_jd_file is not None:
        try:
            from src.resume.file_handler import FileHandler
            fh = FileHandler()
            raw_jd_bytes = uploaded_jd_file.read()
            f_info = fh.handle_uploaded_file(raw_jd_bytes, uploaded_jd_file.name)
            if f_info.raw_text and f_info.raw_text != st.session_state.jd_text_content:
                st.session_state.jd_text_content = f_info.raw_text
                reset_jd_and_insights_session_state()
                st.session_state.jd_input_key += 1
        except Exception as e:
            st.warning(f"Unable to parse uploaded JD file: {e}")

    jd_text_input = st.text_area(
        "Job Description Text:",
        value=st.session_state.jd_text_content,
        height=180,
        placeholder="Paste complete Job Description text here...",
        key=f"jd_text_area_{st.session_state.jd_input_key}",
        help="The system will extract target role, experience, required skills, and match against Module 1 candidate profile."
    )
    # Keep session state synced with user typing
    st.session_state.jd_text_content = jd_text_input

    # Reset downstream insights if text was changed away from the analyzed JD
    if st.session_state.get("analyzed_jd_text") and jd_text_input.strip() != st.session_state.analyzed_jd_text:
        reset_jd_and_insights_session_state()

    col_btn, _ = st.columns([2, 3])
    with col_btn:
        analyze_jd_clicked = st.button("🚀 Analyze Match & Rank Candidates", type="primary", use_container_width=True)

    if analyze_jd_clicked:
        if not jd_text_input or not jd_text_input.strip():
            st.warning("⚠️ Please enter or select a Job Description above before analyzing.")
            reset_jd_and_insights_session_state()
        else:
            jd_text_clean = jd_text_input.strip()
            new_jd_id = f"jd_{hashlib.md5(jd_text_clean.encode('utf-8')).hexdigest()[:10]}_{int(time.time()*1000)}"
            reset_jd_and_insights_session_state()
            st.session_state.current_jd_id = new_jd_id
            st.session_state.analyzed_jd_text = jd_text_clean
            st.session_state.jd_analysis_submitted = True

            # STAGE 1: JD EXTRACTION
            st.session_state.jd_extraction_status = "processing"
            try:
                matcher = get_job_matcher()
                active_match = matcher.match_candidate(jd_text_clean, profile)
                if not active_match or not getattr(active_match, "job_title", None):
                    raise ValueError("Could not extract target role or requirements from the provided Job Description.")
                st.session_state.active_jd_match = active_match
                st.session_state.extracted_jd_data = active_match
                st.session_state.jd_extraction_status = "success"
                st.session_state.extraction_jd_id = new_jd_id
            except Exception as e:
                st.session_state.jd_extraction_status = "error"
                st.session_state.jd_extraction_error = str(e)
                st.session_state.extraction_jd_id = None

            # STAGE 2: JD RANKING (Only if Stage 1 succeeded for this exact JD)
            if st.session_state.get("jd_extraction_status") == "success" and st.session_state.get("extraction_jd_id") == new_jd_id:
                st.session_state.jd_ranking_status = "processing"
                try:
                    ranker = get_candidate_ranker()
                    cand_pool = ranker.get_default_candidate_pool(active_profile=profile)
                    ranked_list = ranker.rank_candidates(jd_text_clean, cand_pool)
                    if not ranked_list:
                        raise ValueError("Candidate ranking produced no ranked candidates for the provided Job Description.")
                    st.session_state.ranked_candidates_list = ranked_list
                    st.session_state.jd_ranking_status = "success"
                    st.session_state.ranking_jd_id = new_jd_id
                except Exception as e:
                    st.session_state.jd_ranking_status = "error"
                    st.session_state.jd_ranking_error = str(e)
                    st.session_state.ranking_jd_id = None

    # Authoritative visibility condition
    can_show_advanced_insights = (
        st.session_state.get("jd_extraction_status") == "success"
        and st.session_state.get("jd_ranking_status") == "success"
        and st.session_state.get("current_jd_id") is not None
        and st.session_state.get("extraction_jd_id") == st.session_state.get("current_jd_id")
        and st.session_state.get("ranking_jd_id") == st.session_state.get("current_jd_id")
        and st.session_state.get("active_jd_match") is not None
        and st.session_state.get("ranked_candidates_list") is not None
    )

    if st.session_state.get("jd_extraction_status") == "error":
        st.error(f"❌ **JD Extraction Failed:** {st.session_state.get('jd_extraction_error')}")
    elif st.session_state.get("jd_ranking_status") == "error":
        active_match = st.session_state.get("active_jd_match")
        if active_match:
            render_jd_match_result(active_match)
        st.error(f"❌ **JD Candidate Ranking Failed:** {st.session_state.get('jd_ranking_error')}")
    elif can_show_advanced_insights:
        active_match = st.session_state.active_jd_match
        ranked_list = st.session_state.ranked_candidates_list
        cand_display_name = active_match.candidate_name

        render_jd_match_result(active_match)
        render_candidate_ranking(ranked_list, cand_display_name)
    else:
        st.info("ℹ️ Enter a Job Description above and click **'🚀 Analyze Match & Rank Candidates'** to view matching results.")

    # PART 4: ADVANCED AI INSIGHTS
    if can_show_advanced_insights:
        render_advanced_ai_insights(
            profile=profile,
            active_match=st.session_state.active_jd_match,
            recs=recs if 'recs' in locals() else None,
        )
    else:
        st.markdown('<div id="advanced-insights" class="nav-section-anchor" style="height:0; min-height:0; overflow:hidden; visibility:hidden;"></div>', unsafe_allow_html=True)

else:
    # Zero-height navigation anchors so in-page links have targets before a resume is analyzed
    st.markdown(
        """
        <div id="job-recommendations" class="nav-section-anchor" style="height:0; min-height:0; overflow:hidden; visibility:hidden;"></div>
        <div id="skill-gap-analysis" class="nav-section-anchor" style="height:0; min-height:0; overflow:hidden; visibility:hidden;"></div>
        <div id="jd-matching" class="nav-section-anchor" style="height:0; min-height:0; overflow:hidden; visibility:hidden;"></div>
        <div id="advanced-insights" class="nav-section-anchor" style="height:0; min-height:0; overflow:hidden; visibility:hidden;"></div>
        """,
        unsafe_allow_html=True,
    )

