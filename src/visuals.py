
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
def timeline(df):
    if df.empty or 'year_num' not in df.columns: return go.Figure()
    d=df.dropna(subset=['year_num']).copy()
    if d.empty: return go.Figure()
    c=d.groupby(['year_num','focus_label']).size().reset_index(name='count')
    fig=px.bar(c,x='year_num',y='count',color='focus_label',title='Publication timeline by metallurgy focus'); fig.update_layout(xaxis_title='Year',yaxis_title='Records in current corpus',legend_title='Focus'); return fig
def count_bar(df,column,title,top_n=20):
    rows=[]
    if df.empty or column not in df.columns: return go.Figure()
    for vals in df[column].fillna('').astype(str):
        for v in vals.split(';'):
            v=v.strip()
            if v: rows.append(v)
    if not rows: return go.Figure()
    counts=pd.Series(rows).value_counts().head(top_n).sort_values().reset_index(); counts.columns=[column,'count']
    fig=px.bar(counts,x='count',y=column,orientation='h',title=title); fig.update_layout(height=max(400,26*len(counts)),yaxis_title=''); return fig
def heatmap_pairs(pair_df,x,y,title):
    if pair_df.empty: return go.Figure()
    pivot=pair_df.pivot_table(index=y,columns=x,values='count',fill_value=0)
    fig=px.imshow(pivot,text_auto=True,aspect='auto',title=title); fig.update_layout(height=max(450,26*len(pivot.index))); return fig
def network_figure(df,max_papers=80):
    if df.empty: return go.Figure()
    G=nx.Graph()
    for _,row in df.head(max_papers).iterrows():
        paper=str(row.get('record_id',''))+': '+str(row.get('title',''))[:65]; G.add_node(paper,kind='paper')
        for fam in ['alloy_systems','mechanisms','methods']:
            for label in str(row.get(fam,'')).split(';'):
                label=label.strip()
                if label: G.add_node(label,kind=fam); G.add_edge(paper,label)
    if len(G)==0: return go.Figure()
    pos=nx.spring_layout(G,seed=7,k=0.55); edge_x=[]; edge_y=[]
    for a,b in G.edges(): edge_x += [pos[a][0],pos[b][0],None]; edge_y += [pos[a][1],pos[b][1],None]
    traces=[go.Scatter(x=edge_x,y=edge_y,mode='lines',line=dict(width=0.5),hoverinfo='none')]
    for kind in ['paper','alloy_systems','mechanisms','methods']:
        nodes=[n for n,data in G.nodes(data=True) if data.get('kind')==kind]
        if nodes: traces.append(go.Scatter(x=[pos[n][0] for n in nodes],y=[pos[n][1] for n in nodes],mode='markers+text',name=kind,text=[n if kind!='paper' else '' for n in nodes],hovertext=nodes,hoverinfo='text',textposition='top center',marker=dict(size=7 if kind=='paper' else 13)))
    fig=go.Figure(data=traces); fig.update_layout(title='Corpus knowledge graph: papers ↔ alloys/methods/mechanisms',showlegend=True,height=720,xaxis=dict(visible=False),yaxis=dict(visible=False)); return fig
