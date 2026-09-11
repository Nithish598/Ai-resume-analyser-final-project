import json
import re
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.resume.pipeline import extract_candidate_profile
from src.resume.section_detector import SectionDetector
from src.resume.information_extractor import InformationExtractor
from src.resume.validator import ProfileValidator

# 1. JOSHIKA
p_joshika = extract_candidate_profile('data/sample_resumes/12_joshika_multicolumn_resume.pdf')
d_joshika = p_joshika.to_dict()

# 2. DEFFANI
p_deffani = extract_candidate_profile('data/sample_resumes/11_deffani_scanned_multicolumn_resume.pdf')
d_deffani = p_deffani.to_dict()

# 3. NITHISH
with open('tests/test_negative_cases.py', 'r', encoding='utf-8') as fp:
    txt = fp.read()
nithish_text = re.search(r'def test_neg_10_full_student_resume_with_internship_and_education_hierarchy\(\):\s+"""[^"]+"""\s+text = """(.*?)"""', txt, re.DOTALL).group(1)
sec = SectionDetector.detect_sections(nithish_text).sections
p_nithish = InformationExtractor().extract(nithish_text, sec)
p_nithish = ProfileValidator.validate(p_nithish, nithish_text)
d_nithish = p_nithish.to_dict()

print('=== JOSHIKA SUMMARY ===')
print('Name:', d_joshika['personal_info']['name'])
print('Email:', d_joshika['personal_info']['email'])
print('Phone:', d_joshika['personal_info']['phone'])
print('Loc:', d_joshika['personal_info']['location'])
print('Education:')
for e in d_joshika['education']:
    print('  -', e['qualification'], '| Inst:', e['institution'], '| Status:', e['status'], '| Score:', e['score'])
print('Internships:')
for i in d_joshika['internships']:
    print('  -', i['title'], '| Duration:', i['duration'], '| Desc:', i['description'])

print('\n=== DEFFANI SUMMARY ===')
print('Name:', d_deffani['personal_info']['name'])
print('Email:', d_deffani['personal_info']['email'])
print('Phone:', d_deffani['personal_info']['phone'])
print('Loc:', d_deffani['personal_info']['location'])
print('LinkedIn:', d_deffani['personal_info']['linkedin'])
print('Education:')
for e in d_deffani['education']:
    print('  -', e['qualification'], '| Inst:', e['institution'], '| Status:', e['status'], '| Score:', e['score'], '| Expected:', e['expected_year'])
print('Skills count: technical =', len(d_deffani['skills']['technical']), ', soft_skills =', len(d_deffani['skills']['soft_skills']))

print('\n=== NITHISH SUMMARY ===')
print('Name:', d_nithish['personal_info']['name'])
print('Email:', d_nithish['personal_info']['email'])
print('Phone:', d_nithish['personal_info']['phone'])
print('Loc:', d_nithish['personal_info']['location'])
print('Education:')
for e in d_nithish['education']:
    print('  -', e['qualification'], '| Inst:', e['institution'], '| Status:', e['status'], '| Score:', e['score'], '| Expected:', e['expected_year'])
print('Internships:')
for i in d_nithish['internships']:
    print('  -', i['title'], '| Company:', i['company'], '| Duration:', i['duration'])
print('Projects:')
for p in d_nithish['projects']:
    print('  -', p['name'], '| Tech:', p['technologies'])
