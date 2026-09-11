"""HR / Admin Portal: Analytics Dashboard, Job Creation (Form & AI JD Parser), Job Management, Candidate Repository, AI Matching Leaderboard, and Application Tracking."""
import os
import json
import html
import datetime
from typing import Dict, Any, List, Optional
import streamlit as st
import pandas as pd

from src.storage.candidate_repository import CandidateRepository
from src.storage.job_repository import JobRepository
from src.storage.application_repository import ApplicationRepository
from src.jobs.jd_parser import JobDescriptionParser
from src.matching.matching_engine import MatchingEngine
from src.ranking.candidate_ranker import CandidateRanker


def render_hr_portal():
    """Main rendering function for the HR / Admin Portal."""
    st.markdown('<div class="module-badge">HR & TALENT ACQUISITION · ADMIN PORTAL</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="main-header">Recruitment Operations & Candidate Intelligence</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Manage job requisitions, analyze JD requirements, rank talent with multi-signal AI matching, and oversee the candidate hiring pipeline.</p>', unsafe_allow_html=True)

    # Initialize Seed Jobs if needed
    JobRepository.initialize_seeds_if_empty()

    # HR Portal Tab Navigation
    tab_dash, tab_create, tab_manage_jobs, tab_cands, tab_matching, tab_pipeline = st.tabs([
        "📊 Recruitment Dashboard",
        "➕ Post New Job Requisition",
        "📁 Manage Job Postings",
        "👥 Candidate Talent Pool",
        "🎯 AI Candidate Matching & Ranking",
        "📋 Applicant Pipeline (ATS)",
    ])

    # Load shared data
    all_jobs = JobRepository.get_all_jobs()
    active_jobs = [j for j in all_jobs if str(j.get("status", "Active")).lower() == "active"]
    all_candidates = CandidateRepository.get_all_candidates()
    all_applications = ApplicationRepository.get_all_applications()

    # -------------------------------------------------------------
    # TAB 1: RECRUITMENT DASHBOARD (KPIS)
    # -------------------------------------------------------------
    with tab_dash:
        st.markdown("### 📈 Executive Recruitment Metrics")
        
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-value">{len(active_jobs)}</div>
                <div class="metric-label">Active Job Openings</div>
            </div>''', unsafe_allow_html=True)
        with k2:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-value">{len(all_candidates)}</div>
                <div class="metric-label">Candidates in Talent Pool</div>
            </div>''', unsafe_allow_html=True)
        with k3:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-value">{len(all_applications)}</div>
                <div class="metric-label">Total Applications Received</div>
            </div>''', unsafe_allow_html=True)
        with k4:
            shortlisted_total = len([a for a in all_applications if a.get("status") in ["Shortlisted", "Selected"]])
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-value" style="color: #86EFAC;">{shortlisted_total}</div>
                <div class="metric-label">Shortlisted Candidates</div>
            </div>''', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col_h1, col_h2 = st.columns([1.1, 1])
        with col_h1:
            st.markdown("#### 📊 Candidate Application Pipeline Funnel")
            status_counts = {
                "Applied": len([a for a in all_applications if a.get("status") == "Applied"]),
                "Under Review": len([a for a in all_applications if a.get("status") == "Under Review"]),
                "Shortlisted": len([a for a in all_applications if a.get("status") == "Shortlisted"]),
                "Selected": len([a for a in all_applications if a.get("status") == "Selected"]),
                "Rejected": len([a for a in all_applications if a.get("status") == "Rejected"]),
            }
            funnel_df = pd.DataFrame(list(status_counts.items()), columns=["Pipeline Stage", "Candidate Count"])
            st.dataframe(funnel_df, use_container_width=True, hide_index=True)

        with col_h2:
            st.markdown("#### ⚡ Quick Actions")
            st.info(
                "**Recruiter Capabilities:**\n\n"
                "• **Create Job with AI Parser:** Upload/paste raw JDs to auto-extract structured skills & requirements.\n"
                "• **Multi-Signal Candidate Ranking:** Rank all candidates against selected jobs with skill gap inspection.\n"
                "• **Real-Time Status Synchronization:** Shortlist or reject candidates with instant candidate updates."
            )

    # -------------------------------------------------------------
    # TAB 2: CREATE / POST NEW JOB (FORM & AI JD PARSER)
    # -------------------------------------------------------------
    with tab_create:
        st.markdown("### ➕ Create New Job Requisition")
        st.caption("Choose between our structured form input or AI-powered Job Description extraction parser.")

        create_mode = st.radio("Select Creation Mode:", ["🤖 AI Job Description Parser (Paste/Upload JD)", "📝 Structured Job Form"], horizontal=True)

        if "AI Job Description" in create_mode:
            st.markdown("#### 🧠 AI Job Description Intelligence Parser")
            st.caption("Paste a full job description or upload a document (PDF, DOCX, TXT) to automatically extract required skills, experience, and responsibilities.")

            jd_raw_text = st.text_area(
                "Paste Complete Job Description Text:",
                height=180,
                placeholder="We are looking for a Senior Python Developer with 3+ years of experience in Django, PostgreSQL, and AWS..."
            )

            jd_file = st.file_uploader("Or Upload Job Description Document (PDF, DOCX, TXT):", type=["pdf", "docx", "txt"], key="jd_doc_uploader")

            if st.button("⚡ Extract Job Requirements via AI", type="primary", use_container_width=True):
                if not jd_raw_text.strip() and jd_file is None:
                    st.warning("⚠️ Please paste job description text or upload a document first.")
                else:
                    with st.spinner("Analyzing Job Description semantics and extracting structured requirements..."):
                        if jd_file is not None:
                            extracted_jd = JobDescriptionParser.parse_file(jd_file, jd_file.name)
                        else:
                            extracted_jd = JobDescriptionParser.parse_text(jd_raw_text)
                        
                        st.session_state.draft_jd = extracted_jd.to_dict()
                        st.success("✓ Job requirements successfully extracted! Review and edit below before saving.")

            if "draft_jd" in st.session_state:
                draft = st.session_state.draft_jd
                st.markdown("---")
                st.markdown("#### 📝 Review & Confirm Extracted Job Posting")

                with st.form("confirm_extracted_job_form"):
                    f_title = st.text_input("Job Title:", value=draft.get("title", "Software Engineer"))
                    f_comp = st.text_input("Company Name:", value=draft.get("company", "Enterprise"))
                    f_loc = st.text_input("Location / Mode:", value=draft.get("location", "Hybrid"))
                    f_type = st.selectbox("Employment Type:", ["Full-Time", "Part-Time", "Contract", "Internship"], index=0)
                    f_exp = st.number_input("Minimum Experience Required (Years):", min_value=0.0, max_value=20.0, value=float(draft.get("experience_years", 1.0)), step=0.5)
                    f_edu = st.text_input("Education Requirements:", value=draft.get("education", "Bachelor's Degree in Computer Science or related"))
                    
                    req_skills_str = ", ".join(draft.get("required_skills", []))
                    f_req_skills = st.text_input("Required Skills (comma-separated):", value=req_skills_str)
                    
                    pref_skills_str = ", ".join(draft.get("preferred_skills", []))
                    f_pref_skills = st.text_input("Preferred / Nice-to-Have Skills (comma-separated):", value=pref_skills_str)
                    
                    f_salary = st.text_input("Salary Range:", value=draft.get("salary_range", "Competitive"))
                    f_desc = st.text_area("Full Job Description:", value=draft.get("description", ""), height=100)
                    
                    submit_save = st.form_submit_button("💾 Save & Publish Job Requisition", type="primary", use_container_width=True)

                    if submit_save:
                        r_list = [s.strip() for s in f_req_skills.split(",") if s.strip()]
                        p_list = [s.strip() for s in f_pref_skills.split(",") if s.strip()]
                        
                        new_job = JobRepository.create_job(
                            title=f_title,
                            company=f_comp,
                            location=f_loc,
                            employment_type=f_type,
                            experience_years=f_exp,
                            education=f_edu,
                            required_skills=r_list,
                            preferred_skills=p_list,
                            salary_range=f_salary,
                            description=f_desc,
                            responsibilities=draft.get("responsibilities", []),
                        )
                        del st.session_state.draft_jd
                        st.success(f"🎉 **Job Requisition Published!** (Job ID: `{new_job['job_id']}`)")
                        st.rerun()

        else:
            # Structured Form
            st.markdown("#### 📝 Manual Job Creation Form")
            with st.form("manual_job_create_form"):
                m_title = st.text_input("Job Title:", placeholder="e.g. Python Developer")
                m_comp = st.text_input("Company Name:", placeholder="e.g. CloudTech Solutions")
                m_loc = st.text_input("Location:", placeholder="e.g. Chennai / Remote")
                m_type = st.selectbox("Employment Type:", ["Full-Time", "Contract", "Internship", "Part-Time"])
                m_exp = st.number_input("Minimum Experience (Years):", min_value=0.0, max_value=20.0, value=1.0, step=0.5)
                m_edu = st.text_input("Education Requirements:", value="Bachelor's Degree in CS / IT or related")
                m_req_skills = st.text_input("Required Skills (comma-separated):", placeholder="e.g. Python, SQL, Django, Git")
                m_pref_skills = st.text_input("Preferred Skills (comma-separated):", placeholder="e.g. AWS, Docker, Redis")
                m_salary = st.text_input("Salary Range:", placeholder="e.g. ₹6,00,000 - ₹9,00,000 / year")
                m_desc = st.text_area("Job Description:", placeholder="Describe the role responsibilities and requirements...")

                m_submit = st.form_submit_button("🚀 Publish Job Requisition", type="primary", use_container_width=True)

                if m_submit:
                    if not m_title.strip() or not m_req_skills.strip():
                        st.warning("⚠️ Please provide at least a Job Title and Required Skills.")
                    else:
                        r_list = [s.strip() for s in m_req_skills.split(",") if s.strip()]
                        p_list = [s.strip() for s in m_pref_skills.split(",") if s.strip()]
                        saved_job = JobRepository.create_job(
                            title=m_title,
                            company=m_comp or "Enterprise",
                            location=m_loc or "Hybrid",
                            employment_type=m_type,
                            experience_years=m_exp,
                            education=m_edu,
                            required_skills=r_list,
                            preferred_skills=p_list,
                            salary_range=m_salary or "Competitive",
                            description=m_desc,
                        )
                        st.success(f"✓ **Job Successfully Created & Published!** (ID: `{saved_job['job_id']}`)")
                        st.rerun()

    # -------------------------------------------------------------
    # TAB 3: MANAGE JOB POSTINGS
    # -------------------------------------------------------------
    with tab_manage_jobs:
        st.markdown("### 📁 Manage Job Postings")
        st.caption("Review active and closed positions, track applicant volumes, and toggle posting statuses.")

        if not all_jobs:
            st.info("ℹ️ No job requisitions created yet.")
        else:
            for job in all_jobs:
                j_id = job["job_id"]
                apps_for_job = ApplicationRepository.get_applications_by_job(j_id)
                status = job.get("status", "Active")
                status_color = "#86EFAC" if status.lower() == "active" else "#94A3B8"

                with st.expander(f"💼 **{job.get('title')}** @ **{job.get('company')}** — Status: {status.upper()} ({len(apps_for_job)} Applicants)", expanded=False):
                    c_m1, c_m2 = st.columns([2, 1])
                    with c_m1:
                        st.markdown(f"**Job ID:** `{j_id}` | 📍 **Location:** `{job.get('location')}` | ⏱️ **Req Exp:** `{job.get('experience_years')} yrs`")
                        st.markdown(f"💰 **Salary:** `{job.get('salary_range')}` | 📅 **Posted:** `{job.get('created_at', '')[:10]}`")
                        st.markdown(f"**Required Skills:** {', '.join(job.get('required_skills', []))}")
                        if job.get("preferred_skills"):
                            st.markdown(f"**Preferred Skills:** {', '.join(job.get('preferred_skills', []))}")
                        if job.get("description"):
                            st.caption(f"Description: {job['description'][:200]}...")
                    with c_m2:
                        st.markdown(f"#### Status: <span style='color: {status_color}; font-weight: 800;'>{status}</span>", unsafe_allow_html=True)
                        st.markdown(f"👥 **Total Applicants:** `{len(apps_for_job)}`")
                        
                        # Toggle Action
                        new_toggle_status = "Closed" if status.lower() == "active" else "Active"
                        if st.button(f"Mark as {new_toggle_status}", key=f"toggle_{j_id}", use_container_width=True):
                            JobRepository.update_job_status(j_id, new_toggle_status)
                            st.rerun()

                        if st.button("🗑️ Delete Job", key=f"del_{j_id}", use_container_width=True):
                            JobRepository.delete_job(j_id)
                            st.success(f"Job {j_id} deleted.")
                            st.rerun()

    # -------------------------------------------------------------
    # TAB 4: CANDIDATE TALENT POOL / REPOSITORY
    # -------------------------------------------------------------
    with tab_cands:
        st.markdown("### 👥 Candidate Talent Pool")
        st.caption("Searchable candidate database parsed and registered through Module 1.")

        if not all_candidates:
            st.info("ℹ️ No candidate profiles stored yet. Upload resumes in the Candidate Portal to populate the talent pool.")
        else:
            c_search = st.text_input("🔍 Search Candidates by Name, Email, or Skill:", placeholder="e.g. Nithish, Python, SQL")
            
            c_filtered = all_candidates
            if c_search.strip():
                cs = c_search.strip().lower()
                c_filtered = [
                    c for c in all_candidates
                    if cs in c.get("name", "").lower()
                    or cs in c.get("email", "").lower()
                    or any(cs in sk.lower() for sk in c.get("skills", []))
                ]

            st.markdown(f"**Total Candidates Found: {len(c_filtered)}**")

            for cand in c_filtered:
                c_id = cand["candidate_id"]
                with st.expander(f"👤 **{cand.get('name', 'Candidate')}** ({cand.get('professional_title') or 'Profile'}) — {cand.get('experience_years', 0)} yrs exp | {len(cand.get('skills', []))} skills", expanded=False):
                    c_col1, c_col2 = st.columns([2, 1])
                    with c_col1:
                        st.markdown(f"**Candidate ID:** `{c_id}` | ✉️ **Email:** `{cand.get('email')}` | ☎️ **Phone:** `{cand.get('phone')}`")
                        st.markdown(f"📍 **Location:** `{cand.get('location')}` | 🏷️ **Status:** `{cand.get('employment_status')}`")
                        st.markdown(f"🎓 **Education:** `{cand.get('highest_education')}`")
                        
                        if cand.get("skills"):
                            st.markdown("**Skills:**")
                            st.markdown("".join([f'<span class="skill-badge">{s}</span>' for s in cand["skills"][:15]]), unsafe_allow_html=True)
                            
                        # Show full education history
                        prof_data = cand.get("profile_data") or {}
                        cand_edu = prof_data.get("education") or []
                        if cand_edu:
                            st.markdown("**Education Breakdown:**")
                            for ce in cand_edu:
                                c_deg = ce.get("qualification") or ce.get("degree") or "Degree"
                                c_inst = ce.get("institution") or "Institution"
                                c_stat = f" ({ce['status']})" if ce.get("status") else ""
                                c_yr = f" – Expected: {ce['expected_year']}" if ce.get("expected_year") else (f" – Year: {ce['end_year']}" if ce.get("end_year") else "")
                                c_sc = f" | Score: {ce['score']}" if ce.get("score") else ""
                                st.markdown(f"• **{c_deg}** @ _{c_inst}_{c_stat}{c_yr}{c_sc}")

                        # Show projects
                        cand_projs = prof_data.get("projects") or []
                        if cand_projs:
                            st.markdown(f"**Key Projects ({len(cand_projs)}):**")
                            for cp in cand_projs[:2]:
                                cp_name = cp.get("name") or cp.get("title") or "Project"
                                cp_tech = f" ({', '.join(cp.get('technologies', []))})" if cp.get("technologies") else ""
                                st.markdown(f"• **{cp_name}**{cp_tech}")

                    with c_col2:
                        st.markdown(f"📅 **Registered:** `{cand.get('created_at', '')[:10]}`")
                        st.markdown(f"📄 **Resume Ref:** `{cand.get('resume_filename')}`")
                        
                        # Full JSON export
                        c_json = json.dumps(cand.get("profile_data", cand), indent=2)
                        st.download_button(
                            label="⬇️ Export Candidate JSON",
                            data=c_json,
                            file_name=f"{cand.get('name', 'candidate')}_profile.json".replace(" ", "_").lower(),
                            mime="application/json",
                            key=f"exp_cand_{c_id}",
                            use_container_width=True,
                        )

    # -------------------------------------------------------------
    # TAB 5: AI CANDIDATE MATCHING & MULTI-SIGNAL RANKING
    # -------------------------------------------------------------
    with tab_matching:
        st.markdown("### 🎯 AI Candidate Matching & Leaderboard Ranking")
        st.caption("Select any active job posting to match and rank all candidates in the talent pool using multi-dimensional scoring and deep skill gap analysis.")

        if not active_jobs:
            st.warning("⚠️ No active jobs available to match. Please create a job first.")
        elif not all_candidates:
            st.warning("⚠️ No candidates in the talent pool yet. Upload resumes in the Candidate Portal first.")
        else:
            job_choices = {f"{j['title']} @ {j['company']} ({j['job_id']})": j for j in active_jobs}
            selected_job_label = st.selectbox("Select Target Job Opening for Matching:", list(job_choices.keys()))
            target_job = job_choices[selected_job_label]

            # Display Target Job Summary Banner
            st.markdown(f"""
            <div style="background: #1E293B; border: 1px solid #334155; border-radius: 12px; padding: 1.1rem; margin: 1rem 0;">
                <div style="font-size: 1.1rem; font-weight: 700; color: #F8FAFC;">
                    🎯 Target Requisition: <span style="color: #60A5FA;">{target_job['title']}</span>
                </div>
                <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 0.3rem;">
                    Required Experience: <b>{target_job['experience_years']} yrs</b> | Required Skills: <b>{', '.join(target_job.get('required_skills', []))}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Run Matching Engine
            ranked_candidates = MatchingEngine.rank_all_candidates_for_job(target_job, all_candidates)

            st.markdown(f"#### 🏆 Ranked Candidate Leaderboard ({len(ranked_candidates)} evaluated)")

            for cand_res in ranked_candidates:
                score = cand_res["overall_match_score"]
                score_color = "#86EFAC" if score >= 80 else ("#FCD34D" if score >= 60 else "#F87171")
                
                with st.expander(f"**Rank {cand_res['rank']}: {cand_res['candidate_name']}** — Fit Score: **{score}%** ({cand_res['recommendation_status']})", expanded=(cand_res['rank'] == 1)):
                    c_rk1, c_rk2 = st.columns([1.8, 1])
                    with c_rk1:
                        st.markdown(f"👤 **Candidate Name:** `{cand_res['candidate_name']}` | ✉️ **Email:** `{cand_res['email']}`")
                        st.markdown(f"⏱️ **Experience:** `{cand_res['experience_years']} yrs` ({cand_res['experience_status']})")
                        st.markdown(f"💬 **AI Rationale:** _{cand_res['reason']}_")
                        
                        st.markdown("---")
                        # Skill Gap Analysis
                        col_g1, col_g2 = st.columns(2)
                        with col_g1:
                            st.markdown(f"✅ **Matched Required Skills ({len(cand_res['matched_skills'])}):**")
                            if cand_res["matched_skills"]:
                                st.markdown("".join([f'<span class="skill-badge" style="background: rgba(34, 197, 94, 0.15); color: #86EFAC; border-color: rgba(34, 197, 94, 0.3);">{s}</span>' for s in cand_res["matched_skills"]]), unsafe_allow_html=True)
                            else:
                                st.caption("No direct skill matches.")
                        with col_g2:
                            st.markdown(f"⚠️ **Missing Required Skills ({len(cand_res['missing_skills'])}):**")
                            if cand_res["missing_skills"]:
                                st.markdown("".join([f'<span class="skill-badge" style="background: rgba(245, 158, 11, 0.15); color: #FCD34D; border-color: rgba(245, 158, 11, 0.3);">{s}</span>' for s in cand_res["missing_skills"]]), unsafe_allow_html=True)
                            else:
                                st.markdown("<span style='color: #86EFAC; font-size: 0.85rem; font-weight: 600;'>✓ All required skills met!</span>", unsafe_allow_html=True)

                    with c_rk2:
                        st.markdown(f"""
                        <div style="background: #0F172A; border: 1px solid {score_color}; border-radius: 12px; padding: 1rem; text-align: center; margin-bottom: 0.8rem;">
                            <div style="font-size: 0.78rem; color: #94A3B8; text-transform: uppercase;">Composite Match Score</div>
                            <div style="font-size: 2rem; font-weight: 800; color: {score_color};">{score}%</div>
                            <div style="font-size: 0.8rem; color: #E2E8F0; margin-top: 0.2rem;">Skill Coverage: <b>{cand_res['skill_match_percentage']}%</b></div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Status Actions
                        existing_app = ApplicationRepository.find_application(cand_res["candidate_id"], target_job["job_id"])
                        curr_status = existing_app.get("status", "Not Applied") if existing_app else "Not Applied"
                        st.markdown(f"Current Application Status: **`{curr_status}`**")

                        col_act1, col_act2 = st.columns(2)
                        with col_act1:
                            if st.button("⭐ Shortlist", key=f"sl_{cand_res['candidate_id']}_{target_job['job_id']}", use_container_width=True):
                                if not existing_app:
                                    existing_app = ApplicationRepository.create_application(
                                        cand_res["candidate_id"],
                                        target_job["job_id"],
                                        match_score_pct=score,
                                        matched_skills=cand_res["matched_skills"],
                                        missing_skills=cand_res["missing_skills"],
                                    )
                                ApplicationRepository.update_status(existing_app["application_id"], "Shortlisted", "Shortlisted based on strong AI match ranking.")
                                st.success("✓ Candidate Shortlisted!")
                                st.rerun()

                        with col_act2:
                            if st.button("❌ Reject", key=f"rj_{cand_res['candidate_id']}_{target_job['job_id']}", use_container_width=True):
                                if not existing_app:
                                    existing_app = ApplicationRepository.create_application(
                                        cand_res["candidate_id"],
                                        target_job["job_id"],
                                        match_score_pct=score,
                                        matched_skills=cand_res["matched_skills"],
                                        missing_skills=cand_res["missing_skills"],
                                    )
                                ApplicationRepository.update_status(existing_app["application_id"], "Rejected", "Does not meet core requirements.")
                                st.warning("Candidate Rejected.")
                                st.rerun()

    # -------------------------------------------------------------
    # TAB 6: APPLICANT PIPELINE (ATS)
    # -------------------------------------------------------------
    with tab_pipeline:
        st.markdown("### 📋 Applicant Tracking System (ATS) Pipeline")
        st.caption("Manage all incoming job applications, update review stages, and add recruiter notes.")

        if not all_applications:
            st.info("ℹ️ No applications submitted yet.")
        else:
            filter_status = st.selectbox("Filter Applications by Status:", ["All Statuses", "Applied", "Under Review", "Shortlisted", "Selected", "Rejected"])
            
            apps_to_show = all_applications
            if filter_status != "All Statuses":
                apps_to_show = [a for a in all_applications if a.get("status") == filter_status]

            st.markdown(f"**Showing {len(apps_to_show)} application(s):**")

            for app in apps_to_show:
                app_id = app["application_id"]
                st_val = app.get("status", "Applied")
                
                with st.expander(f"📄 **{app.get('candidate_name')}** ➔ **{app.get('job_title')}** ({app.get('company')}) — Status: {st_val.upper()}", expanded=False):
                    col_p1, col_p2 = st.columns([2, 1])
                    with col_p1:
                        st.markdown(f"**Application ID:** `{app_id}` | ✉️ **Candidate Email:** `{app.get('candidate_email')}`")
                        st.markdown(f"📅 **Applied Date:** `{app.get('applied_at', '')[:10]}` | ⭐ **Fit Score:** `{app.get('match_score_pct')}%`")
                        if app.get("matched_skills"):
                            st.markdown(f"✅ **Matched Skills:** {', '.join(app['matched_skills'])}")
                        if app.get("missing_skills"):
                            st.markdown(f"⚠️ **Missing Skills:** {', '.join(app['missing_skills'])}")
                    with col_p2:
                        st.markdown("#### Update Status & Notes")
                        new_st = st.selectbox(
                            "Stage Status:",
                            ["Applied", "Under Review", "Shortlisted", "Selected", "Rejected"],
                            index=["Applied", "Under Review", "Shortlisted", "Selected", "Rejected"].index(st_val) if st_val in ["Applied", "Under Review", "Shortlisted", "Selected", "Rejected"] else 0,
                            key=f"status_sel_{app_id}",
                        )
                        r_notes = st.text_input("Recruiter Notes:", value=app.get("recruiter_notes", ""), key=f"notes_{app_id}")
                        
                        if st.button("💾 Save Status Update", key=f"save_app_{app_id}", type="primary", use_container_width=True):
                            ApplicationRepository.update_status(app_id, new_st, r_notes)
                            st.success(f"✓ Application {app_id} updated to '{new_st}'!")
                            st.rerun()
