import pandas as pd
import numpy as np
import math

SPEND_MAP = {
    'organic_search': 5000,
    'paid_search': 50000,
    'social': 40000,
    'email': 10000,
    'direct_traffic': 2000,
    'referral': 3000,
    'display': 20000,
    'other_publicities': 1000,
    'other': 500,
    'unknown': 0
}

def safe_float(val, default=0.0):
    try:
        f = float(val)
        return default if (math.isnan(f) or math.isinf(f)) else f
    except:
        return default

def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.select_dtypes(include=[np.floating]).columns:
        df[col] = df[col].apply(lambda x: None if (x is not None and (math.isnan(x) or math.isinf(x))) else x)
    return df

def load_olist_files(files: dict) -> dict:
    dfs = {}
    for name, fileobj in files.items():
        try:
            dfs[name] = pd.read_csv(fileobj)
        except Exception as e:
            raise ValueError(f"Could not read {name}: {str(e)}")
    return dfs

def validate_files(dfs: dict) -> list:
    required = ['orders', 'items', 'payments', 'customers', 'mql', 'deals']
    return [r for r in required if r not in dfs]

def parse_dates(orders: pd.DataFrame) -> pd.DataFrame:
    orders = orders.copy()
    orders['order_purchase_timestamp'] = pd.to_datetime(
        orders['order_purchase_timestamp'], errors='coerce'
    )
    return orders

def build_channel_pipeline(dfs: dict) -> pd.DataFrame:
    orders    = parse_dates(dfs['orders'])
    items     = dfs['items']
    payments  = dfs['payments']
    customers = dfs['customers']
    mql       = dfs['mql']
    deals     = dfs['deals']

    delivered = orders[orders['order_status'] == 'delivered'].copy()

    channel_seller = mql.merge(
        deals[['mql_id', 'seller_id']], on='mql_id', how='inner'
    )[['seller_id', 'origin']].dropna()

    seller_orders = items[['order_id', 'seller_id', 'price']].merge(
        channel_seller, on='seller_id', how='inner'
    )

    pipeline = seller_orders.merge(
        payments[['order_id', 'payment_value']], on='order_id', how='left'
    )
    pipeline = pipeline.merge(
        delivered[['order_id', 'order_purchase_timestamp', 'customer_id']],
        on='order_id', how='inner'
    )
    pipeline = pipeline.merge(
        customers[['customer_id', 'customer_unique_id']], on='customer_id', how='left'
    )

    pipeline['payment_value'] = pipeline['payment_value'].fillna(0)
    return pipeline

def compute_channel_metrics(pipeline: pd.DataFrame, mql: pd.DataFrame,
                             deals: pd.DataFrame) -> pd.DataFrame:
    revenue = pipeline.groupby('origin').agg(
        total_revenue  = ('payment_value', 'sum'),
        total_orders   = ('order_id',      'nunique'),
        unique_sellers = ('seller_id',     'nunique')
    ).reset_index()

    conv = mql.merge(deals[['mql_id', 'seller_id']], on='mql_id', how='left')
    conv['converted'] = conv['seller_id'].notna().astype(int)

    conv_summary = conv.groupby('origin').agg(
        total_leads     = ('mql_id',    'count'),
        converted_leads = ('converted', 'sum')
    ).reset_index()

    conv_summary['conversion_rate'] = (
        conv_summary['converted_leads'] / conv_summary['total_leads'].replace(0, np.nan) * 100
    ).fillna(0).round(2)

    metrics = revenue.merge(conv_summary, on='origin', how='outer')
    metrics['assumed_spend']   = metrics['origin'].map(SPEND_MAP).fillna(0)
    metrics['total_revenue']   = metrics['total_revenue'].fillna(0)
    metrics['converted_leads'] = metrics['converted_leads'].fillna(0)
    metrics['total_leads']     = metrics['total_leads'].fillna(0)

    metrics['CAC'] = np.where(
        metrics['converted_leads'] > 0,
        (metrics['assumed_spend'] / metrics['converted_leads']).round(2),
        None
    )

    metrics['ROAS'] = np.where(
        metrics['assumed_spend'] > 0,
        (metrics['total_revenue'] / metrics['assumed_spend']).round(2),
        None
    )

    metrics = metrics[~metrics['origin'].isin(['unknown'])].copy()
    metrics = metrics.sort_values('ROAS', ascending=False, na_position='last').reset_index(drop=True)

    return clean_df(metrics)

def compute_ltv(pipeline: pd.DataFrame) -> pd.DataFrame:
    pipeline = pipeline.copy()
    pipeline['purchase_month'] = pd.to_datetime(
        pipeline['order_purchase_timestamp']
    ).dt.to_period('M')

    cohort = pipeline.groupby('customer_unique_id')['purchase_month'].min().reset_index()
    cohort.columns = ['customer_unique_id', 'cohort_month']
    pipeline = pipeline.merge(cohort, on='customer_unique_id', how='left')

    pipeline['months_since_first'] = (
        pipeline['purchase_month'] - pipeline['cohort_month']
    ).apply(lambda x: x.n if hasattr(x, 'n') else 0)

    customer_stats = pipeline.groupby('customer_unique_id').agg(
        total_revenue  = ('payment_value', 'sum'),
        total_orders   = ('order_id',      'nunique'),
        first_purchase = ('purchase_month','min'),
        last_purchase  = ('purchase_month','max')
    ).reset_index()

    customer_stats['lifespan_months'] = (
        customer_stats['last_purchase'] - customer_stats['first_purchase']
    ).apply(lambda x: max(x.n, 1) if hasattr(x, 'n') else 1)

    customer_stats['avg_order_value'] = (
        customer_stats['total_revenue'] / customer_stats['total_orders'].replace(0, 1)
    )
    customer_stats['purchase_frequency'] = (
        customer_stats['total_orders'] / customer_stats['lifespan_months'].replace(0, 1)
    )
    customer_stats['LTV'] = (
        customer_stats['avg_order_value'] *
        customer_stats['purchase_frequency'] *
        customer_stats['lifespan_months']
    )

    customer_stats['LTV'] = customer_stats['LTV'].fillna(0)
    return customer_stats

def compute_ltv_per_channel(pipeline: pd.DataFrame,
                             metrics: pd.DataFrame) -> pd.DataFrame:
    ltv_ch = pipeline.groupby('origin')['payment_value'].agg(
        ['sum', 'mean', 'count']
    ).reset_index()
    ltv_ch.columns = ['origin', 'total_revenue', 'avg_order_value', 'total_orders']

    cac_map = dict(zip(metrics['origin'], metrics['CAC']))
    ltv_ch['CAC'] = ltv_ch['origin'].map(cac_map)

    ltv_ch['LTV_CAC'] = np.where(
        ltv_ch['CAC'].notna() & (ltv_ch['CAC'] > 0),
        (ltv_ch['avg_order_value'] / ltv_ch['CAC']).round(2),
        None
    )

    return clean_df(ltv_ch.sort_values('LTV_CAC', ascending=False, na_position='last'))

def compute_cohort_matrix(pipeline: pd.DataFrame) -> pd.DataFrame:
    pipeline = pipeline.copy()
    pipeline['purchase_month'] = pd.to_datetime(
        pipeline['order_purchase_timestamp']
    ).dt.to_period('M')

    cohort = pipeline.groupby('customer_unique_id')['purchase_month'].min().reset_index()
    cohort.columns = ['customer_unique_id', 'cohort_month']
    pipeline = pipeline.merge(cohort, on='customer_unique_id', how='left')

    pipeline['months_since_first'] = (
        pipeline['purchase_month'] - pipeline['cohort_month']
    ).apply(lambda x: x.n if hasattr(x, 'n') else 0)

    cohort_matrix = pipeline.groupby(
        ['cohort_month', 'months_since_first']
    )['payment_value'].sum().reset_index()

    pivot = cohort_matrix.pivot(
        index='cohort_month', columns='months_since_first', values='payment_value'
    ).fillna(0)

    pivot.index = pivot.index.astype(str)
    pivot.columns = pivot.columns.astype(str)

    return pivot.iloc[:, :12]

def compute_budget_recommendation(metrics: pd.DataFrame) -> pd.DataFrame:
    df = metrics.copy()
    df = df[df['assumed_spend'] > 0].copy()

    df['roas_safe']    = df['ROAS'].fillna(0)
    df['ltv_cac_safe'] = df['LTV_CAC'].fillna(0) if 'LTV_CAC' in df.columns else 0
    df['score']        = df['roas_safe'] * df['ltv_cac_safe']

    total        = df['score'].sum()
    total_budget = df['assumed_spend'].sum()

    df['score_normalized']  = (df['score'] / total).fillna(0) if total > 0 else 0
    df['recommended_spend'] = (df['score_normalized'] * total_budget).round(0)
    df['budget_change']     = df['recommended_spend'] - df['assumed_spend']
    df['change_pct']        = np.where(
        df['assumed_spend'] > 0,
        ((df['budget_change'] / df['assumed_spend']) * 100).round(1),
        0
    )

    def action(row):
        c = row['budget_change']
        if c > 5000:   return 'Scale Up'
        if c >= 0:     return 'Maintain'
        if c > -10000: return 'Reduce'
        return 'Cut'

    df['action'] = df.apply(action, axis=1)
    df = df.drop(columns=['roas_safe','ltv_cac_safe','score','score_normalized'], errors='ignore')

    return clean_df(df.sort_values('recommended_spend', ascending=False))

def run_full_analysis(dfs: dict) -> dict:
    pipeline = build_channel_pipeline(dfs)
    metrics  = compute_channel_metrics(pipeline, dfs['mql'], dfs['deals'])
    ltv_ch   = compute_ltv_per_channel(pipeline, metrics)

    metrics  = metrics.merge(
        ltv_ch[['origin', 'LTV_CAC', 'avg_order_value']], on='origin', how='left'
    )
    metrics  = clean_df(metrics)

    budget   = compute_budget_recommendation(metrics)
    cohort   = compute_cohort_matrix(pipeline)
    ltv_dist = compute_ltv(pipeline)

    best_idx  = metrics['ROAS'].idxmax() if metrics['ROAS'].notna().any() else 0
    worst_idx = metrics['ROAS'].idxmin() if metrics['ROAS'].notna().any() else 0

    overview = {
        'total_revenue':   safe_float(pipeline['payment_value'].sum()),
        'total_orders':    int(pipeline['order_id'].nunique()),
        'total_spend':     int(sum(SPEND_MAP.values())),
        'total_leads':     int(len(dfs['mql'])),
        'total_converted': int(len(dfs['deals'])),
        'best_roas':       safe_float(metrics.loc[best_idx, 'ROAS']),
        'best_channel':    str(metrics.loc[best_idx, 'origin']),
        'worst_channel':   str(metrics.loc[worst_idx, 'origin']),
        'avg_ltv':         safe_float(ltv_dist['LTV'].mean()),
    }

    return {
        'overview': overview,
        'metrics':  metrics.to_dict(orient='records'),
        'budget':   budget.to_dict(orient='records'),
        'cohort':   cohort.to_dict(),
        'ltv_dist': {
            'mean':   safe_float(ltv_dist['LTV'].mean()),
            'median': safe_float(ltv_dist['LTV'].median()),
            'max':    safe_float(ltv_dist['LTV'].max()),
        }
    }