"""Candidate Portal: Dashboard, Resume Upload, Lossless Profile, and AI Recommended Roles."""
import os
import json
import html
import datetime
from typing import Dict, Any, List, Optional
import streamlit as st
import pandas as pd

from src.resume.pipeline import ResumeExtractionPipeline
from src.resume.profile_schema import (
    CandidateProfile,
    normalize_education_record,
    normalize_publication,
    format_publication_metadata,
    clean_publication_detail,
    get_education_counts,
    normalize_profile_url,
)
from src.storage.candidate_repository import CandidateRepository
from src.skills.skill_normalizer import SkillNormalizer
from src.recommendation.job_recommender import JobRoleRecommender, JobRoleRecommendation
from src.recommendation.job_role_kb import SKILL_IMPORTANCE_REASONS


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
        getattr(skills, "web_technologies", []),
        getattr(skills, "technical_disciplines", []),
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


def render_profile_link_entry(platform_title: str, platform_key: str, p: Any) -> Optional[str]:
    """Renders a safe clickable profile link."""
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
        
    disp_label = str(label)
    if url and prof_entry.get("valid_format", True):
        return f'**{platform_title}:** <a href="{html.escape(url)}" target="_blank" rel="noopener noreferrer" style="color: #60A5FA; text-decoration: underline; font-weight: 500;">{html.escape(disp_label)} ↗</a>'
    elif disp_label:
        return f"**{platform_title}:** {html.escape(disp_label)}"
    return None


def calculate_profile_completion(profile: Any) -> int:
    """Calculate profile completion percentage from extracted fields."""
    if not profile:
        return 0
    if hasattr(profile, "to_dict"):
        d = profile.to_dict()
    else:
        d = profile if isinstance(profile, dict) else {}

    score = 20  # Base for upload
    if d.get("personal_info", {}).get("name"): score += 15
    if d.get("personal_info", {}).get("email"): score += 10
    if d.get("personal_info", {}).get("phone"): score += 10
    if d.get("summary"): score += 15
    if d.get("skills"): score += 15
    if d.get("education"): score += 15
    return min(100, score)


def render_candidate_portal():
    """Main rendering function for the Candidate Portal."""
    st.markdown('<div class="module-badge">CANDIDATE PORTAL · CAREER INTELLIGENCE</div>', unsafe_allow_html=True)
    
    # Initialize active candidate in session state
    current_profile = st.session_state.get("current_profile")
    current_candidate_id = st.session_state.get("active_candidate_id")

    # If active_candidate_id is present but profile not loaded in session, load from repo
    if not current_profile and current_candidate_id:
        c_record = CandidateRepository.get_candidate(current_candidate_id)
        if c_record:
            current_profile = c_record.get("profile_data")
            st.session_state.current_profile = current_profile

    cand_name = "Candidate"
    if current_profile:
        if hasattr(current_profile, "personal_info"):
            cand_name = current_profile.personal_info.name or "Candidate"
        elif isinstance(current_profile, dict):
            cand_name = current_profile.get("personal_info", {}).get("name") or "Candidate"

    # Tab Navigation for Candidate Portal (Strictly 4 Required Items)
    tab_dash, tab_upload, tab_prof, tab_rec = st.tabs([
        "📊 Candidate Dashboard",
        "📤 Upload & Parse Resume",
        "👤 My Full Profile",
        "🎯 AI Recommended Roles",
    ])

    # -------------------------------------------------------------
    # TAB 1: CANDIDATE DASHBOARD
    # -------------------------------------------------------------
    with tab_dash:
        st.markdown(f'<h2 class="main-header">Welcome, {html.escape(cand_name)} 👋</h2>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Review your extracted profile intelligence, evaluate your skills, and explore AI matched job role recommendations.</p>', unsafe_allow_html=True)

        if not current_profile:
            st.info("💡 **Get Started:** Upload your resume in the **'Upload & Parse Resume'** tab to generate your AI candidate profile and unlock personalized career recommendations.")
        else:
            completion = calculate_profile_completion(current_profile)
            unique_skills = get_all_unique_skills(current_profile.skills if hasattr(current_profile, "skills") else current_profile.get("skills", {}))
            
            recommender = JobRoleRecommender()
            recs = recommender.recommend_all_10_mandatory_roles(current_profile)
            top_match_pct = int(round(recs[0].match_score)) if recs else 0
            cand_tier = recs[0].candidate_tier if recs else "Student / Fresher"

            # 4 KPI Cards
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            with kpi1:
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-value">{completion}%</div>
                    <div class="metric-label">Profile Completion</div>
                </div>''', unsafe_allow_html=True)
            with kpi2:
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-value">{len(unique_skills)}</div>
                    <div class="metric-label">Extracted Skills</div>
                </div>''', unsafe_allow_html=True)
            with kpi3:
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-value">{len(recs)}</div>
                    <div class="metric-label">Career Paths Evaluated</div>
                </div>''', unsafe_allow_html=True)
            with kpi4:
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-value" style="color: #86EFAC;">{top_match_pct}%</div>
                    <div class="metric-label">Top Role Alignment</div>
                </div>''', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Dashboard 2-column view
            c_d1, c_d2 = st.columns([1.1, 1])

            with c_d1:
                st.markdown("#### 🎯 Top AI Career Role Matches")
                if recs:
                    for r in recs[:3]:  # Show top 3 of 10 evaluated roles as quick preview
                        badge_color = "#86EFAC" if r.match_score >= 70 else ("#FCD34D" if r.match_score >= 50 else "#93C5FD")
                        st.markdown(f"""
                        <div style="background: #1E293B; border: 1px solid #334155; border-radius: 10px; padding: 0.9rem 1.1rem; margin-bottom: 0.7rem;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <span style="font-weight: 700; font-size: 1.05rem; color: #FFFFFF;">#{r.rank} {r.icon} {r.role_name}</span>
                                    <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 2px;">{r.category} · {r.match_label}</div>
                                </div>
                                <span style="background: rgba(16, 185, 129, 0.15); color: {badge_color}; border: 1px solid {badge_color}44; padding: 0.3rem 0.7rem; border-radius: 6px; font-weight: 800; font-size: 0.95rem;">{int(round(r.match_score))}% Match</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.caption("No role predictions available.")

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("#### 🛠️ Key Identified Skills")
                chips = "".join([f'<span class="skill-badge">{s}</span>' for s in unique_skills[:12]])
                st.markdown(chips, unsafe_allow_html=True)

            with c_d2:
                st.markdown("#### 🚀 Career Readiness & Strategic Growth")
                if recs:
                    top_rec = recs[0]
                    st.markdown(f"""
                    <div style="background: #1E293B; border: 1px solid #334155; border-radius: 10px; padding: 1.1rem; margin-bottom: 0.8rem;">
                        <div style="font-size: 0.82rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em;">Career Pathway Readiness</div>
                        <div style="font-size: 1.15rem; font-weight: 800; color: #60A5FA; margin: 0.25rem 0 0.5rem 0;">
                            {cand_tier}
                        </div>
                        <div style="font-size: 0.88rem; color: #CBD5E1; line-height: 1.5;">
                            {top_rec.overall_assessment or top_rec.simplified_why_reason}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if top_rec.transferable_strengths:
                        st.markdown("**Your Verified Technical Strengths:**")
                        for strength in top_rec.transferable_strengths[:3]:
                            st.markdown(f"<span style='color: #86EFAC; font-weight: 700;'>✓</span> {strength}", unsafe_allow_html=True)

                    if top_rec.top_improvement:
                        st.markdown(f"<br>**Priority Growth Area:** `{top_rec.top_improvement}`", unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)
                    st.info("💡 Explore detailed skill gap breakdowns, alternative technology paths, and customized learning roadmaps in the **'🎯 AI Recommended Roles'** tab.")
                else:
                    st.caption("Upload a resume to unlock career readiness insights.")


    # -------------------------------------------------------------
    # TAB 2: RESUME UPLOAD & PARSING (MODULE 1 INTEGRATION)
    # -------------------------------------------------------------
    with tab_upload:
        st.markdown("### 📤 Upload & Parse Candidate Resume")
        st.caption("Upload your resume in PDF, DOCX, TXT, or JSON format. Our multi-engine AI extraction pipeline will extract your complete candidate profile losslessly.")

        uploaded_file = st.file_uploader(
            "Choose your resume document:",
            type=["pdf", "docx", "txt", "json"],
            key="candidate_resume_uploader",
        )

        SAMPLE_RESUMES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "sample_resumes")
        sample_options = ["-- None (Upload Custom Document) --"]
        if os.path.exists(SAMPLE_RESUMES_DIR):
            sample_options += sorted([f for f in os.listdir(SAMPLE_RESUMES_DIR) if f.endswith((".pdf", ".docx", ".txt", ".json"))])
        
        selected_sample = st.selectbox(
            "Or select a verified benchmark sample resume to test:",
            options=sample_options,
            key="candidate_sample_selector",
        )

        file_to_process = None
        filename_to_process = ""

        if uploaded_file is not None:
            file_to_process = uploaded_file
            filename_to_process = uploaded_file.name
        elif selected_sample != "-- None (Upload Custom Document) --":
            s_path = os.path.join(SAMPLE_RESUMES_DIR, selected_sample)
            if os.path.exists(s_path):
                file_to_process = s_path
                filename_to_process = selected_sample
                st.info(f"✨ **Benchmark Resume Selected:** `{selected_sample}`")

        c_btn1, c_btn2 = st.columns([4, 1])
        with c_btn1:
            parse_btn = st.button("🚀 Analyze Resume & Build Profile", type="primary", use_container_width=True, key="cand_parse_btn")
        with c_btn2:
            rescan_btn = st.button("🔄 Fresh Re-Scan", use_container_width=True, key="cand_rescan_btn")

        if parse_btn or rescan_btn:
            if not file_to_process:
                st.warning("⚠️ Please upload a resume or select a benchmark resume first.")
            else:
                progress_ph = st.empty()
                with progress_ph.container():
                    st.markdown("""
                    <div style="background: #1E293B; border: 1px solid #475569; border-radius: 12px; padding: 1.2rem; margin: 1rem 0;">
                        <div style="font-size: 1.05rem; font-weight: 700; color: #F8FAFC; margin-bottom: 0.5rem;">
                            🧠 Running AI Extraction Pipeline
                        </div>
                        <div style="font-family: monospace; font-size: 0.84rem; color: #93C5FD; line-height: 1.6;">
                            ✓ Ingesting document bytes<br>
                            ✓ Multi-engine OCR & spatial reading order reconstruction<br>
                            ✓ Deterministic regex rules & 2-pass LLM reasoning<br>
                            ✓ Lossless schema mapping & persistent repository registration...
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    pipeline = ResumeExtractionPipeline()
                    extracted_profile = pipeline.process(file_to_process, filename_to_process)
                    
                    # Save to CandidateRepository
                    saved_record = CandidateRepository.save_candidate(
                        profile=extracted_profile,
                        resume_filename=filename_to_process,
                    )
                    
                    st.session_state.current_profile = extracted_profile
                    st.session_state.active_candidate_id = saved_record["candidate_id"]
                    st.session_state.pipeline = pipeline

                progress_ph.empty()
                st.success(f"✓ **Resume Successfully Analyzed & Registered!** (Candidate ID: `{saved_record['candidate_id']}`)")
                st.rerun()

    # -------------------------------------------------------------
    # TAB 3: MY FULL PROFILE (100% COMPLETE LOSSLESS RENDERING)
    # -------------------------------------------------------------
    with tab_prof:
        if not current_profile:
            st.info("ℹ️ No candidate profile loaded yet. Please upload a resume first.")
        else:
            p_dict = current_profile.to_dict() if hasattr(current_profile, "to_dict") else current_profile
            p_info = p_dict.get("personal_info", {})
            p_exp = p_dict.get("experience")
            p_edu = p_dict.get("education", [])
            p_skills = p_dict.get("skills", {})
            p_summary = p_dict.get("summary") or ""

            # Extract employment status safely
            emp_status = p_dict.get("employment_status")
            if not emp_status and isinstance(p_exp, dict):
                emp_status = p_exp.get("employment_status")
            elif not emp_status and hasattr(current_profile, "experience"):
                emp_status = getattr(current_profile.experience, "employment_status", None)

            cand_display_name = p_info.get('name') or 'Candidate'
            st.markdown(f"### 👤 Candidate Profile: {html.escape(cand_display_name)}")
            if p_info.get("professional_title"):
                st.caption(f"Professional Title: **{p_info.get('professional_title')}**")

            # 1. Contact Information Row
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                st.markdown(f"**Full Name:** {p_info.get('name') or '_Not mentioned in resume_'}")
                if p_info.get("professional_title"):
                    st.markdown(f"**Professional Title:** `{p_info['professional_title']}`")
                st.markdown(f"**Email Address:** {p_info.get('email') or '_Not mentioned in resume_'}")
                st.markdown(f"**Phone Number:** {p_info.get('phone') or '_Not mentioned in resume_'}")
                st.markdown(f"**Location:** {p_info.get('location') or '_Not mentioned in resume_'}")
                st.markdown(f"**Employment Status:** `{emp_status or 'Fresher'}`")
            with c_p2:
                rendered_any_link = False
                for plat_title, plat_key in [
                    ("LinkedIn", "linkedin"), ("GitHub", "github"), ("LeetCode", "leetcode"),
                    ("Kaggle", "kaggle"), ("Portfolio", "portfolio"), ("Personal Website", "personal_website")
                ]:
                    rendered = render_profile_link_entry(plat_title, plat_key, current_profile.personal_info if hasattr(current_profile, "personal_info") else p_info)
                    if rendered:
                        st.markdown(rendered, unsafe_allow_html=True)
                        rendered_any_link = True
                if not rendered_any_link:
                    st.caption("_No online profile links detected in resume._")

            # 2. Professional Summary (100% Full Unsummarized Text)
            st.markdown("---")
            st.markdown("#### 🎯 Professional Summary")
            if p_summary:
                st.markdown(f'<div class="summary-box">{html.escape(p_summary)}</div>', unsafe_allow_html=True)
            else:
                st.caption("_Not mentioned in resume._")

            # 3. Categorized Skills Matrix (Constructed from Complete Master Skill Set)
            st.markdown("---")
            st.markdown("#### 🛠️ Categorized Skills Matrix")
            
            # Construct comprehensive master matrix across all Module 1 evidence & raw text
            categorized_matrix = SkillNormalizer.build_categorized_skills_matrix(current_profile or p_dict)
            
            rendered_skills_count = 0
            for g_name, s_list in categorized_matrix.items():
                if s_list:
                    rendered_skills_count += len(s_list)
                    st.markdown(f"##### {g_name} ({len(s_list)})")
                    st.markdown("".join([f'<span class="skill-badge">{sk}</span>' for sk in s_list]), unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)

            if rendered_skills_count == 0:
                st.caption("_No skills mentioned in resume._")

            # 4. Educational Qualifications & Academic Hierarchy (Exact Fields)
            st.markdown("---")
            st.markdown(f"#### 🎓 Educational Qualifications ({len(p_edu)} Records)")
            if p_edu:
                for idx, edu in enumerate(p_edu, 1):
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
                            elif isinstance(edu, dict) and edu.get("field_of_study") and edu.get("field_of_study") not in (vm["qualification"] or ""):
                                st.markdown(f"🔬 **Field of Study:** {edu['field_of_study']}")
                            
                            if getattr(edu, "specialization", None) and getattr(edu, "specialization", "") != getattr(edu, "field_of_study", ""):
                                st.markdown(f"🔬 **Specialization / Stream:** {edu.specialization}")
                            elif isinstance(edu, dict) and edu.get("specialization") and edu.get("specialization") != edu.get("field_of_study"):
                                st.markdown(f"🔬 **Specialization / Stream:** {edu['specialization']}")
                            elif getattr(edu, "stream", None):
                                st.markdown(f"🔬 **Stream:** {edu.stream}")
                            elif isinstance(edu, dict) and edu.get("stream"):
                                st.markdown(f"🔬 **Stream:** {edu['stream']}")
                                
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
                                st.markdown("<span style='background: #334155; color: #94A3B8; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.8rem; font-weight: 500;'>Status: Not specified</span>", unsafe_allow_html=True)
                            
                            # Full Timeline / Expected Graduation / Year resolution
                            if vm.get("start_year") and (vm.get("expected_year") or vm.get("end_year")):
                                end_disp = vm.get("expected_year") or vm.get("end_year")
                                year_label = "Timeline (Expected)" if "Pursuing" in str(vm.get("status") or "") else "Timeline"
                                st.markdown(f"🗓️ **{year_label}:** {vm['start_year']} – {end_disp}")
                            elif vm.get("expected_year") or vm.get("end_year"):
                                y = vm.get("expected_year") or vm.get("end_year")
                                year_label = "Expected Graduation" if "Pursuing" in str(vm.get("status") or "") else "Year of Completion"
                                st.markdown(f"🗓️ **{year_label}:** {y}")
                            elif vm.get("start_year"):
                                st.markdown(f"🗓️ **Start Year:** {vm['start_year']}")

                            if vm.get("score"):
                                st_label = f"⭐ **{vm.get('score_type') or 'Academic Score'}:**"
                                st.markdown(f"{st_label} `{vm['score']}`")

                        if vm.get("details"):
                            st.markdown("---")
                            st.markdown("**Academic Achievements & Details:**")
                            all_edu_details = list(dict.fromkeys(vm["details"]))
                            for d in all_edu_details:
                                st.markdown(f"• {d}")
            else:
                st.caption("_Not mentioned in resume._")

            # 5. Work & Internships
            if isinstance(p_exp, dict):
                internships = p_exp.get("internships", [])
                full_time = p_exp.get("full_time", [])
            elif isinstance(p_exp, list):
                internships = [e for e in p_exp if isinstance(e, dict) and (e.get("type") == "internship" or e.get("experience_type") == "internship")]
                full_time = [e for e in p_exp if isinstance(e, dict) and (e.get("type") == "full_time" or e.get("experience_type") == "full_time")]
            elif hasattr(current_profile, "experience"):
                internships = getattr(current_profile.experience, "internships", []) or []
                full_time = getattr(current_profile.experience, "full_time", []) or []
            else:
                internships = p_dict.get("internships", []) or []
                full_time = p_dict.get("full_time", []) or []

            st.markdown("---")
            st.markdown(f"#### 💼 Work & Internship Experience")
            if internships or full_time:
                if internships:
                    st.markdown("##### 🎯 Internship Experience")
                    for intern in internships:
                        i_role = (intern.get("role") or intern.get("title") or "Intern") if isinstance(intern, dict) else (getattr(intern, "role", None) or getattr(intern, "title", "Intern"))
                        i_comp = (intern.get("company") or "Company") if isinstance(intern, dict) else (getattr(intern, "company", "Company"))
                        i_dur = (intern.get("duration_display") or intern.get("duration") or "Duration not specified") if isinstance(intern, dict) else (getattr(intern, "duration_display", "Duration not specified"))
                        i_loc = intern.get("location") if isinstance(intern, dict) else getattr(intern, "location", None)
                        i_start = intern.get("start_date") if isinstance(intern, dict) else getattr(intern, "start_date", None)
                        i_end = intern.get("end_date") if isinstance(intern, dict) else getattr(intern, "end_date", None)
                        i_desc = intern.get("description") if isinstance(intern, dict) else getattr(intern, "description", None)
                        i_resps = (intern.get("responsibilities") or []) if isinstance(intern, dict) else (getattr(intern, "responsibilities", []) or [])
                        i_techs = (intern.get("technologies") or []) if isinstance(intern, dict) else (getattr(intern, "technologies", []) or [])
                        i_details = (intern.get("details") or []) if isinstance(intern, dict) else (getattr(intern, "details", []) or [])

                        dur_suffix = f" ({i_dur})" if i_dur and i_dur != "Duration not specified" else ""
                        with st.expander(f"📌 {i_role} @ {i_comp}{dur_suffix}", expanded=True):
                            col_i1, col_i2 = st.columns(2)
                            with col_i1:
                                if i_loc: st.markdown(f"📍 **Location:** {i_loc}")
                                if i_dur and i_dur != "Duration not specified": st.markdown(f"⏱️ **Duration:** {i_dur}")
                            with col_i2:
                                if i_start or i_end:
                                    dur_l = f" (Duration: {i_dur})" if i_dur and i_dur != "Duration not specified" else ""
                                    st.markdown(f"📅 **Timeline:** {i_start or 'N/A'} – {i_end or 'N/A'}{dur_l}")
                            if i_desc: st.markdown(f"**Description:** {i_desc}")
                            if i_resps:
                                st.markdown("**Key Responsibilities & Highlights:**")
                                for r in i_resps: st.markdown(f"- {r}")
                            if i_techs:
                                st.markdown("**Technologies:** " + ", ".join([f"`{t}`" for t in i_techs]))
                            if i_details and i_details != i_resps:
                                st.markdown("**Additional Details:**")
                                for d in i_details: st.markdown(f"- {d}")

                if full_time:
                    st.markdown("##### 💼 Full-Time Professional Experience")
                    for ft in full_time:
                        f_title = (ft.get("title") or ft.get("role") or "Position") if isinstance(ft, dict) else (getattr(ft, "title", None) or getattr(ft, "role", "Position"))
                        f_comp = (ft.get("company") or "Company") if isinstance(ft, dict) else getattr(ft, "company", "Company")
                        f_dur = (ft.get("duration") or "Full-Time") if isinstance(ft, dict) else (getattr(ft, "duration", "Full-Time"))
                        f_loc = ft.get("location") if isinstance(ft, dict) else getattr(ft, "location", None)
                        f_start = ft.get("start_date") if isinstance(ft, dict) else getattr(ft, "start_date", None)
                        f_end = ft.get("end_date") if isinstance(ft, dict) else getattr(ft, "end_date", None)
                        f_desc = ft.get("description") if isinstance(ft, dict) else getattr(ft, "description", None)
                        f_resps = (ft.get("responsibilities") or []) if isinstance(ft, dict) else (getattr(ft, "responsibilities", []) or [])
                        f_techs = (ft.get("technologies") or []) if isinstance(ft, dict) else (getattr(ft, "technologies", []) or [])

                        with st.expander(f"📌 {f_title} @ {f_comp} ({f_dur})", expanded=True):
                            if f_loc: st.markdown(f"📍 **Location:** {f_loc}")
                            if f_start or f_end: st.markdown(f"📅 **Timeline:** {f_start or 'N/A'} – {f_end or 'N/A'}")
                            if f_desc: st.markdown(f"**Description:** {f_desc}")
                            if f_resps:
                                st.markdown("**Key Responsibilities:**")
                                for r in f_resps: st.markdown(f"- {r}")
                            if f_techs:
                                st.markdown("**Technologies:** " + ", ".join([f"`{t}`" for t in f_techs]))
            else:
                st.caption("_No formal employment or internship entries detected. Academic and personal projects are listed under Projects._")

            # 6. Projects & Certifications
            projects = p_dict.get("projects", [])
            certs = p_dict.get("certifications", [])
            
            st.markdown("---")
            col_pr, col_cr = st.columns(2)
            with col_pr:
                st.markdown(f"#### 🚀 Projects ({len(projects)})")
                if projects:
                    for pr in projects:
                        pr_name = (pr.get("name") or pr.get("title") or "Project") if isinstance(pr, dict) else (getattr(pr, "name", None) or getattr(pr, "title", "Project"))
                        pr_type = pr.get("project_type") if isinstance(pr, dict) else getattr(pr, "project_type", None)
                        pr_desc = pr.get("description") if isinstance(pr, dict) else getattr(pr, "description", None)
                        pr_tech = (pr.get("technologies") or []) if isinstance(pr, dict) else (getattr(pr, "technologies", []) or [])
                        pr_url = pr.get("url") if isinstance(pr, dict) else getattr(pr, "url", None)
                        pr_details = (pr.get("details") or []) if isinstance(pr, dict) else (getattr(pr, "details", []) or [])

                        type_sfx = f" ({pr_type})" if pr_type else ""
                        with st.expander(f"📦 {pr_name}{type_sfx}", expanded=True):
                            if pr_desc: st.markdown(f"<p style='font-size: 0.95rem; line-height: 1.55;'>{pr_desc}</p>", unsafe_allow_html=True)
                            if pr_tech: st.markdown("**Technologies:** " + ", ".join([f"`{t}`" for t in pr_tech]))
                            if pr_url: st.markdown(f"🔗 [Project Link / Repository]({pr_url})")
                            if pr_details:
                                for d in pr_details: st.markdown(f"- {d}")
                else:
                    st.caption("_Not mentioned in resume._")

            with col_cr:
                st.markdown(f"#### 📜 Certifications ({len(certs)})")
                if certs:
                    for cr in certs:
                        c_name = cr.get("name") if isinstance(cr, dict) else getattr(cr, "name", "Certification")
                        c_issuer = cr.get("issuer") if isinstance(cr, dict) else getattr(cr, "issuer", None)
                        c_date = cr.get("date") if isinstance(cr, dict) else getattr(cr, "date", None)
                        c_id = cr.get("credential_id") if isinstance(cr, dict) else getattr(cr, "credential_id", None)
                        c_url = cr.get("url") if isinstance(cr, dict) else getattr(cr, "url", None)
                        
                        cert_line = f"• **{c_name}**"
                        if c_issuer: cert_line += f" ({c_issuer})"
                        if c_date: cert_line += f" – {c_date}"
                        if c_id: cert_line += f" (ID: `{c_id}`)"
                        st.markdown(cert_line)
                        if c_url: st.markdown(f"  [Verify Credential]({c_url})")
                else:
                    st.caption("_Not mentioned in resume._")

            # 7. Awards & Achievements
            achievements_raw = (p_dict.get("achievements") or []) + (p_dict.get("awards_achievements") or [])
            achievements = list(dict.fromkeys([str(a).strip() for a in achievements_raw if str(a).strip()]))
            if achievements:
                st.markdown("---")
                st.markdown(f"#### 🏆 Awards & Achievements ({len(achievements)})")
                for ach in achievements:
                    st.markdown(f"• {ach}")

            # 8. Research Publications & Papers
            raw_pubs = p_dict.get("publications") or []
            valid_pubs = [normalize_publication(p) for p in raw_pubs if normalize_publication(p)]
            if valid_pubs:
                st.markdown("---")
                st.markdown(f"#### 📚 Research Publications & Papers ({len(valid_pubs)})")
                for p_dict_item in valid_pubs:
                    pub_title = p_dict_item.get("title") or "Research Publication"
                    pub_authors = p_dict_item.get("authors") or []
                    pub_url = p_dict_item.get("url")
                    pub_desc = p_dict_item.get("description")
                    pub_details = p_dict_item.get("details") or []
                    
                    st.markdown(f"• **{pub_title}**")
                    if pub_authors:
                        authors_str = ", ".join(pub_authors) if isinstance(pub_authors, list) else str(pub_authors)
                        if authors_str.strip():
                            st.caption(f"Authors: _{authors_str.strip()}_")
                    meta_lines = format_publication_metadata(p_dict_item)
                    for m_line in meta_lines:
                        st.markdown(f"  🏛️ _{m_line}_")
                    if pub_url:
                        st.markdown(f"  🔗 [Read Publication / Link]({pub_url})")
                    if pub_desc and isinstance(pub_desc, str) and pub_desc.strip():
                        st.markdown(f"  {pub_desc.strip()}")

            # 9. Spoken Languages
            languages = [str(l).strip() for l in (p_dict.get("languages") or []) if str(l).strip()]
            if languages:
                st.markdown("---")
                st.markdown(f"#### 🌐 Spoken Languages ({len(languages)})")
                st.markdown("".join([f'<span class="skill-badge">{str(l)}</span>' for l in languages]), unsafe_allow_html=True)

            # 10. Interests & Hobbies
            interests = list(dict.fromkeys([str(i).strip() for i in (p_dict.get("interests") or []) + (p_dict.get("hobbies") or []) if str(i).strip()]))
            if interests:
                st.markdown("---")
                st.markdown(f"#### 🎯 Interests & Hobbies ({len(interests)})")
                st.markdown("".join([f'<span class="skill-badge">{str(i)}</span>' for i in interests]), unsafe_allow_html=True)

            # 11. Core Strengths & Personal Attributes
            strengths = [str(s).strip() for s in (p_dict.get("strengths") or []) if str(s).strip()]
            if strengths:
                st.markdown("---")
                st.markdown(f"#### 💡 Core Strengths & Attributes ({len(strengths)})")
                st.markdown("".join([f'<span class="skill-badge">{str(s)}</span>' for s in strengths]), unsafe_allow_html=True)

            # 12. Additional Qualifications
            add_quals = p_dict.get("additional_qualifications") or []
            if add_quals:
                st.markdown("---")
                st.markdown(f"#### 🌟 Additional Qualifications ({len(add_quals)})")
                for aq in add_quals:
                    st.markdown(f"• {aq}")

            # 13. Declaration & Signature
            decl = p_dict.get("declaration")
            if decl and isinstance(decl, dict) and any(decl.values()):
                st.markdown("---")
                st.markdown("#### ✍️ Declaration")
                if decl.get("text"):
                    st.caption(f'"{decl["text"]}"')
                col_d1, col_d2, col_d3 = st.columns(3)
                with col_d1:
                    if decl.get("place"): st.markdown(f"📍 **Place:** {decl['place']}")
                with col_d2:
                    if decl.get("date"): st.markdown(f"📅 **Date:** {decl['date']}")
                with col_d3:
                    if decl.get("signature"): st.markdown(f"✍️ **Signature:** `{decl['signature']}`")

            # 14. Additional Extracted Sections (Completeness Check)
            other_secs = p_dict.get("other_sections") or []
            if other_secs:
                st.markdown("---")
                st.markdown("#### 📑 Additional Extracted Resume Information")
                for sec in other_secs:
                    sec_name = sec.get("section_name") or "Extra Section"
                    sec_content = sec.get("content") or ""
                    with st.expander(f"📌 {sec_name}", expanded=False):
                        st.write(sec_content)

            # 15. Export Button
            st.markdown("---")
            json_str = json.dumps(p_dict, indent=2)
            st.download_button(
                label="⬇️ Download Full Structured Candidate JSON",
                data=json_str,
                file_name=f"candidate_{cand_display_name}.json".replace(" ", "_").lower(),
                mime="application/json",
                type="primary",
                use_container_width=True,
            )

    # -------------------------------------------------------------
    # TAB 4: AI JOB RECOMMENDATIONS (ENTERPRISE CAREER INTELLIGENCE)
    # -------------------------------------------------------------
    with tab_rec:
        st.markdown("### 🎯 AI Job Recommendations & Career Intelligence")
        st.markdown('<p class="sub-header">Structured, evidence-based career alignment and skill gap analysis evaluated against real-world engineering benchmarks.</p>', unsafe_allow_html=True)

        if not current_profile:
            st.info("ℹ️ Upload your resume in the **'Upload & Parse Resume'** tab to view your personalized job recommendations.")
        else:
            recommender = JobRoleRecommender()
            # Always evaluate ALL 10 mandatory roles — no role is ever omitted regardless of score
            recs = recommender.recommend_all_10_mandatory_roles(current_profile)

            if not recs:
                st.warning("⚠️ Insufficient technical skills detected in the profile to generate confident recommendations. Please check your extracted skills in **My Full Profile**.")
            else:
                def render_role_skill_gap_view(r: JobRoleRecommendation):
                    """Detailed, role-specific full skill gap view."""
                    st.markdown(f"### {r.role_name.upper()}")
                    
                    if r.career_tip:
                        st.info(f"💡 **Overall Improvement Recommendation:** {r.career_tip}")

                    # Section: Your Skills
                    st.markdown("#### Your Skills")
                    if r.all_matched_skills:
                        for sk in r.all_matched_skills:
                            st.markdown(f"<span style='color: #86EFAC; font-weight: 700;'>✓</span> `{sk}`", unsafe_allow_html=True)
                    else:
                        st.caption("_General foundation / academic coursework detected._")

                    # Real-World Technical Archetype Chips
                    if r.matched_tools or r.matched_frameworks or r.matched_databases:
                        st.markdown("<div style='margin-top: 0.6rem;'></div>", unsafe_allow_html=True)
                        t_cols = st.columns(3)
                        with t_cols[0]:
                            if r.matched_tools:
                                st.markdown(f"🛠️ **Tools:** " + ", ".join([f"`{t}`" for t in r.matched_tools]))
                        with t_cols[1]:
                            if r.matched_frameworks:
                                st.markdown(f"📦 **Frameworks:** " + ", ".join([f"`{f}`" for f in r.matched_frameworks]))
                        with t_cols[2]:
                            if r.matched_databases:
                                st.markdown(f"🗄️ **Databases:** " + ", ".join([f"`{d}`" for d in r.matched_databases]))

                    st.markdown("---")

                    # Section: Skills to Improve (Complete list with clear 1-2 sentence explanations)
                    st.markdown("#### Skills to Improve")

                    if r.tool_gaps or r.framework_gaps or r.database_gaps:
                        g_cols = st.columns(3)
                        with g_cols[0]:
                            if r.tool_gaps:
                                st.markdown(f"⚠️ **Missing Tools:** " + ", ".join([f"`{t}`" for t in r.tool_gaps]))
                        with g_cols[1]:
                            if r.framework_gaps:
                                st.markdown(f"⚠️ **Missing Frameworks:** " + ", ".join([f"`{f}`" for f in r.framework_gaps]))
                        with g_cols[2]:
                            if r.database_gaps:
                                st.markdown(f"⚠️ **Missing Databases:** " + ", ".join([f"`{d}`" for d in r.database_gaps]))
                        st.markdown("<div style='margin-bottom: 0.8rem;'></div>", unsafe_allow_html=True)
                    
                    gaps_rendered = set()
                    
                    # 1. Render categorized missing competencies
                    if r.missing_competencies:
                        for cat_name, gaps in r.missing_competencies.items():
                            st.markdown(f"**{cat_name}**")
                            for g in gaps:
                                sk_name = g["skill"]
                                sk_reason = g.get("reason") or SKILL_IMPORTANCE_REASONS.get(sk_name.lower(), f"Learn {sk_name} for production {r.role_name} workflows.")
                                gaps_rendered.add(sk_name.lower())
                                st.markdown(f"""
                                <div style="margin-bottom: 0.75rem; padding-left: 0.4rem;">
                                    <div style="font-weight: 700; color: #F8FAFC; font-size: 0.96rem;">{sk_name}</div>
                                    <div style="color: #CBD5E1; font-size: 0.88rem; margin-top: 0.15rem; line-height: 1.45;">{sk_reason}</div>
                                </div>
                                """, unsafe_allow_html=True)
                    
                    # 2. Render any remaining skills in all_skills_to_improve
                    remaining_gaps = [s for s in r.all_skills_to_improve if s.lower() not in gaps_rendered]
                    if remaining_gaps:
                        st.markdown("**Additional Competency Areas**")
                        for sk_name in remaining_gaps:
                            sk_reason = SKILL_IMPORTANCE_REASONS.get(sk_name.lower(), f"Learn {sk_name} to strengthen your qualification for {r.role_name}.")
                            st.markdown(f"""
                            <div style="margin-bottom: 0.75rem; padding-left: 0.4rem;">
                                <div style="font-weight: 700; color: #F8FAFC; font-size: 0.96rem;">{sk_name}</div>
                                <div style="color: #CBD5E1; font-size: 0.88rem; margin-top: 0.15rem; line-height: 1.45;">{sk_reason}</div>
                            </div>
                            """, unsafe_allow_html=True)

                    if not r.all_skills_to_improve and not r.missing_competencies:
                        st.success("✓ Excellent! All core and required skills for this role are demonstrated in your resume.")


                    # Domain Category Gap Metrics
                    if r.category_gap_scores:
                        st.markdown("---")
                        st.markdown("#### 📈 Competency Scores by Technical Domain")
                        cat_cols = st.columns(min(4, len(r.category_gap_scores)))
                        for idx, (cat_name, cat_stat) in enumerate(r.category_gap_scores.items()):
                            col_idx = idx % len(cat_cols)
                            with cat_cols[col_idx]:
                                st.metric(
                                    label=cat_name,
                                    value=f"{cat_stat['matched']}/{cat_stat['total']} ({cat_stat['pct']}%)",
                                    delta=f"{cat_stat['tier']} Tier",
                                    delta_color="normal" if cat_stat['pct'] >= 50 else "inverse"
                                )

                    # Alternative Skills Satisfied
                    if r.alternatives_satisfied:
                        st.markdown("---")
                        st.markdown("#### 🧩 Alternative Technologies Satisfied")
                        for alt in r.alternatives_satisfied:
                            st.success(f"✓ **{alt['cluster_name']}:** Demonstrated **`{alt['demonstrated_option']}`** satisfies requirement with zero penalty (Options: _{alt['options_list']}_).")

                    # Missing Prerequisites Alert
                    if r.prerequisites_missing:
                        st.markdown("---")
                        st.markdown("#### ⚠️ Missing Prerequisites")
                        for prereq in r.prerequisites_missing:
                            st.warning(f"⚠️ **{prereq['skill']} Prerequisite:** Missing **`{prereq['missing_prerequisite']}`** — {prereq['explanation']}")

                    # Targeted Project Blueprints
                    if r.targeted_project_blueprints:
                        st.markdown("---")
                        st.markdown("#### 🛠️ Targeted Portfolio Project Blueprints")
                        st.caption("Practical project blueprints designed to specifically close your missing skill gaps:")
                        for p_bp in r.targeted_project_blueprints:
                            st.markdown(f"""
                            <div style="background: #0F172A; border: 1px solid #334155; border-radius: 8px; padding: 0.85rem 1.1rem; margin-bottom: 0.6rem;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span style="font-weight: 700; color: #60A5FA; font-size: 0.95rem;">{p_bp['tier']}: {p_bp['name']}</span>
                                </div>
                                <div style="font-size: 0.86rem; color: #E2E8F0; margin-top: 0.25rem;">{p_bp['description']}</div>
                                <div style="margin-top: 0.4rem; font-size: 0.78rem; color: #94A3B8;"><b>Skills Targeted:</b> {', '.join(p_bp['skills'])}</div>
                            </div>
                            """, unsafe_allow_html=True)

                    # Learning Roadmap
                    if r.learning_roadmap_phases:
                        st.markdown("---")
                        st.markdown("#### 🎯 Sequential Learning Roadmap")
                        for phase_item in r.learning_roadmap_phases:
                            st.markdown(f"• **{phase_item['phase']}:** {phase_item['focus']}")

                # --------------------------------------------------
                # ALL 10 MANDATORY ROLE RECOMMENDATION CARDS
                # Sorted: highest match → lowest match
                # ALL 10 always shown — no role is ever omitted
                # --------------------------------------------------
                st.markdown(f"**📊 Evaluating all 10 career paths — {len(recs)} roles assessed:**")

                for idx, rec in enumerate(recs, 1):
                    # Dynamic colour: green ≥80, yellow ≥55, blue ≥35, red <35
                    if rec.match_score >= 80:
                        card_color = "#86EFAC"   # green
                        border_style = "2px solid #22C55E44"
                    elif rec.match_score >= 55:
                        card_color = "#FCD34D"   # yellow
                        border_style = "1px solid #F59E0B44"
                    elif rec.match_score >= 35:
                        card_color = "#93C5FD"   # blue
                        border_style = "1px solid #3B82F644"
                    else:
                        card_color = "#F87171"   # red (low match)
                        border_style = "1px solid #EF444444"

                    st.markdown(f"""
                    <div style="background: #1E293B; border: {border_style}; border-radius: 12px; padding: 1.1rem 1.4rem; margin-top: 1rem; margin-bottom: 0.6rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.6rem;">
                            <div>
                                <span style="font-size: 1.25rem; font-weight: 800; color: #FFFFFF;">
                                    {idx}. {rec.icon} {rec.role_name}
                                </span>
                                <span style="font-size: 0.82rem; color: #94A3B8; margin-left: 0.6rem;">({rec.category})</span>
                            </div>
                            <span style="background: rgba(16, 185, 129, 0.12); color: {card_color}; border: 1px solid {card_color}55; padding: 0.35rem 0.85rem; border-radius: 8px; font-weight: 800; font-size: 0.95rem;">
                                Match: {int(round(rec.match_score))}%
                            </span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    c_left, c_right = st.columns(2)
                    with c_left:
                        st.markdown(f"**Matched Skills ({len(rec.all_matched_skills)})**")
                        if rec.all_matched_skills:
                            for sk in rec.all_matched_skills:
                                st.markdown(f"<span style='color: #86EFAC; font-weight: 700;'>✓</span> `{sk}`", unsafe_allow_html=True)
                        else:
                            st.caption("_General academic foundation_")

                    with c_right:
                        st.markdown(f"**Skill Gap / Improve ({len(rec.all_skills_to_improve)})**")
                        if rec.all_skills_to_improve:
                            for sk_entry in (rec.skill_gaps_formatted or [f"{s} — HIGH" for s in rec.all_skills_to_improve]):
                                parts = sk_entry.split(" — ")
                                sk_title = parts[0]
                                prio = parts[1] if len(parts) > 1 else "HIGH"
                                prio_color = "#EF4444" if prio == "HIGH" else "#F59E0B"
                                st.markdown(f"<span style='color: #FCD34D; font-weight: 700;'>⚠</span> `{sk_title}` <span style='font-size: 0.72rem; background: {prio_color}22; color: {prio_color}; padding: 0.12rem 0.45rem; border-radius: 4px; border: 1px solid {prio_color}44; font-weight: 800; vertical-align: middle;'>{prio}</span>", unsafe_allow_html=True)
                        else:
                            st.markdown("<span style='color: #86EFAC; font-weight: 600;'>✓ All required skills met!</span>", unsafe_allow_html=True)


                    with st.expander(f"🔍 View Skill Gap for {rec.role_name}", expanded=False):
                        render_role_skill_gap_view(rec)


                # --------------------------------------------------
                # STRATEGIC CROSS-ROLE SKILL GROWTH PLAN
                # --------------------------------------------------
                roadmap = recommender.get_overall_skill_development_roadmap(recs)
                if roadmap:
                    cand_skills_list = recommender.extract_flat_candidate_skills(current_profile)
                    
                    st.markdown("---")
                    st.markdown("### 🚀 Your Strategic Skill Growth Plan")
                    st.markdown("Cross-role priority skills recommended to accelerate your career readiness across multiple career pathways:")

                    st.markdown("**Your Verified Strengths in Uploaded Resume:**")
                    if cand_skills_list:
                        st.markdown(" ".join([f'<span class="skill-badge" style="background: rgba(34, 197, 94, 0.15); color: #86EFAC; border-color: rgba(34, 197, 94, 0.35);">✓ {s}</span>' for s in cand_skills_list[:10]]), unsafe_allow_html=True)

                    st.markdown("<br>**Priority Roadmap Steps (in Dependency Order):**", unsafe_allow_html=True)
                    for item in roadmap:
                        st.markdown(f"""
                        <div style="background: #1E293B; border-left: 4px solid #60A5FA; border-radius: 0 8px 8px 0; padding: 0.75rem 1.1rem; margin-bottom: 0.55rem;">
                            <div style="font-weight: 700; font-size: 0.95rem; color: #F8FAFC;">
                                {item['rank']}. Master {item['skill']}
                            </div>
                            <div style="font-size: 0.84rem; color: #CBD5E1; margin-top: 0.2rem;">
                                {item['reason']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)


