import re, os, json
from datetime import date
from collections import Counter

# ── Paths
KB_FILE   = "C:/Users/callanco/StrateGPT_V0/usp_strategy_docs.txt"
EXTRACTED = "C:/Users/callanco/StrateGPT_V0/extracted_docs.txt"
AMB45_EXT = "C:/Users/callanco/StrateGPT_V0/amb45_extracted.txt"
OUT_FILE  = "C:/Users/callanco/StrateGPT_V0/document_index.json"
AMB45_BASE = "US Program - Ambition 2045"

# ── Year extraction
def get_year(name):
    for m in re.finditer(r'(?<!\d)(20\d{2})(0[1-9]|1[0-2])\d{2}(?!\d)', name):
        return int(m.group(1))
    for m in re.finditer(r'(?<!\d)\d{4}(20\d{2}|19\d{2})(?!\d)', name):
        y = int(m.group(1))
        if 1900 <= y <= 2100: return y
    for m in re.finditer(r'(?<!\d)(20\d\d|19\d\d)(?!\d)', name):
        return int(m.group(1))
    for m in re.finditer(r'(?<!\d)\d{6}(?!\d)', name):
        s = m.group(); yy = int(s[4:])
        return 2000 + yy if yy <= 30 else 1900 + yy
    return None

# ── Doc type
def get_doc_type(name):
    n = name.lower()
    if re.search(r'cover note|cover letter', n):        return 'cover-note'
    if re.search(r'strategy memo|^memo|\bmemo\b', n):   return 'memo'
    if re.search(r'presentation deck|presentation', n): return 'presentation'
    if re.search(r'meeting notes', n):                  return 'meeting-notes'
    if re.search(r'investment narrative', n):           return 'investment-narrative'
    if re.search(r'investment plan', n):                return 'investment-plan'
    if re.search(r'inv scoring|investment scoring', n): return 'investment-scoring'
    if re.search(r'pre-read|pre read', n):              return 'pre-read'
    if re.search(r'table of contents|toc\b', n):        return 'table-of-contents'
    if re.search(r'participant bio|bios\b', n):         return 'participant-bios'
    if re.search(r'acronym list|acronym', n):           return 'acronym-list'
    if re.search(r'org chart', n):                      return 'org-chart'
    if re.search(r'follow.?up|action item', n):         return 'follow-ups'
    if re.search(r'appendix', n):                       return 'appendix'
    if re.search(r'digital binder|binder', n):          return 'digital-binder'
    if re.search(r'placemat', n):                       return 'placemat'
    if re.search(r'\.eml$|email', n):                   return 'email'
    if re.search(r'\.xlsx$|\.xls$', n):                 return 'spreadsheet'
    if re.search(r'\.mp4$|\.mov$', n):                  return 'video'
    return 'other'

# ── Meeting topic (strip date prefix and doc-type suffix)
SUFFIXES = [
    'Cover Note','Cover Letter','Strategy Memo','Memo','Presentation Deck','Presentation',
    'Meeting Notes','Investment Narrative','Investment Plan','Inv Scoring Top5-Bottom5',
    'Inv Scoring Summary','Investment Scoring','Table of Contents','Participant Bios',
    'Acronym List','Team Org Chart','Org Chart','Follow-Ups','Follow Ups','Action Items',
    'Pre-read','Appendix A','Appendix B','Appendix C','Appendix D','Appendix E',
    'Appendix F','Appendix G','Appendix H','Appendix','Digital Binder','Placemat',
    'Optional Appendices List','Optional Appendix','Bios','Email',
]
def get_meeting_topic(name):
    s = re.sub(r'\.\w+$', '', name)
    s = re.sub(r'^[\d_\-\. ]+', '', s)
    for suffix in SUFFIXES:
        s = re.sub(r'[\s_\-]*' + re.escape(suffix) + r'\s*$', '', s, flags=re.I)
    return s.strip(' -_')

# ── Strategy areas
def get_strategy_areas(fname, is_amb45=False):
    n = fname.lower()
    areas = []
    if re.search(r'k-12', n):                                                    areas.append('K-12')
    if re.search(r'postsecondary', n):                                           areas.append('Postsecondary')
    if re.search(r'pathway', n):                                                 areas.append('Pathways')
    if re.search(r'wsi|washington|charter', n):                                  areas.append('WSI-Charters')
    if re.search(r'usp.{0,4}data|data.{0,10}strategy|data.{0,10}discussion|joint.pathways', n): areas.append('USP-Data')
    if re.search(r'uspac|uspc|u\.s\.\s*policy', n):                              areas.append('USPAC')
    if is_amb45 and 'Amb45' not in areas:
        areas.append('Amb45')
    if not areas:
        if re.search(r'usp|u\.s\.\s*program', n):                               areas.append('General-USP')
    return areas or ['General-USP']

# ── Priority → legacy area (OOP removed from Priority 6)
PRIORITY_LEGACY = {
    'priority-1': ['K-12'],
    'priority-2': ['Postsecondary', 'Pathways'],
    'priority-3': ['Postsecondary', 'Pathways', 'WSI-Charters'],
    'priority-4': ['Postsecondary', 'Pathways'],
    'priority-5': ['USP-Data'],
    'priority-6': ['USPAC'],
    'priority-7': ['Cross-cutting'],
}

# ── Concept rules
CONCEPT_RULES = [
    # K-12
    (r'algebra.?1|algebra i\b',                                          'algebra-1-milestone'),
    (r'hqim|high.quality instructional|instructional material|curricula efficacy|high quality curriculum', 'HQIM'),
    (r'teacher prep|teacher professional|professional learning|teacher practice', 'teacher-professional-learning'),
    (r'math pathway|dana center|math course sequence',                   'math-pathways'),
    (r'modernizing math|reimagin.{0,20}math|redesign.{0,20}math',       'modernizing-math'),
    (r'ai.{0,10}tutor|tutoring\b|carnegie learning|zearn|khanmigo',     'AI-tutoring'),
    (r'product quality framework|pqf|courseware feature|feature map',   'product-quality-framework'),
    (r'coherent.{0,20}system|coherent instructional',                   'coherent-instructional-system'),
    (r'scaling hypothesis|theory of scale|path of least resistance',    'scaling-hypothesis'),
    (r'learning progression|learning science',                          'learning-science'),
    (r'formative assess|summative assess|\bassessment\b',               'assessment'),
    (r'network.{0,20}school improvement|\bnsi\b',                       'networks-school-improvement'),
    (r'illustrative math|im curriculum|open up resources|amplify|desmos|eureka math', 'HQIM-grantees'),
    (r'tntp|teacher preparation partner|teacher development',           'teacher-prep-grantees'),
    (r'mathematica|impact model',                                       'impact-modeling'),
    # Postsecondary
    (r'\bifs\b|institutional financial sustainability',                  'IFS'),
    (r'\bnse\b|national scale enterprise',                              'NSE'),
    (r'learnvia|gateway math course',                                   'learnvia-gateway-math'),
    (r'dhss|digital holistic|holistic student support',                 'DHSS'),
    (r'\budts\b|unified.{0,10}data.{0,10}transfer',                     'UDTS'),
    (r'pest.{0,10}framework|political.economic.social',                 'PEST-framework'),
    (r'postsecondary value|ps value|value commission|roi.{0,15}degree', 'PS-value'),
    (r'credential.{0,10}value|valued credential',                       'credential-of-value'),
    (r'completion rate|credential attainment|degree completion',        'credential-completion'),
    (r'\bsnhu\b|\basu\b|\bwgu\b|\bhbcu\b|\bmsi\b|\bhsi\b|\btcu\b',     'PS-institutions'),
    (r'lumen learning|courseware partner',                               'PS-courseware-grantees'),
    # Pathways
    (r'dual enrollment|dual credit|concurrent enrollment',              'dual-enrollment'),
    (r'momentum metric|momentum point|e-w momentum',                    'momentum-metrics'),
    (r'\bccmr\b|college career military ready',                         'CCMR'),
    (r'credit mobility|credit transfer|\bcmdt\b|credit mapping',       'credit-mobility-CMDT'),
    (r'aa by year 13|associate.{0,10}year 13',                          'AA-year-13'),
    (r'onegoal|college advising corps|near peer advising',              'advising-models'),
    (r'fafsa completion|fafsa filing',                                  'FAFSA-completion'),
    (r'11.{0,3}16 continuum|grades 11|high school to college',         '11-16-continuum'),
    (r'who am i|student identity|sense of belonging',                   'student-identity'),
    # WSI / Charters
    (r'levy equali|per.pupil funding gap|charter funding gap',          'levy-equalization'),
    (r'place.based|regional partnership|pierce county|tacoma',         'place-based-strategy'),
    (r'charter school|charter authoriz|charter quality',               'charter-schools'),
    (r'stakeholder engagement|community engagement',                    'stakeholder-engagement'),
    (r'theory of scale|wsi scale',                                      'WSI-theory-of-scale'),
    # USP Data
    (r'\bp20w\b|p-20w|longitudinal data system',                        'P20W'),
    (r'data privacy|ferpa|student privacy',                             'data-privacy'),
    (r'data ecosystem|data infrastructure|shared infrastructure',       'data-ecosystem'),
    (r'ai evaluation|evaluation technolog|ai benchmark',               'AI-evaluation-tech'),
    (r'knowledge graph',                                                'knowledge-graph'),
    (r'hyperscaler|microsoft.{0,20}education|google.{0,20}education',  'hyperscaler-partnerships'),
    (r'data.{0,5}ai.{0,5}hub|enablement hub',                          'data-AI-hub'),
    (r'portable memory|context specification|model context protocol',  'portable-memory'),
    (r'feedback loop|rapid feedback',                                   'feedback-loops'),
    (r'trusted evidence|evidence base|evidence ecosystem',             'evidence-ecosystem'),
    # USPAC
    (r'\bhea\b|higher education act|reauthori',                         'HEA-reauthorization'),
    (r'college transparency act|\bcta\b',                               'college-transparency-act'),
    (r'fafsa simplif',                                                  'FAFSA-simplification'),
    (r'state policy|state legislation|state budget',                    'state-policy'),
    (r'lamar alexander|patty murray|federal polic|congress\b|senate\b', 'federal-policy'),
    (r'communications strategy|public narrative|comms',                 'communications'),
    (r'advocacy coalition|coalition partner',                           'advocacy-coalitions'),
    # Amb'45
    (r'ambition 2045|amb.?45|ambition45',                               'Amb45-vision'),
    (r'priority 1|full stack.{0,20}instruct|core instruction.{0,20}tutor', 'priority-1'),
    (r'priority 2|gateway math course|learnvia',                        'priority-2'),
    (r'priority 3|personalized advising',                               'priority-3'),
    (r'priority 4|learning mobility|\bcmdt\b',                          'priority-4'),
    (r'priority 5|ai.{0,5}data infrastructure',                         'priority-5'),
    (r'priority 6|exemplar.{0,20}scal|scaling engine|public good.{0,20}strat', 'priority-6'),
    (r'priority 7|breakthrough innov',                                  'priority-7'),
    (r'moonshot goal|moonshot submission',                               'moonshot-goals'),
    (r'ladder of outcome|ew momentum point',                            'ladder-of-outcomes'),
    (r'delegate group|pillar.{0,5}delegate',                            'delegate-groups'),
    (r'ambition to action',                                             'ambition-to-action'),
    (r'walking up the mountain|toa.{0,10}backward',                    'TOA-methodology'),
    (r'guiding principle.{0,10}goal',                                   'guiding-principles'),
    # Cross-cutting
    (r'targeted universalism',                                          'targeted-universalism'),
    (r'systems change|systemic change|system.{0,10}transfor',          'systems-change'),
    (r'theory of change|\btoc\b|causal pathway',                       'theory-of-change'),
    (r'racial equity|equity gap|opportunity gap|achievement gap|black student|latino student|low.income student', 'racial-equity'),
    (r'mep.{0,10}framework|\bcmep\b|motivation.{0,10}engagement.{0,10}persist', 'MEP-framework'),
    (r'\bai\b|artificial intelligence|generative ai|large language model|\bllm\b', 'AI-technology'),
    (r'co.chair meeting|co-chair session|strategy review meeting',      'co-chair-meeting'),
    (r'strategy approval|investment narr|theory of action',             'strategy-approval'),
    (r'executive order|federal fund cut|title i.{0,10}cut|trump',      'political-context'),
    (r'financial sustainability.{0,10}school|sustain.{0,10}institution', 'institutional-sustainability'),
]

def get_concepts(text):
    t = text.lower()
    return [tag for pattern, tag in CONCEPT_RULES if re.search(pattern, t)]

# ── Load extracted text indexed by filename
print("Loading extracted text...")
doc_texts = {}

def load_docx_blocks(filepath):
    """Parse files with --- filename.docx --- delimiters."""
    with open(filepath, encoding='utf-8', errors='ignore') as f:
        content = f.read()
    # Find all delimiter positions
    delimiters = list(re.finditer(r'---\s*(.+?\.docx)\s*---', content))
    for i, m in enumerate(delimiters):
        fname = os.path.basename(m.group(1).strip())
        start = m.start()
        end = delimiters[i+1].start() if i+1 < len(delimiters) else len(content)
        doc_texts[fname] = content[start:end]

def load_pdf_blocks(filepath):
    """Parse files with FILE: filename headers (amb45 format)."""
    with open(filepath, encoding='utf-8', errors='ignore') as f:
        content = f.read()
    delimiters = list(re.finditer(r'FILE:\s*(.+)', content))
    for i, m in enumerate(delimiters):
        fname = os.path.basename(m.group(1).strip())
        start = m.start()
        end = delimiters[i+1].start() if i+1 < len(delimiters) else len(content)
        doc_texts[fname] = content[start:end]

if os.path.exists(EXTRACTED):
    load_docx_blocks(EXTRACTED)
if os.path.exists(AMB45_EXT):
    load_pdf_blocks(AMB45_EXT)

print(f"  Loaded text for {len(doc_texts)} documents")

# ── Tag all files
print("Tagging all files...")
with open(KB_FILE, encoding='utf-8') as f:
    all_paths = [l.strip() for l in f if l.strip()]

records = []
for path in all_paths:
    fname    = os.path.basename(path)
    is_amb45 = AMB45_BASE in path.replace('\\', '/')
    year     = get_year(fname)
    doc_type = get_doc_type(fname)
    topic    = get_meeting_topic(fname)
    areas    = get_strategy_areas(fname, is_amb45)
    text     = doc_texts.get(fname, fname + ' ' + topic)
    concepts = get_concepts(text)

    if is_amb45:
        if 'Amb45' not in areas:
            areas.insert(0, 'Amb45')
        priorities_found = [c for c in concepts if c.startswith('priority-')]
        if not priorities_found and re.search(r'overview|summary|all usp|compendium|q.?a|memo|guiding|update|strategy', fname.lower()):
            priorities_found = [f'priority-{i}' for i in range(1, 8)]
            concepts += [p for p in priorities_found if p not in concepts]
        for p in priorities_found:
            for legacy in PRIORITY_LEGACY.get(p, []):
                if legacy not in areas:
                    areas.append(legacy)

    records.append({
        'path':          path,
        'filename':      fname,
        'session_year':  year,
        'meeting_topic': topic,
        'strategy_areas': areas,
        'doc_type':      doc_type,
        'concepts':      concepts,
        'is_amb45':      is_amb45,
        'readable':      fname.lower().endswith('.docx'),
    })

# ── Write output
index = {'generated': str(date.today()), 'total': len(records), 'files': records}
with open(OUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(index, f, indent=2, ensure_ascii=False)

# ── Summary
area_counts    = Counter(a for r in records for a in r['strategy_areas'])
concept_counts = Counter(c for r in records for c in r['concepts'])
type_counts    = Counter(r['doc_type'] for r in records)

print(f"\nTagged {len(records)} files -> document_index.json\n")
print("By strategy area:")
for a, n in sorted(area_counts.items(), key=lambda x: -x[1]):
    print(f"  {a:<28} {n:>4}")
print("\nTop 25 concepts:")
for c, n in concept_counts.most_common(25):
    print(f"  {c:<38} {n:>4}")
print("\nBy doc type:")
for dt, n in sorted(type_counts.items(), key=lambda x: -x[1]):
    print(f"  {dt:<28} {n:>4}")
