import plotly.graph_objects as go
import pandas as pd
import json

# Neon color palette
NEON = {
    'cyan':    '#00f5ff',
    'lime':    '#c8ff00',
    'pink':    '#ff2d78',
    'purple':  '#bf5af2',
    'orange':  '#ff9f0a',
    'blue':    '#0a84ff',
    'green':   '#30d158',
    'yellow':  '#ffd60a',
    'teal':    '#5ac8fa',
    'red':     '#ff453a',
    'indigo':  '#7d5fff',
    'mint':    '#00e5cc',
}

CHANNEL_COLORS = [
    NEON['cyan'], NEON['lime'], NEON['purple'], NEON['pink'],
    NEON['orange'], NEON['blue'], NEON['teal'], NEON['yellow'],
    NEON['mint'], NEON['indigo'],
]

def _roas_color(roas):
    if roas is None: return NEON['red']
    roas = float(roas)
    if roas >= 10: return NEON['cyan']
    if roas >= 4:  return NEON['lime']
    if roas >= 2:  return NEON['orange']
    if roas >= 1:  return NEON['yellow']
    return NEON['red']

def _cac_color(cac):
    if cac is None: return NEON['red']
    cac = float(cac)
    if cac < 100:  return NEON['cyan']
    if cac < 200:  return NEON['lime']
    if cac < 500:  return NEON['orange']
    return NEON['red']

def _ltv_color(ltv):
    if ltv is None: return NEON['red']
    ltv = float(ltv)
    if ltv >= 5:  return NEON['cyan']
    if ltv >= 3:  return NEON['lime']
    if ltv >= 1:  return NEON['orange']
    return NEON['red']

def _fig_to_json(fig) -> dict:
    return json.loads(fig.to_json())

def _dark_layout(title: str, height: int = 380) -> dict:
    return dict(
        title=dict(
            text=title,
            font=dict(color='#ffffff', size=15, family='Inter,sans-serif'),
            x=0.02,
            y=0.96
        ),
        autosize=True,
        paper_bgcolor='#0d0d18',
        plot_bgcolor='#0d0d18',
        font=dict(color='#aaaacc', family='Inter,sans-serif', size=12),
        margin=dict(l=110, r=70, t=55, b=45),
        legend=dict(
            bgcolor='#0d0d18',
            font=dict(color='#aaaacc', size=11),
            bordercolor='#1e1e3a',
            borderwidth=1,
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        xaxis=dict(
            automargin=True,
            gridcolor='#1e1e3a',
            zerolinecolor='#1e1e3a',
            tickfont=dict(size=12, color='#aaaacc'),
        ),
        yaxis=dict(
            automargin=True,
            gridcolor='#1e1e3a',
            zerolinecolor='#1e1e3a',
            tickfont=dict(size=12, color='#ffffff'),
        ),
        height=height,
        hoverlabel=dict(
            bgcolor='#1e1e3a',
            bordercolor='#00f5ff',
            font=dict(color='#ffffff', size=12)
        )
    )

def chart_roas(metrics: list) -> dict:
    df = pd.DataFrame(metrics)
    df = df[~df['origin'].isin(['unknown'])].dropna(subset=['ROAS'])
    df = df.sort_values('ROAS', ascending=True)
    colors = [_roas_color(r) for r in df['ROAS']]

    fig = go.Figure(go.Bar(
        x=df['ROAS'], y=df['origin'],
        orientation='h',
        marker=dict(color=colors, line=dict(color='#0d0d18', width=1)),
        text=[f"<b>{r:.1f}x</b>" for r in df['ROAS']],
        textposition='outside',
        textfont=dict(size=11, color='#ffffff'),
        cliponaxis=False,
        hovertemplate='<b>%{y}</b><br>ROAS: <b>%{x:.2f}x</b><extra></extra>'
    ))
    fig.add_vline(
        x=4, line_dash='dash', line_color=NEON['cyan'] + '60', line_width=1.5,
        annotation_text='Benchmark 4x',
        annotation_font=dict(color=NEON['cyan'], size=10),
        annotation_position='top right'
    )
    layout = _dark_layout('ROAS by Channel', height=380)
    layout['margin'] = dict(l=120, r=70, t=55, b=45)
    layout['xaxis']['title'] = dict(text='Return on Ad Spend (ROAS)', font=dict(color='#aaaacc', size=11))
    fig.update_layout(**layout)
    return _fig_to_json(fig)

def chart_cac(metrics: list) -> dict:
    df = pd.DataFrame(metrics)
    df = df[~df['origin'].isin(['unknown'])].dropna(subset=['CAC'])
    df = df.sort_values('CAC', ascending=False)
    colors = [_cac_color(c) for c in df['CAC']]

    fig = go.Figure(go.Bar(
        x=df['CAC'], y=df['origin'],
        orientation='h',
        marker=dict(color=colors, line=dict(color='#0d0d18', width=1)),
        text=[f"<b>${c:,.0f}</b>" for c in df['CAC']],
        textposition='outside',
        textfont=dict(size=11, color='#ffffff'),
        cliponaxis=False,
        hovertemplate='<b>%{y}</b><br>CAC: <b>$%{x:,.0f}</b><extra></extra>'
    ))
    fig.add_vline(
        x=200, line_dash='dash', line_color=NEON['orange'] + '60', line_width=1.5,
        annotation_text='Benchmark $200',
        annotation_font=dict(color=NEON['orange'], size=10),
        annotation_position='top right'
    )
    layout = _dark_layout('CAC by Channel — Lower is Better', height=380)
    layout['margin'] = dict(l=120, r=80, t=55, b=45)
    layout['xaxis']['title'] = dict(text='Customer Acquisition Cost ($)', font=dict(color='#aaaacc', size=11))
    fig.update_layout(**layout)
    return _fig_to_json(fig)

def chart_spend_vs_revenue(metrics: list) -> dict:
    df = pd.DataFrame(metrics)
    df = df[~df['origin'].isin(['unknown'])].sort_values('total_revenue', ascending=False)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Ad Spend', x=df['origin'], y=df['assumed_spend'],
        marker=dict(color=NEON['indigo'], opacity=0.85),
        text=[f"<b>${v/1000:.0f}K</b>" for v in df['assumed_spend']],
        textposition='outside',
        textfont=dict(size=10, color=NEON['indigo']),
        cliponaxis=False,
        hovertemplate='<b>%{x}</b><br>Spend: <b>$%{y:,.0f}</b><extra></extra>'
    ))
    fig.add_trace(go.Bar(
        name='Revenue',
        x=df['origin'],
        y=df['total_revenue'],
        marker=dict(color=[_roas_color(r) for r in df['ROAS']], opacity=0.9),
        text=[f"<b>${v/1000:.0f}K</b>" for v in df['total_revenue']],
        textposition='outside',
        textfont=dict(size=10, color='#ffffff'),
        cliponaxis=False,
        hovertemplate='<b>%{x}</b><br>Revenue: <b>$%{y:,.0f}</b><extra></extra>'
    ))
    layout = _dark_layout('Spend vs Revenue by Channel', height=380)
    layout['barmode'] = 'group'
    layout['margin'] = dict(l=60, r=30, t=55, b=75)
    layout['xaxis']['tickangle'] = -25
    layout['yaxis']['title'] = dict(text='Amount ($)', font=dict(color='#aaaacc', size=11))
    fig.update_layout(**layout)
    return _fig_to_json(fig)

def chart_ltv_cac(metrics: list) -> dict:
    df = pd.DataFrame(metrics).dropna(subset=['LTV_CAC'])
    df = df[~df['origin'].isin(['unknown'])].sort_values('LTV_CAC', ascending=True)
    colors = [_ltv_color(l) for l in df['LTV_CAC']]

    fig = go.Figure(go.Bar(
        x=df['LTV_CAC'], y=df['origin'],
        orientation='h',
        marker=dict(color=colors, line=dict(color='#0d0d18', width=1)),
        text=[f"<b>{l:.2f}x</b>" for l in df['LTV_CAC']],
        textposition='outside',
        textfont=dict(size=11, color='#ffffff'),
        cliponaxis=False,
        hovertemplate='<b>%{y}</b><br>LTV/CAC: <b>%{x:.2f}x</b><extra></extra>'
    ))
    fig.add_vline(
        x=3, line_dash='dash', line_color=NEON['lime'] + '70', line_width=1.5,
        annotation_text='Healthy: 3x',
        annotation_font=dict(color=NEON['lime'], size=10),
        annotation_position='top right'
    )
    layout = _dark_layout('LTV / CAC Ratio by Channel', height=380)
    layout['margin'] = dict(l=120, r=80, t=55, b=45)
    layout['xaxis']['title'] = dict(text='LTV / CAC Ratio', font=dict(color='#aaaacc', size=11))
    fig.update_layout(**layout)
    return _fig_to_json(fig)

def chart_conversion_rate(metrics: list) -> dict:
    df = pd.DataFrame(metrics)
    df = df[~df['origin'].isin(['unknown'])].sort_values('conversion_rate', ascending=False)

    fig = go.Figure(go.Bar(
        x=df['origin'],
        y=df['conversion_rate'],
        marker=dict(
            color=CHANNEL_COLORS[:len(df)],
            line=dict(color='#0d0d18', width=1)
        ),
        text=[f"<b>{c:.1f}%</b>" for c in df['conversion_rate']],
        textposition='outside',
        textfont=dict(size=11, color='#ffffff'),
        cliponaxis=False,
        hovertemplate='<b>%{x}</b><br>Conv Rate: <b>%{y:.2f}%</b><extra></extra>'
    ))
    layout = _dark_layout('Conversion Rate by Channel', height=380)
    layout['margin'] = dict(l=60, r=30, t=55, b=75)
    layout['xaxis']['tickangle'] = -25
    layout['yaxis']['title'] = dict(text='Conversion Rate (%)', font=dict(color='#aaaacc', size=11))
    fig.update_layout(**layout)
    return _fig_to_json(fig)

def chart_budget_recommendation(budget: list) -> dict:
    df = pd.DataFrame(budget)
    df = df[~df['origin'].isin(['unknown'])].sort_values('recommended_spend', ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Current Spend',
        x=df['assumed_spend'], y=df['origin'],
        orientation='h',
        marker=dict(color=NEON['indigo'], opacity=0.5),
        text=[f"<b>${v/1000:.0f}K</b>" for v in df['assumed_spend']],
        textposition='inside',
        textfont=dict(size=10, color='#ffffff'),
        cliponaxis=False,
        hovertemplate='<b>%{y}</b><br>Current: <b>$%{x:,.0f}</b><extra></extra>'
    ))
    fig.add_trace(go.Bar(
        name='Recommended',
        x=df['recommended_spend'], y=df['origin'],
        orientation='h',
        marker=dict(
            color=[NEON['cyan'] if c > 0 else NEON['red'] for c in df['budget_change']],
            opacity=0.9
        ),
        text=[f"<b>${v/1000:.0f}K</b>" for v in df['recommended_spend']],
        textposition='outside',
        textfont=dict(size=10, color='#ffffff'),
        cliponaxis=False,
        hovertemplate='<b>%{y}</b><br>Recommended: <b>$%{x:,.0f}</b><extra></extra>'
    ))
    layout = _dark_layout('Budget Reallocation — Current vs Recommended', height=380)
    layout['barmode'] = 'group'
    layout['margin'] = dict(l=120, r=80, t=55, b=45)
    layout['xaxis']['title'] = dict(text='Budget ($)', font=dict(color='#aaaacc', size=11))
    fig.update_layout(**layout)
    return _fig_to_json(fig)

def chart_channel_efficiency(metrics: list) -> dict:
    """Bubble scatter: ROAS (x) vs LTV/CAC (y), bubble size = revenue."""
    df = pd.DataFrame(metrics)
    df = df[~df['origin'].isin(['unknown'])].dropna(subset=['ROAS'])
    df = df[df['ROAS'] > 0].copy()
    if df.empty:
        return {}

    df['LTV_CAC'] = df['LTV_CAC'].fillna(0).clip(lower=0.01)
    df['total_revenue'] = df['total_revenue'].fillna(0)

    rev_min = df['total_revenue'].min()
    rev_max = df['total_revenue'].max()
    rev_range = rev_max - rev_min if rev_max > rev_min else 1
    df['bubble_size'] = 12 + 28 * ((df['total_revenue'] - rev_min) / rev_range)

    colors = [_roas_color(r) for r in df['ROAS']]

    positions = ['top center', 'bottom center', 'top right', 'bottom left',
                 'top left', 'bottom right', 'middle right', 'middle left']
    text_pos = [positions[i % len(positions)] for i in range(len(df))]

    fig = go.Figure(go.Scatter(
        x=df['ROAS'],
        y=df['LTV_CAC'],
        mode='markers+text',
        marker=dict(
            size=df['bubble_size'],
            color=colors,
            line=dict(color='#0d0d18', width=1.5),
            opacity=0.85,
        ),
        text=df['origin'],
        textposition=text_pos,
        textfont=dict(size=10, color='#ffffff'),
        cliponaxis=False,
        hovertemplate=(
            '<b>%{text}</b><br>'
            'ROAS: <b>%{x:.2f}x</b><br>'
            'LTV/CAC: <b>%{y:.2f}x</b><br>'
            'Revenue: <b>$%{customdata:,.0f}</b>'
            '<extra></extra>'
        ),
        customdata=df['total_revenue'],
    ))

    fig.add_hline(y=3, line_dash='dot', line_color=NEON['lime'] + '50', line_width=1,
                  annotation_text='LTV/CAC = 3x', annotation_position='top left',
                  annotation_font=dict(color=NEON['lime'], size=9))
    fig.add_vline(x=4, line_dash='dot', line_color=NEON['cyan'] + '50', line_width=1,
                  annotation_text='ROAS = 4x', annotation_position='top right',
                  annotation_font=dict(color=NEON['cyan'], size=9))

    layout = _dark_layout('Channel Efficiency Map', height=380)
    layout['xaxis']['title'] = dict(text='ROAS (log scale)', font=dict(color='#aaaacc', size=11))
    layout['yaxis']['title'] = dict(text='LTV / CAC (log scale)', font=dict(color='#aaaacc', size=11))
    layout['xaxis']['type'] = 'log'
    layout['yaxis']['type'] = 'log'
    layout['xaxis']['dtick'] = None
    layout['yaxis']['dtick'] = None
    layout['margin'] = dict(l=70, r=40, t=55, b=60)
    fig.update_layout(**layout)
    return _fig_to_json(fig)

def chart_roas_donut(metrics: list) -> dict:
    df = pd.DataFrame(metrics)
    df = df[~df['origin'].isin(['unknown','other'])].dropna(subset=['ROAS'])
    df = df[df['ROAS'] > 0].sort_values('ROAS', ascending=False)

    fig = go.Figure(go.Pie(
        labels=df['origin'],
        values=df['ROAS'],
        hole=0.65,
        marker=dict(
            colors=CHANNEL_COLORS[:len(df)],
            line=dict(color='#0d0d18', width=2)
        ),
        textfont=dict(size=11, color='#ffffff'),
        hovertemplate='<b>%{label}</b><br>ROAS: <b>%{value:.1f}x</b><br>Share: <b>%{percent}</b><extra></extra>'
    ))
    fig.update_layout(**_dark_layout('ROAS Share by Channel'))
    fig.update_layout(
        annotations=[dict(
            text='<b>ROAS</b>',
            x=0.5, y=0.5,
            font=dict(size=16, color='#ffffff'),
            showarrow=False
        )]
    )
    return _fig_to_json(fig)

def generate_all_charts(results: dict) -> dict:
    metrics = results['metrics']
    budget  = results['budget']
    return {
        'roas':          chart_roas(metrics),
        'cac':           chart_cac(metrics),
        'spend_revenue': chart_spend_vs_revenue(metrics),
        'ltv_cac':       chart_ltv_cac(metrics),
        'conversion':    chart_conversion_rate(metrics),
        'budget':        chart_budget_recommendation(budget),
        'cohort':        chart_channel_efficiency(metrics),
        'roas_donut':    chart_roas_donut(metrics),
    }
