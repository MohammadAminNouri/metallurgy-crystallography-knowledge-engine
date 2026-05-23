
from pathlib import Path
import json, re
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
def load_taxonomy(path=ROOT/'data'/'metallurgy_taxonomy.json'):
    return json.loads(Path(path).read_text(encoding='utf-8'))
def normalize_text(text):
    return str(text or '').replace('–','-').replace('—','-').replace('‐','-').replace('‑','-')
def keyword_hits(text, keywords):
    t=normalize_text(text).lower(); hits=[]; score=0
    for kw in keywords:
        k=normalize_text(kw).strip(); kl=k.lower()
        if not kl: continue
        if len(kl)<=3 and kl.isalpha(): found=re.search(r'(?<![A-Za-z0-9])'+re.escape(kl)+r'(?![A-Za-z0-9])', t) is not None
        else: found=kl in t
        if found:
            hits.append(k); score += 2 if (' ' in k or '-' in k or '→' in k) else 1
    return score, sorted(set(hits), key=lambda x:(len(x),x))
def classify_record(record, taxonomy=None):
    taxonomy=taxonomy or load_taxonomy(); text=' '.join(str(record.get(k,'')) for k in ['title','abstract','venue','authors'])
    out={}; details={}
    for fam, labels in taxonomy.items():
        found=[]; fh={}
        for label,kws in labels.items():
            score,hits=keyword_hits(text,kws)
            if score>0: found.append(label); fh[label]=hits
        out[fam]=found; details[fam]=fh
    priority=[('mechanisms','martensitic transformations'),('mechanisms','twinning and weak twins'),('mechanisms','transformation matrices and symmetry'),('methods','additive manufacturing / LPBF process'),('mechanisms','precipitation and ordering'),('mechanisms','recrystallization and grain evolution'),('methods','EBSD / TKD orientation microscopy'),('mechanisms','mechanical behavior')]
    focus='general metallurgy / microstructure'
    for fam,lab in priority:
        if lab in out.get(fam,[]): focus=lab; break
    out['focus_label']=focus; out['hit_details']=details
    return out
def enrich_dataframe(df, taxonomy=None):
    taxonomy=taxonomy or load_taxonomy(); rows=[]
    for _,row in df.fillna('').iterrows():
        rec=row.to_dict(); cls=classify_record(rec,taxonomy); new=rec.copy()
        for k,v in cls.items(): new[k]=json.dumps(v, ensure_ascii=False) if k=='hit_details' else ('; '.join(v) if isinstance(v,list) else v)
        rows.append(new)
    out=pd.DataFrame(rows)
    if 'year' in out.columns: out['year_num']=pd.to_numeric(out['year'], errors='coerce')
    return out
def explode_labels(df,column):
    if df.empty or column not in df.columns: return pd.DataFrame(columns=[column,'record_id','title'])
    x=df[['record_id','title',column]].copy(); x[column]=x[column].fillna('').astype(str).str.split(';'); x=x.explode(column); x[column]=x[column].astype(str).str.strip(); return x[x[column]!='']
def coverage_counts(df, columns):
    rows=[]
    for col in columns:
        ex=explode_labels(df,col)
        if ex.empty: continue
        counts=ex[col].value_counts().reset_index(); counts.columns=['label','count']; counts.insert(0,'family',col); rows.append(counts)
    return pd.concat(rows,ignore_index=True) if rows else pd.DataFrame(columns=['family','label','count'])
