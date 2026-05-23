
from pathlib import Path
import json
import pandas as pd
import numpy as np
import streamlit as st
from src.parser import parse_copied_publication_text, read_publication_csv
from src.taxonomy import load_taxonomy, enrich_dataframe, coverage_counts
from src.visuals import timeline, count_bar, heatmap_pairs, network_figure
from src.gaps import gap_cards, theme_pair_matrix
from src.crystallography import parse_matrix, matrix_to_markdown, cubic_symmetry_operators, generate_variants, misorientation, axis_angle_from_rotation, rotation_matrix_from_axis_angle
ROOT=Path(__file__).resolve().parent; DATA=ROOT/'data'/'publications_context.csv'; RAW=ROOT/'data'/'uploaded_context_raw.txt'; REGISTRY=ROOT/'data'/'source_registry.json'
st.set_page_config(page_title='Metallurgy Crystallography Knowledge Engine', page_icon='🧬', layout='wide')
st.title('🧬 Metallurgy Crystallography Knowledge Engine')
st.caption('Publication-corpus intelligence for metallurgy: alloys, transformations, EBSD/TKD methods, crystallography, processing–microstructure–property links, and future research gaps.')
@st.cache_data(show_spinner=False)
def load_seed(): return pd.read_csv(DATA).fillna('')
@st.cache_data(show_spinner=False)
def enrich(df): return enrich_dataframe(df, load_taxonomy()).fillna('')
seed=load_seed()
with st.sidebar:
    st.header('Corpus input'); st.write('Seed corpus is parsed from the uploaded context text.')
    uploaded_csv=st.file_uploader('Optional: upload publication CSV', type=['csv'])
    pasted=st.text_area('Optional: paste additional publication-profile text', height=180)
    use_seed=st.checkbox('Use seed context corpus', value=True)
    st.divider(); st.markdown('**Important**'); st.caption('This app does not scrape ResearchGate, Scholar, or institutional pages. Paste/export records and import them here.')
frames=[]
if use_seed: frames.append(seed)
if uploaded_csv is not None:
    try: frames.append(read_publication_csv(uploaded_csv))
    except Exception as e: st.sidebar.error(f'CSV import failed: {e}')
if pasted.strip(): frames.append(parse_copied_publication_text(pasted))
if not frames: st.warning('Load seed corpus or import text/CSV to begin.'); st.stop()
raw_df=pd.concat(frames, ignore_index=True)
if 'title' not in raw_df.columns: st.error('No title column found in the loaded corpus.'); st.stop()
raw_df=raw_df.drop_duplicates(subset=['title']).reset_index(drop=True)
if 'record_id' not in raw_df.columns: raw_df['record_id']=[f'REC-{i:03d}' for i in range(1,len(raw_df)+1)]
df=enrich(raw_df)
with st.sidebar:
    st.header('Filters'); q=st.text_input('Search title/abstract/venue')
    years=sorted([int(y) for y in pd.to_numeric(df.get('year',pd.Series(dtype=str)), errors='coerce').dropna().unique()])
    year_range=st.slider('Year range', min_value=min(years), max_value=max(years), value=(min(years),max(years))) if years else None
    focus_sel=st.multiselect('Focus labels', sorted([x for x in df['focus_label'].dropna().unique() if x]))
fdf=df.copy()
if q: fdf=fdf[fdf.apply(lambda row: q.lower() in ' '.join(map(str,row.values)).lower(), axis=1)]
if year_range and 'year_num' in fdf.columns: fdf=fdf[(fdf['year_num'].isna())|((fdf['year_num']>=year_range[0])&(fdf['year_num']<=year_range[1]))]
if focus_sel: fdf=fdf[fdf['focus_label'].isin(focus_sel)]
c1,c2,c3,c4,c5=st.columns(5)
c1.metric('Records loaded', len(df)); c2.metric('After filters', len(fdf))
c3.metric('Years covered', f"{int(df['year_num'].min()) if 'year_num' in df and df['year_num'].notna().any() else '—'}–{int(df['year_num'].max()) if 'year_num' in df and df['year_num'].notna().any() else '—'}")
c4.metric('Full-text flags', int(df.get('full_text_available',pd.Series(dtype=bool)).astype(str).str.lower().isin(['true','1','yes']).sum()))
c5.metric('Unique focus labels', df['focus_label'].nunique() if 'focus_label' in df else 0)
st.info('Coverage note: the seed dataset covers all publication-like entries visible in the uploaded context text. The original profile header may mention a larger total, so import additional EPFL/Scholar/ResearchGate exports to extend the corpus.')
tabs=st.tabs(['Overview','Publication Explorer','Knowledge Graph','Theme Matrix','Research Gap Engine','NiTi Variant Gap','Crystallography Lab','Data Export'])
with tabs[0]:
    st.subheader('Metallurgy-first overview'); st.plotly_chart(timeline(fdf), use_container_width=True)
    a,b=st.columns(2)
    with a: st.plotly_chart(count_bar(fdf,'alloy_systems','Alloy systems in current corpus'), use_container_width=True); st.plotly_chart(count_bar(fdf,'methods','Methods and processing tools'), use_container_width=True)
    with b: st.plotly_chart(count_bar(fdf,'mechanisms','Metallurgical mechanisms'), use_container_width=True); st.plotly_chart(count_bar(fdf,'properties','Property / response links'), use_container_width=True)
    with st.expander('Coverage table'): st.dataframe(coverage_counts(fdf,['alloy_systems','mechanisms','methods','properties']), use_container_width=True, hide_index=True)
with tabs[1]:
    st.subheader('Publication Explorer'); show=['record_id','year','publication_type','title','venue','focus_label','alloy_systems','mechanisms','methods','properties','abstract']; show=[c for c in show if c in fdf.columns]
    st.dataframe(fdf[show], use_container_width=True, hide_index=True, height=620); st.download_button('Download filtered enriched corpus CSV', fdf.to_csv(index=False).encode('utf-8'), 'enriched_filtered_corpus.csv', 'text/csv')
with tabs[2]:
    st.subheader('Knowledge Graph'); st.caption('Papers are connected to detected alloy systems, mechanisms, and methods. Use filters/sidebar to reduce the graph.')
    limit=st.slider('Max papers in graph', 20, 160, 80, step=10); st.plotly_chart(network_figure(fdf, max_papers=limit), use_container_width=True)
with tabs[3]:
    st.subheader('Theme Matrix'); col_a,col_b=st.columns(2)
    with col_a: left=st.selectbox('Rows/theme A', ['alloy_systems','mechanisms','methods','properties'], index=0)
    with col_b: right=st.selectbox('Columns/theme B', ['mechanisms','methods','properties','alloy_systems'], index=0)
    pairs=theme_pair_matrix(fdf,left,right); st.plotly_chart(heatmap_pairs(pairs.head(80),x=left,y=right,title=f'{left} × {right} co-occurrence'), use_container_width=True); st.dataframe(pairs, use_container_width=True, hide_index=True)
with tabs[4]:
    st.subheader('Research Gap Engine'); st.caption('Gap cards are generated from repeated corpus ingredients. Future-extension cards must not be presented as already completed work.')
    for card in gap_cards(df):
        with st.expander(f"{card['title']} · coverage score {card['coverage_score']}/5", expanded=card['title'].startswith('Process-aware NiTi')):
            st.markdown(f"**Status:** {card['status']}"); st.markdown(f"**Confidence:** {card['confidence']}"); st.markdown('**Logic**'); st.write(card['logic'])
            st.markdown('**Evidence counts in current corpus**'); st.dataframe(pd.DataFrame([{'knowledge_block':k,'count':v} for k,v in card['evidence_counts'].items()]), use_container_width=True, hide_index=True)
            A,B,C=st.columns(3)
            with A: st.markdown('**Research questions**'); [st.write('• '+x) for x in card['research_questions']]
            with B: st.markdown('**Data needed**'); [st.write('• '+x) for x in card['data_needed']]
            with C: st.markdown('**Possible outputs**'); [st.write('• '+x) for x in card['possible_outputs']]
            with st.expander('Risk flags / interpretation limits'):
                for x in card['risk_flags']: st.warning(x)
with tabs[5]:
    st.subheader('Deep layer: Process-aware NiTi martensite variant-mapping framework')
    st.markdown('''This page explains the main future gap in layers. It is a proposed extension, not a direct claim that the corpus already contains a completed LPBF-NiTi variant-map study.

**Core chain:**

```text
LPBF / process history
    → thermal gradient, cooling rate, melt-pool geometry
    → B2 parent grain structure and texture
    → B19′ martensite variant selection
    → EBSD/TKD variant map
    → texture-memory relation
    → superelastic or shape-memory response
```
''')
    layer_tabs=st.tabs(['Foundation','Missing combination','Scientific questions','Data architecture','Software outputs','Risks'])
    with layer_tabs[0]: st.markdown('''**Existing foundation in the corpus:**
- NiTi shape-memory alloys
- B2→B19′ martensitic transformation
- EBSD/TKD orientation microscopy
- martensite variants and reorientation
- texture evolution
- transformation matrices and correspondence theory
- LPBF/additive manufacturing metallurgy in metallic alloys
- process-driven microstructure control''')
    with layer_tabs[1]: st.markdown('''**Underdeveloped combined problem:**

```text
LPBF process parameters
    → B2 parent-grain morphology/texture
    → B19′ product-variant distribution
    → local crystallographic memory
    → mechanical/functional response
```

The novelty is not simply printing NiTi. The metallurgy novelty is making the transformation-variant structure measurable, reconstructable, and linkable to processing.''')
    with layer_tabs[2]:
        for qx in ['Can LPBF thermal history be used to design the crystallographic variant structure of NiTi martensite?','Does melt-pool geometry bias B2 parent grain orientation?','Does parent B2 texture control B19′ variant selection?','Can EBSD/TKD reconstruct the parent B2 grains from B19′ martensite?','Are certain B19′ variant pairs favored by LPBF thermal gradients?','Does variant distribution correlate with recoverable strain or superelastic behavior?','Can correspondence theory predict observed variant families?','Can post-processing heat treatment erase or preserve LPBF-induced variant memory?']: st.write('• '+qx)
    with layer_tabs[3]: st.code('''sample_id
process: laser_power, scan_speed, hatch_spacing, layer_thickness, scan_strategy
thermal: cooling_rate_proxy, melt_pool_width, thermal_gradient_direction
microstructure: phase_map, grain_size, boundary_map, porosity, precipitates
crystallography: B2_parent_orientation, B19_variant_label, OR_fit_error, misorientation_pair
mechanical: transformation_stress, superelastic_strain, hysteresis, residual_strain
heat_treatment: anneal_temp, anneal_time, aging_temp, transformation_temperatures''')
    with layer_tabs[4]:
        for o in ['B2 parent reconstruction map','B19′ martensite variant map','Variant-family census','Variant-pair misorientation histogram','Packet/domain graph','Texture-memory map','Scan-vector vs variant-selection plot','Melt-pool boundary vs variant-distribution plot','Process → microstructure → property Sankey diagram','Superelasticity prediction dashboard']: st.write('• '+o)
    with layer_tabs[5]:
        for r in ['EBSD indexing of B19′ martensite can be difficult.','NiTi surface preparation is demanding.','LPBF can introduce residual stress, porosity, and composition shifts.','B2 parent reconstruction from B19′ may be non-unique.','Multiple orientation relationships may fit the same data.','Variant assignment depends strongly on the assumed correspondence theory.','Mechanical response depends on porosity, precipitates, texture, and residual stress, not only variants.']: st.warning(r)
with tabs[6]:
    st.subheader('Crystallography Lab'); st.caption('Transparent helper calculations for orientation/misorientation and simplified variant exploration. Validate before publication use.')
    lab_tabs=st.tabs(['Misorientation','Axis-angle rotation','Variant generator'])
    with lab_tabs[0]:
        st.markdown('Paste two 3×3 orientation matrices. Cubic symmetry reduction is optional.'); a,b=st.columns(2)
        with a: m1=st.text_area('Matrix g1','1 0 0\n0 1 0\n0 0 1',key='m1')
        with b: m2=st.text_area('Matrix g2','0 -1 0\n1 0 0\n0 0 1',key='m2')
        use_cubic=st.checkbox('Use cubic symmetry reduction', value=True)
        if st.button('Calculate misorientation'):
            try:
                G1,G2=parse_matrix(m1),parse_matrix(m2); sym=cubic_symmetry_operators() if use_cubic else [np.eye(3)]; angle,axis=misorientation(G1,G2,sym); st.success(f'Minimum misorientation angle: {angle:.4f}°'); st.write(f'Axis: [{axis[0]:.4f}, {axis[1]:.4f}, {axis[2]:.4f}]')
            except Exception as e: st.error(str(e))
    with lab_tabs[1]:
        axis=st.text_input('Axis x,y,z','0,0,1'); angle=st.number_input('Angle in degrees', value=90.0)
        try:
            ax=[float(x) for x in axis.replace(',',' ').split()]; R=rotation_matrix_from_axis_angle(ax, angle); st.markdown(matrix_to_markdown(R)); aa,aa_axis=axis_angle_from_rotation(R); st.write(f'Check: {aa:.4f}° about [{aa_axis[0]:.4f}, {aa_axis[1]:.4f}, {aa_axis[2]:.4f}]')
        except Exception as e: st.error(str(e))
    with lab_tabs[2]:
        st.markdown('Simplified parent-symmetry variant enumeration from a supplied orientation-relationship matrix.'); orm=st.text_area('Orientation relationship matrix','1 0 0\n0 1 0\n0 0 1',key='orm'); maxv=st.slider('Max variants to show',1,48,24)
        if st.button('Generate variants'):
            try:
                OR=parse_matrix(orm); variants=generate_variants(OR,parent_sym=cubic_symmetry_operators(),max_variants=maxv); st.write(f'Generated {len(variants)} unique simplified variants.'); rows=[]
                for i,V in enumerate(variants,1): angle,axis=axis_angle_from_rotation(V); rows.append({'variant':i,'angle_deg':round(angle,4),'axis':f'[{axis[0]:.3f},{axis[1]:.3f},{axis[2]:.3f}]'})
                st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
            except Exception as e: st.error(str(e))
with tabs[7]:
    st.subheader('Data Export and Source Notes'); st.download_button('Download full enriched corpus CSV', df.to_csv(index=False).encode('utf-8'), 'full_enriched_corpus.csv', 'text/csv'); st.download_button('Download filtered enriched corpus CSV', fdf.to_csv(index=False).encode('utf-8'), 'filtered_enriched_corpus.csv', 'text/csv')
    if REGISTRY.exists(): st.markdown('### Source registry'); st.json(json.loads(REGISTRY.read_text(encoding='utf-8')))
    with st.expander('Raw uploaded context text preview'):
        if RAW.exists(): st.text(RAW.read_text(encoding='utf-8')[:5000])
