from __future__ import annotations
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx


def bar_counts(df: pd.DataFrame, column: str, title: str, top_n: int = 20):
    if df.empty or column not in df.columns:
        return go.Figure()
    counts = df[column].value_counts().head(top_n).reset_index()
    counts.columns = [column, "count"]
    fig = px.bar(counts, x="count", y=column, orientation="h", title=title)
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=max(420, 24 * len(counts)))
    return fig


def timeline(df: pd.DataFrame):
    if df.empty or "year_num" not in df.columns:
        return go.Figure()
    d = df.dropna(subset=["year_num"]).copy()
    if d.empty:
        return go.Figure()
    c = d.groupby(["year_num", "focus_label"]).size().reset_index(name="count")
    fig = px.bar(c, x="year_num", y="count", color="focus_label", title="Publication timeline by metallurgy focus")
    fig.update_layout(xaxis_title="Year", yaxis_title="Records", height=430)
    return fig


def network_figure(df: pd.DataFrame, max_edges: int = 160):
    G = nx.Graph()
    for _, r in df.iterrows():
        title = str(r.get("title", ""))[:90]
        y = str(r.get("year", ""))
        paper = f"P: {title} ({y})"
        if not title:
            continue
        G.add_node(paper, kind="paper", size=4)
        for col, kind in [("alloy_systems", "alloy"), ("mechanisms", "mechanism"), ("methods", "method")]:
            for label in str(r.get(col, "")).split(";"):
                label = label.strip()
                if label:
                    node = f"{kind}: {label}"
                    G.add_node(node, kind=kind, size=10)
                    G.add_edge(paper, node)
    if G.number_of_edges() > max_edges:
        # keep most connected non-paper nodes and related paper edges
        non_papers = [n for n in G.nodes if not n.startswith("P: ")]
        keep = set(sorted(non_papers, key=lambda n: G.degree(n), reverse=True)[:45])
        for p in [n for n in G.nodes if n.startswith("P: ")]:
            if any(nb in keep for nb in G.neighbors(p)):
                keep.add(p)
        G = G.subgraph(keep).copy()
    if G.number_of_nodes() == 0:
        return go.Figure()
    pos = nx.spring_layout(G, k=0.55, iterations=60, seed=7)
    edge_x, edge_y = [], []
    for a, b in G.edges():
        x0, y0 = pos[a]
        x1, y1 = pos[b]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
    edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=0.5), hoverinfo="none", mode="lines")
    node_x, node_y, text, sizes = [], [], [], []
    for n in G.nodes():
        x, y = pos[n]
        node_x.append(x); node_y.append(y); text.append(n); sizes.append(8 + G.degree(n) * 1.5)
    node_trace = go.Scatter(x=node_x, y=node_y, mode="markers+text", text=[t.replace("mechanism: ", "M: ").replace("method: ", "Method: ").replace("alloy: ", "Alloy: ") for t in text], textposition="top center", hovertext=text, hoverinfo="text", marker=dict(size=sizes, line=dict(width=1)))
    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(title="Metallurgy knowledge graph: papers → alloys → mechanisms → methods", showlegend=False, height=720, margin=dict(l=10, r=10, t=60, b=10))
    fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
    return fig
