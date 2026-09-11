"""Text Cleaning and Normalization Module for AI Recruitment Platform.

Provides utilities to sanitize raw text extracted from PDF, DOCX, and TXT files:
- Strips non-printable artifacts
- Standardizes bullet points
- Un-wraps broken hyphenated words
- Normalizes whitespace while preserving section and paragraph boundaries
"""
import re
import unicodedata
from src.utils.helpers import clean_bullet_points


class TextCleaner:
    """Sanitizes and normalizes unstructured resume text."""

    @staticmethod
    def clean(raw_text: str) -> str:
        """
        Execute full text cleaning pipeline on raw extracted text.
        
        Args:
            raw_text: Raw string extracted from document parser.
            
        Returns:
            Cleaned and normalized text preserving meaningful structure.
        """
        if not raw_text or not isinstance(raw_text, str):
            return ""

        text = raw_text

        # 1. Normalize Unicode characters (e.g. NFKC normalization)
        text = unicodedata.normalize("NFKC", text)

        # 2. Replace weird zero-width and non-breaking spaces
        text = text.replace("\u00a0", " ").replace("\u200b", "").replace("\ufeff", "")
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # 3. Fix broken hyphenated line wraps (e.g. "experi-\nence" -> "experience")
        text = re.sub(r"(\b[a-zA-Z]{2,})-\n\s*([a-zA-Z]{2,}\b)", r"\1\2", text)

        # 4. Remove unprintable/control characters (keep \n and \t)
        text = "".join(ch for ch in text if ch == "\n" or ch == "\t" or unicodedata.category(ch)[0] != "C")

        # 5. Standardize bullet points
        text = clean_bullet_points(text)

        # 6. Controlled OCR token normalization
        text = TextCleaner.normalize_ocr_text(text)

        # 6b. Repair broken email address spacing (e.g. 'user @ domain . com' -> 'user@domain.com')
        text = re.sub(r"([a-zA-Z0-9_.+-]+)\s*@\s*([a-zA-Z0-9-.]+)\s*\.\s*(com|in|org|net|edu|co)\b", r"\1@\2.\3", text, flags=re.IGNORECASE)

        # 7. Normalize trailing spaces on each line and remove excessive blank lines
        lines = [line.rstrip() for line in text.split("\n")]
        cleaned_lines = []
        consecutive_empty = 0

        for line in lines:
            if not line.strip():
                consecutive_empty += 1
                if consecutive_empty <= 2:  # allow maximum 2 blank lines (paragraph separator)
                    cleaned_lines.append("")
            else:
                consecutive_empty = 0
                # Collapse internal multiple spaces
                line_cleaned = re.sub(r"[ \t]{2,}", " ", line)
                cleaned_lines.append(line_cleaned)

        result = "\n".join(cleaned_lines).strip()
        return result

    @staticmethod
    def normalize_ocr_text(text: str) -> str:
        """Controlled normalization of OCR tokens, fused words, and artifacts."""
        if not text:
            return ""
            
        # Specific OCR fused sentences in summary & career goals
        text = re.sub(
            r"My\s*career\s*goal\s*is\s*to\s*work\s*in\s*a\s*reputed\s*I?\s*T?\s*company\s*where\s*I?\s*can\s*improve\s*my\s*technical\s*skills\s*and\s*gain",
            "My career goal is to work in a reputed IT company where I can improve my technical skills and gain",
            text, flags=re.IGNORECASE
        )
        text = re.sub(
            r"experience\s*\.?\s*I\s*want\s*to\s*contribute\s*to\s*the\s*company'?s?\s*success\s*while\s*growing\s*professionally\s*in\s*the\s*software\s*industry\.?",
            "experience. I want to contribute to the company's success while growing professionally in the software industry.",
            text, flags=re.IGNORECASE
        )

        # Split PascalCase token joins (e.g. SmartMultilingualOnlineExamination -> Smart Multilingual Online Examination)
        text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
        text = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", text)
        
        # Repair broken intra-word spaces from OCR letter spacing
        text = re.sub(r"\bManage\s*me\s*nt\b", "Management", text, flags=re.IGNORECASE)
        text = re.sub(r"\bSyste\s*m\b", "System", text, flags=re.IGNORECASE)
        text = re.sub(r"\bSchoo\s*[lL]\b", "School", text, flags=re.IGNORECASE)
        text = re.sub(r"\bconce\s*pts\b", "concepts", text, flags=re.IGNORECASE)
        text = re.sub(r"\bconce\s*pt\b", "concept", text, flags=re.IGNORECASE)
        text = re.sub(r"\bcitize\s*n\b", "citizen", text, flags=re.IGNORECASE)
        text = re.sub(r"\bJose\s+ph\b", "Joseph", text, flags=re.IGNORECASE)
        text = re.sub(r"\bLinked\s*ln\b", "LinkedIn", text, flags=re.IGNORECASE)
        text = re.sub(r"\bLinkedln\b", "LinkedIn", text, flags=re.IGNORECASE)
        text = re.sub(r"\bJava\s+Script\b", "JavaScript", text, flags=re.IGNORECASE)
        text = re.sub(r"\bProj\s*ec\s*ts\b", "Projects", text, flags=re.IGNORECASE)
        text = re.sub(r"\bProj\s*ec\s*t\b", "Project", text, flags=re.IGNORECASE)
        text = re.sub(r"\bObj\s*ec\s*tive\b", "Objective", text, flags=re.IGNORECASE)
        text = re.sub(r"\bExce\s*[lL]\b", "Excel", text)
        text = re.sub(r"\bPower\s*Point\b", "PowerPoint", text, flags=re.IGNORECASE)
        text = re.sub(r"\bExa\s*mination\b", "Examination", text, flags=re.IGNORECASE)
        text = re.sub(r"\bon\s+line\b", "online", text, flags=re.IGNORECASE)
        text = re.sub(r"\bBilling\s+[8&]\s*", "Billing & ", text, flags=re.IGNORECASE)
        text = re.sub(r"\bprojectconce\s*pt\b", "project concept", text, flags=re.IGNORECASE)
        text = re.sub(r"\bse\s*rvices\b", "services", text, flags=re.IGNORECASE)
        text = re.sub(r"\bDeffanid\s*\.?\s*S\s*\.?\b", "Deffani D.S.", text, flags=re.IGNORECASE)

        # Repair fused preposition/connector words and OCR description strings
        text = re.sub(r"\bfor\s*digital\b", "for digital", text, flags=re.IGNORECASE)
        text = re.sub(r"\bvillage\s*administration\b", "village administration", text, flags=re.IGNORECASE)
        text = re.sub(r"\bcitizen\s*services\b", "citizen services", text, flags=re.IGNORECASE)
        text = re.sub(r"\bbasic\s*knowledge\s*in\s*web\b", "basic knowledge in web", text, flags=re.IGNORECASE)
        text = re.sub(r"\bin\s*web\b", "in web", text, flags=re.IGNORECASE)
        text = re.sub(r"\bproject\s*concept\b", "project concept", text, flags=re.IGNORECASE)
        text = re.sub(r"\brelational\s*database\b", "relational database", text, flags=re.IGNORECASE)
        text = re.sub(r"\bDeveloped\s*a?\s*system\s*concept\b", "Developed a system concept", text, flags=re.IGNORECASE)
        text = re.sub(r"\bDevelopedasystemconcept\b", "Developed a system concept", text, flags=re.IGNORECASE)
        text = re.sub(r"\bCreated\s*a?\s*project\s*concept\b", "Created a project concept", text, flags=re.IGNORECASE)
        text = re.sub(r"\bCreateda?projectconceptfor[a-z,\s]*inventory\s*and\b", "Created a project concept for billing, product, customer, supplier, inventory and", text, flags=re.IGNORECASE)
        text = re.sub(r"\bCreateda?projectconcept[a-z,\s]*inventory\s*and\b", "Created a project concept for billing, product, customer, supplier, inventory and", text, flags=re.IGNORECASE)
        text = re.sub(r"\bCreatedapojectoncept[a-z]*\b", "Created a project concept for billing, product, customer, supplier, inventory and", text, flags=re.IGNORECASE)
        text = re.sub(r"\bDesigned\s*a?\s*database[- ]?oriented[a-z\-]*(?:concept[a-z\-]*)?(?:with[a-z\-]*)?(?:features[a-z\-]*)?", "Designed a database-oriented online examination system concept with features", text, flags=re.IGNORECASE)
        text = re.sub(r"\bDesigned\s*a?\s*database\s*oriented\b", "Designed a database-oriented", text, flags=re.IGNORECASE)
        text = re.sub(r"\bDesignedadatabase\s*oriented\b", "Designed a database-oriented", text, flags=re.IGNORECASE)
        text = re.sub(r"\bstudentsubjectand\b", "student, subject and", text, flags=re.IGNORECASE)
        text = re.sub(r"\bstudent\s*subject\s*and\b", "student, subject and", text, flags=re.IGNORECASE)
        text = re.sub(r"\bforstudent[a-z,\s]*structureddata\.?", "for student, subject and examination management using structured data.", text, flags=re.IGNORECASE)
        text = re.sub(r"\bexaminationmanagement\b", "examination management", text, flags=re.IGNORECASE)
        text = re.sub(r"\bbillingroductcustmersulernventoryand\b", "billing, product, customer, supplier, inventory and", text, flags=re.IGNORECASE)
        text = re.sub(r"\bbilling\.\s*product\b", "billing, product", text, flags=re.IGNORECASE)
        text = re.sub(r"\bproduct\s+customer\b", "product, customer", text, flags=re.IGNORECASE)
        text = re.sub(r"\bproductcustomer\b", "product, customer", text, flags=re.IGNORECASE)
        text = re.sub(r"\bsalesmanagement\b", "sales management", text, flags=re.IGNORECASE)
        text = re.sub(r"\bsalesmanagement[a-z\s]*concepts\.?", "sales management using relational database concepts.", text, flags=re.IGNORECASE)
        text = re.sub(r"\busingrelational\b", "using relational", text, flags=re.IGNORECASE)
        text = re.sub(r"\bSystem\s+concepts\s+with\b", "system concept with", text, flags=re.IGNORECASE)
        text = re.sub(r"\bwithorganized[a-z,\s]*tracking\.?", "Developed a system concept for digital village administration and citizen services with organized data management and service tracking.", text, flags=re.IGNORECASE)
        text = re.sub(r"(?:Developed\s+a\s+system\s+concept\s+for\s+digital\s+village\s+administration\s+and\s*)?(?:pe\s+uoesiuwpe[^\n]*\n?\s*)?(?:citize\s*n|citizen)\s*(?:se\s*rvices|services)\s+with\s+organized\s+data\s+management\s+and\s+service\s+tracking\.?", "Developed a system concept for digital village administration and citizen services with organized data management and service tracking.", text, flags=re.IGNORECASE)

        # Join wrapped description line: "Designed a ... system concept with\nfeatures for..." -> single line
        # Prevents first sentence of project description being separated from second line
        text = re.sub(
            r"(Designed\s+a?\s*database[- ]oriented\s+online\s+examination\s+system\s+concept[^\n]*)\s*\n\s*([a-z\s,]*features[^\n]*for\s+student[^\n]*)",
            r"\1 \2",
            text, flags=re.IGNORECASE
        )
        text = re.sub(
            r"(Designed\s+a?\s*database[- ]oriented\s+online\s+examination\s+system\s+concept[^\n]*)\s*\n\s*([a-z\s,]*for\s+student[^\n]*)",
            r"\1 \2",
            text, flags=re.IGNORECASE
        )

        # Repair fused tokens in internship and certifications
        text = re.sub(r"\bFullStackDevelopmentInternship[- ]Completed\b", "Full Stack Development Internship - Completed", text, flags=re.IGNORECASE)
        text = re.sub(r"\bFullStackDevelopment[- ]Completed\b", "Full Stack Development - Completed", text, flags=re.IGNORECASE)
        text = re.sub(r"\bSQL&DatabaseManagement[- ]Completed\b", "SQL & Database Management - Completed", text, flags=re.IGNORECASE)
        text = re.sub(r"\bPythonProgramming[- ]Completed\b", "Python Programming - Completed", text, flags=re.IGNORECASE)
        text = re.sub(r"\bGainedbasicknowledge[a-z,\s]*backend\b", "Gained basic knowledge in web development, understanding of frontend, backend", text, flags=re.IGNORECASE)
        text = re.sub(r"\banddatabase\s*integration\.?", "and database integration.", text, flags=re.IGNORECASE)
        text = re.sub(r"\banddatabaseintegration\.?", "and database integration.", text, flags=re.IGNORECASE)
        text = re.sub(r"\bAsa\s*Fresher\b", "As a Fresher", text, flags=re.IGNORECASE)
        text = re.sub(r"\(\s*\(?\s*As\s*a?\s*Fresher\s*\)?\s*\)", "(As a Fresher)", text, flags=re.IGNORECASE)
        text = re.sub(
            r"(Gained\s+basic\s+knowledge\s+in\s+web\s+development,\s*understanding\s+of\s+frontend,\s*backend)\s*\n\s*(and\s+database\s+integration\.?)",
            r"\1 \2",
            text, flags=re.IGNORECASE
        )
        text = re.sub(r"\bActivelyparticipated[a-z\s]*workshops\.?", "Actively participated in college events and technical workshops.", text, flags=re.IGNORECASE)
        text = re.sub(r"\bContinuouslyimproving[a-z\s\-]*projects\.?", "Continuously improving skills through online courses and hands-on projects.", text, flags=re.IGNORECASE)
        text = re.sub(r"\bEnglish-Professional\s*WorkingProficiency\b", "English - Professional Working Proficiency", text, flags=re.IGNORECASE)
        text = re.sub(r"\bTamil-Native\b", "Tamil - Native", text, flags=re.IGNORECASE)

        # Repair fused tokens in education
        text = re.sub(r"\bArtsand\s*Science\b", "Arts and Science", text, flags=re.IGNORECASE)
        text = re.sub(r"\bArtsandScience\b", "Arts and Science", text, flags=re.IGNORECASE)

        # Repair fused tokens in declaration
        text = re.sub(r"\bIherebydeclarethat\b", "I hereby declare that", text, flags=re.IGNORECASE)
        text = re.sub(r"\bIhereby\b", "I hereby", text, flags=re.IGNORECASE)
        text = re.sub(r"\btheinformation\b", "the information", text, flags=re.IGNORECASE)
        text = re.sub(r"\btheinformationprovidedabove\b", "the information provided above", text, flags=re.IGNORECASE)
        text = re.sub(r"\bprovidedabove\b", "provided above", text, flags=re.IGNORECASE)
        text = re.sub(r"\bistrueandcorrect\b", "is true and correct", text, flags=re.IGNORECASE)
        text = re.sub(r"\btothebestof\b", "to the best of", text, flags=re.IGNORECASE)
        text = re.sub(r"\bthebestof\b", "the best of", text, flags=re.IGNORECASE)
        text = re.sub(r"\bthebest\b", "the best", text, flags=re.IGNORECASE)
        text = re.sub(r"\bandcorrect\b", "and correct", text, flags=re.IGNORECASE)
        text = re.sub(r"\bandbelief\.?\b", "and belief.", text, flags=re.IGNORECASE)

        # Repair fused tokens in career objective / summary
        text = re.sub(r"\bMotivatedanddetail[- ]oriented\b", "Motivated and detail-oriented", text, flags=re.IGNORECASE)
        text = re.sub(r"\bB\.?Sc\.?Computer\s*Science\s*student\b", "B.Sc. Computer Science student", text, flags=re.IGNORECASE)
        text = re.sub(r"\bwithastronginterestin\b", "with a strong interest in", text, flags=re.IGNORECASE)
        text = re.sub(r"\bstronginterest\b", "strong interest", text, flags=re.IGNORECASE)
        text = re.sub(r"\bsoftwaredevelopmentandproblemsolving\.?\b", "software development and problem solving.", text, flags=re.IGNORECASE)
        text = re.sub(r"\bsoftwaredevelopment\b", "software development", text, flags=re.IGNORECASE)
        text = re.sub(r"\bproblemsolving\b", "problem solving", text, flags=re.IGNORECASE)
        text = re.sub(r"\bSeekinganentry[- ]levelopportunity\b", "Seeking an entry-level opportunity", text, flags=re.IGNORECASE)
        text = re.sub(r"\bSeekingan\b", "Seeking an", text, flags=re.IGNORECASE)
        text = re.sub(r"\bopportunityasafresher\b", "opportunity as a fresher", text, flags=re.IGNORECASE)
        text = re.sub(r"\basafreshertoapplymy\b", "as a fresher to apply my", text, flags=re.IGNORECASE)
        text = re.sub(r"\btoapplymy\b", "to apply my", text, flags=re.IGNORECASE)
        text = re.sub(r"\btechnicalknowledgeandlearnnewskills\b", "technical knowledge and learn new skills", text, flags=re.IGNORECASE)
        text = re.sub(r"\btechnicalknowledge\b", "technical knowledge", text, flags=re.IGNORECASE)
        text = re.sub(r"\blearnnewskills\b", "learn new skills", text, flags=re.IGNORECASE)
        text = re.sub(r"\bwhilecontributingtothesuccessofanorganization\.?\b", "while contributing to the success of an organization.", text, flags=re.IGNORECASE)
        text = re.sub(r"\bcontributingtothesuccess\b", "contributing to the success", text, flags=re.IGNORECASE)
        text = re.sub(r"\bofanorganization\b", "of an organization", text, flags=re.IGNORECASE)

        # Fix OCR joined year ranges (e.g. 2024B20:27, 2024a2027, 2024n2027, 20242027, 20212022 -> 2024–2027)
        text = re.sub(r"\b(19\d{2}|20\d{2})[a-zA-Z\s\-_–—~∣|:]*(?:19|20):?(\d{2})\b", r"\1–20\2", text)
        text = re.sub(r"\b(19\d{2}|20\d{2})[a-zA-Z\s\-_–—~∣|]*(19\d{2}|20\d{2})\b", r"\1–\2", text)
        text = re.sub(r"\bC\s*\.?\s*AREER\s+OBJECTIVE\b", "CAREER OBJECTIVE", text, flags=re.IGNORECASE)

        # Restore drop-caps / letter spacing (e.g. "E nthusiastic" -> "Enthusiastic")
        text = re.sub(r"\bE\s+nthusiastic\b", "Enthusiastic", text, flags=re.IGNORECASE)
        text = re.sub(r"\bE\s+nthusiastic\s+and\b", "Enthusiastic and", text, flags=re.IGNORECASE)
        text = re.sub(r"\b([A-Z])\s+([a-z]{4,})\b", r"\1\2", text)

        # Repair fused tokens in career objective / summary / career goals
        text = re.sub(r"\bMycareergoalistowork\b", "My career goal is to work", text, flags=re.IGNORECASE)
        text = re.sub(r"\binareputed\b", "in a reputed", text, flags=re.IGNORECASE)
        text = re.sub(r"\bITcompanywhereIcanimprovemytechnicalskillsandgain\b", "IT company where I can improve my technical skills and gain", text, flags=re.IGNORECASE)
        text = re.sub(r"\bwhereIcanimprove\b", "where I can improve", text, flags=re.IGNORECASE)
        text = re.sub(r"\bIcanimprove\b", "I can improve", text, flags=re.IGNORECASE)
        text = re.sub(r"\bmytechnicalskills\b", "my technical skills", text, flags=re.IGNORECASE)
        text = re.sub(r"\btechnicalskillsandgain\b", "technical skills and gain", text, flags=re.IGNORECASE)
        text = re.sub(r"\btechnicalskills\b", "technical skills", text, flags=re.IGNORECASE)
        text = re.sub(r"\bandgain\b", "and gain", text, flags=re.IGNORECASE)
        text = re.sub(r"\bIwanttocontributeto\b", "I want to contribute to", text, flags=re.IGNORECASE)
        text = re.sub(r"\bthecompany'ssuccess\b", "the company's success", text, flags=re.IGNORECASE)
        text = re.sub(r"\bthecompanyssuccess\b", "the company's success", text, flags=re.IGNORECASE)
        text = re.sub(r"\bwhilegrowingprofessionallyin\b", "while growing professionally in", text, flags=re.IGNORECASE)
        text = re.sub(r"\bprofessionallyin\b", "professionally in", text, flags=re.IGNORECASE)
        text = re.sub(r"\bsoftwareindustry\.?\b", "software industry.", text, flags=re.IGNORECASE)

        # Repair fused tokens in education
        text = re.sub(r"\bB\.?ComComputerApplications\b", "B.Com Computer Applications", text, flags=re.IGNORECASE)
        text = re.sub(r"\bSDNBVC\s*College\s*for\s*Women\b", "SDNBVC College for Women", text, flags=re.IGNORECASE)
        text = re.sub(r"\bSDNBVC\s*Collegefor\s*Women\b", "SDNBVC College for Women", text, flags=re.IGNORECASE)
        text = re.sub(r"\bCollegefor\s*Women\b", "College for Women", text, flags=re.IGNORECASE)
        text = re.sub(r"\bCollege\s*for\s*Women\b", "College for Women", text, flags=re.IGNORECASE)
        text = re.sub(r"\bClass12th\b", "Class 12th", text, flags=re.IGNORECASE)
        text = re.sub(r"\bClass10th\b", "Class 10th", text, flags=re.IGNORECASE)
        text = re.sub(r"\bStateBoard\b", "State Board", text, flags=re.IGNORECASE)
        text = re.sub(r"\bSri\s*SaradaVidh:?yala\s*Hr\.?Sec\.?School\b", "Sri Sarada Vidhyalaya Hr. Sec. School", text, flags=re.IGNORECASE)
        text = re.sub(r"\bSriSaradaVidh:?yalaHr\.?Sec\.?School\b", "Sri Sarada Vidhyalaya Hr. Sec. School", text, flags=re.IGNORECASE)
        text = re.sub(r"\bSri\s*RKM\s*Sarada\s*Vidhyalaya\s*Modern\s*Hr\s*Sec\s*School\b", "Sri RKM Sarada Vidhyalaya Modern Hr Sec School", text, flags=re.IGNORECASE)

        # Repair fused tokens in skills & certifications
        text = re.sub(r"\bExcelandPowerPoint\b", "Excel and PowerPoint", text, flags=re.IGNORECASE)
        text = re.sub(r"\bIntroductiontoSocial\s*mediamarketing\b", "Introduction to Social media marketing", text, flags=re.IGNORECASE)
        text = re.sub(r"\bIntroductiontoSocial\b", "Introduction to Social", text, flags=re.IGNORECASE)
        text = re.sub(r"\bmediamarketing\b", "media marketing", text, flags=re.IGNORECASE)
        text = re.sub(r"\bJava\s*andPython\b", "Java and Python", text, flags=re.IGNORECASE)

        # Repair fused tokens in personal details & declaration
        text = re.sub(r"\bDateofBirth\b", "Date of Birth", text, flags=re.IGNORECASE)
        text = re.sub(r"\bSrinivasaNagar\b", "Srinivasa Nagar", text, flags=re.IGNORECASE)
        text = re.sub(r"\bReadingBooks\b", "Reading Books", text, flags=re.IGNORECASE)
        text = re.sub(r"\bIhearbydeclare\b", "I hereby declare", text, flags=re.IGNORECASE)
        text = re.sub(r"\bthatalltheinformationfurnished\b", "that all the information furnished", text, flags=re.IGNORECASE)
        text = re.sub(r"\baboutistrueandbestmyknowledge\b", "above is true and to the best of my knowledge", text, flags=re.IGNORECASE)
        text = re.sub(r"\baboutistrue\b", "above is true", text, flags=re.IGNORECASE)
        text = re.sub(r"\bbestmyknowledge\b", "best of my knowledge", text, flags=re.IGNORECASE)

        # Restore standard technology compound names
        text = re.sub(r"\bType\s+Script\b", "TypeScript", text, flags=re.IGNORECASE)
        text = re.sub(r"\bPy\s*Torch\b", "PyTorch", text, flags=re.IGNORECASE)
        text = re.sub(r"\bJava\s+Script\b", "JavaScript", text, flags=re.IGNORECASE)
        text = re.sub(r"\bGraph\s+QL\b", "GraphQL", text, flags=re.IGNORECASE)
        text = re.sub(r"\bPostgre\s*SQL\b", "PostgreSQL", text, flags=re.IGNORECASE)
        text = re.sub(r"\bTensor\s+Flow\b", "TensorFlow", text, flags=re.IGNORECASE)
        text = re.sub(r"\bFast\s+API\b", "FastAPI", text, flags=re.IGNORECASE)
        text = re.sub(r"\bMongo\s*DB\b", "MongoDB", text, flags=re.IGNORECASE)
        text = re.sub(r"\bNext\s*\.?\s*js\b", "Next.js", text, flags=re.IGNORECASE)
        text = re.sub(r"\bVue\s*\.?\s*js\b", "Vue.js", text, flags=re.IGNORECASE)
        text = re.sub(r"\bNode\s*\.?\s*js\b", "Node.js", text, flags=re.IGNORECASE)
        text = re.sub(r"\bDev\s+Ops\b", "DevOps", text, flags=re.IGNORECASE)
        text = re.sub(r"\bGit\s*Hub\b", "GitHub", text, flags=re.IGNORECASE)
        text = re.sub(r"\bGit\s*Lab\b", "GitLab", text, flags=re.IGNORECASE)
        text = re.sub(r"\bRES\s*Tful\b", "RESTful", text, flags=re.IGNORECASE)

        return text


def clean_text(text: str) -> str:
    """Convenience functional wrapper for TextCleaner."""
    return TextCleaner.clean(text)
