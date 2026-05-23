
import io, re
import pandas as pd
PUB_TYPES={"Article","Preprint","Presentation","Poster","Conference Paper","Book","Chapter","Question"}
MONTHS=r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|June|July|August|September|October|November|December)"
DATE_RE=re.compile(rf"^(?:{MONTHS}\s+)?(?:19|20)\d{{2}}$"); YEAR_RE=re.compile(r"(19|20)\d{2}")
NOISE_PREFIXES=('Fig.','Figure','Table','SEM ','Typical ','Chemical ','SPS ','Optical ','EBSD ','Pole ','Lattices ','Unit cell','Pseudocode','Projections','Examples','Directional','Hyperplanar','Similarities','Schematic','Phase diagram','a)','b)','c)','d)','Micrograph','FESEM','TEMPERATURE','Full-text','View','Published:','Current ','Top ','Join ','Network','Cited','About','Home','Questions','Answers','App Store','Get it','Company','Terms','Discover','Recruit','ResearchGate Logo','Search for','Contact','Skills','Education','Additional affiliations','Position','Field of study','Publications','Introduction','Reads','Citations','Network','Cited By','View All')
VENUE_HINTS=['Acta','Materials','Scripta','Journal','Crystals','Metals','Nature','Geology','Earth','Philosophical','Microscopy','SSRN','Advanced','Energy','Applied','Crystal','Results','Additive','Material']
def clean_line(s): return re.sub(r'\s+',' ',str(s).strip().replace('\ufeff',''))
def is_noise(s): return (not s) or s in {'View','Show All','Full-text available','Publications (230)','Publications'} or len(s)<3 or s.startswith(NOISE_PREFIXES) or s.startswith('©')
def looks_author(s): return ('Cyril Cayron' in s or '[...]' in s or re.search(r'[A-Z][a-z]+ [A-Z][a-z]+',s)) and len(s)<240 and not any(v in s for v in ['Acta','Journal','Materials','Scripta'])
def looks_venue(s): return len(s)<=100 and any(h in s for h in VENUE_HINTS)
def parse_copied_publication_text(text):
    lines=[clean_line(x) for x in str(text).splitlines()]; lines=[x for x in lines if x]; anchors=[i for i,l in enumerate(lines) if l in PUB_TYPES]
    recs=[]; seen=set()
    for k,i in enumerate(anchors):
        t=i-1
        while t>=0 and (is_noise(lines[t]) or lines[t] in PUB_TYPES or DATE_RE.match(lines[t])): t-=1
        if t<0: continue
        title=lines[t]
        if is_noise(title) or title in seen or len(title)<8 or title.startswith('Cyril Cayron') or title.startswith('Swiss Federal'): continue
        next_i=anchors[k+1] if k+1<len(anchors) else len(lines)
        if k+1<len(anchors):
            nt=anchors[k+1]-1
            while nt>i and (is_noise(lines[nt]) or lines[nt] in PUB_TYPES or DATE_RE.match(lines[nt])): nt-=1
            block=lines[i+1:max(i+1,nt)]
        else: block=lines[i+1:next_i]
        pos=0
        while pos<len(block) and is_noise(block[pos]): pos+=1
        date=year=venue=authors=''
        if pos<len(block) and DATE_RE.match(block[pos]): date=block[pos]; m=YEAR_RE.search(date); year=m.group(0) if m else ''; pos+=1
        if pos<len(block) and looks_venue(block[pos]) and not looks_author(block[pos]): venue=block[pos]; pos+=1
        if pos<len(block) and not DATE_RE.match(block[pos]) and not looks_venue(block[pos]) and (looks_author(block[pos]) or 'Cyril' in block[pos] or '[...]' in block[pos]): authors=block[pos]; pos+=1
        abstract=' '.join([b for b in block[pos:] if (not is_noise(b)) and (not DATE_RE.match(b)) and b not in PUB_TYPES and len(b)>25])[:1800]
        if not year:
            m=YEAR_RE.search(' '.join([date,title,abstract])); year=m.group(0) if m else ''
        seen.add(title); recs.append({'title':title,'publication_type':lines[i],'date':date,'year':year,'venue':venue,'authors':authors,'abstract':abstract,'source':'pasted text import','full_text_available':any('Full-text available' in x for x in lines[i:next_i])})
    for idx,r in enumerate(recs,1): r['record_id']=f'IMP-{idx:03d}'
    return pd.DataFrame(recs)
def read_publication_csv(uploaded_file):
    df=pd.read_csv(io.BytesIO(uploaded_file.read())); df=df.rename(columns={c:c.strip().lower().replace(' ','_') for c in df.columns})
    if 'title' not in df.columns:
        for c in ['publication_title','name','document_title']:
            if c in df.columns: df=df.rename(columns={c:'title'}); break
    for col in ['year','authors','venue','abstract','source','publication_type']:
        if col not in df.columns: df[col]=''
    if 'record_id' not in df.columns: df['record_id']=[f'CSV-{i:03d}' for i in range(1,len(df)+1)]
    return df
