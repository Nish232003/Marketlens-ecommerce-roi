import os
import sys
import io
import traceback
import math
import json

# Ensure backend directory is always in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
try:
    import anthropic
except ImportError:
    anthropic = None

from analysis import load_olist_files, validate_files, run_full_analysis
from charts import generate_all_charts

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend')

app = Flask(__name__)
CORS(app, origins="*")

def clean_nan(obj):
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_nan(i) for i in obj]
    return obj

FILE_MAP = {
    'orders.csv':     'orders',
    'items.csv':      'items',
    'payments.csv':   'payments',
    'customers.csv':  'customers',
    'products.csv':   'products',
    'sellers.csv':    'sellers',
    'reviews.csv':    'reviews',
    'mql.csv':        'mql',
    'deals.csv':      'deals',
}

REQUIRED = ['orders', 'items', 'payments', 'customers', 'mql', 'deals']

@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/dashboard')
def serve_dashboard():
    return send_from_directory(FRONTEND_DIR, 'dashboard.html')

DATA_RAW_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'raw')
DEMO_CACHE = None

@app.route('/demo', methods=['GET', 'POST'])
def demo():
    global DEMO_CACHE
    try:
        if DEMO_CACHE is not None:
            return jsonify(DEMO_CACHE)

        raw_files = {
            'orders':    os.path.join(DATA_RAW_DIR, 'olist_orders_dataset.csv'),
            'items':     os.path.join(DATA_RAW_DIR, 'olist_order_items_dataset.csv'),
            'payments':  os.path.join(DATA_RAW_DIR, 'olist_order_payments_dataset.csv'),
            'customers': os.path.join(DATA_RAW_DIR, 'olist_customers_dataset.csv'),
            'mql':       os.path.join(DATA_RAW_DIR, 'olist_marketing_qualified_leads_dataset.csv'),
            'deals':     os.path.join(DATA_RAW_DIR, 'olist_closed_deals_dataset.csv'),
        }

        import pandas as pd
        dfs = {k: pd.read_csv(p) for k, p in raw_files.items()}

        results = run_full_analysis(dfs)
        charts  = generate_all_charts(results)

        response = clean_nan({
            'success':  True,
            'overview': results['overview'],
            'metrics':  results['metrics'],
            'budget':   results['budget'],
            'ltv_dist': results['ltv_dist'],
            'charts':   charts,
        })
        DEMO_CACHE = response
        return jsonify(response)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Failed to load demo dataset: {str(e)}'}), 500

@app.route('/analyse', methods=['POST'])
def analyse():
    try:
        uploaded = request.files
        if not uploaded:
            return jsonify({'error': 'No files uploaded'}), 400

        dfs = {}
        unrecognized = []

        for filename, fileobj in uploaded.items():
            fname = fileobj.filename
            key = FILE_MAP.get(fname)
            if key:
                content = fileobj.read()
                dfs[key] = io.StringIO(content.decode('utf-8'))
            else:
                unrecognized.append(fname)

        missing = [r for r in REQUIRED if r not in dfs]
        if missing:
            return jsonify({
                'error': f'Missing required files: {missing}',
                'hint': 'Upload all required CSVs: orders, items, payments, customers, mql, deals'
            }), 400

        raw_dfs = load_olist_files(dfs)
        results = run_full_analysis(raw_dfs)
        charts  = generate_all_charts(results)

        response = clean_nan({
            'success':  True,
            'overview': results['overview'],
            'metrics':  results['metrics'],
            'budget':   results['budget'],
            'ltv_dist': results['ltv_dist'],
            'charts':   charts,
        })
        return jsonify(response)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        body = request.get_json()
        api_key  = body.get('api_key', '')
        messages = body.get('messages', [])
        context  = body.get('context', {})

        if not api_key or not api_key.startswith('sk-ant-'):
            return jsonify({'error': 'Invalid Anthropic API key'}), 401

        if not messages:
            return jsonify({'error': 'No messages provided'}), 400

        overview = context.get('overview', {})
        metrics  = context.get('metrics', [])

        metrics_text = '\n'.join([
            f"- {m.get('origin','?')}: spend R${m.get('assumed_spend',0):,.0f}, "
            f"revenue R${m.get('total_revenue',0):,.0f}, "
            f"CAC R${m.get('CAC',0):,.0f}, ROAS {m.get('ROAS',0):.2f}x, "
            f"LTV/CAC {m.get('LTV_CAC',0):.2f}x, "
            f"conv {m.get('conversion_rate',0):.1f}%"
            for m in metrics if m.get('origin') != 'unknown'
        ])

        system_prompt = f"""You are MarketLens AI, a sharp senior marketing analyst.

You have analysed the user's uploaded marketing data. Here are the results:

OVERVIEW:
- Total Revenue: R${overview.get('total_revenue', 0):,.0f}
- Total Orders: {overview.get('total_orders', 0):,}
- Total Spend: R${overview.get('total_spend', 0):,.0f}
- Total Leads: {overview.get('total_leads', 0):,}
- Total Converted: {overview.get('total_converted', 0):,}
- Best ROAS: {overview.get('best_roas', 0):.2f}x ({overview.get('best_channel','?')})
- Avg LTV: R${overview.get('avg_ltv', 0):,.0f}

CHANNEL METRICS:
{metrics_text}

BENCHMARKS:
- Healthy LTV/CAC: > 3x
- Good ROAS: > 4x
- Efficient CAC: < R$200

YOUR ROLE:
- Give sharp, data-driven answers with exact numbers from the analysis
- Use bullet points for clarity
- Be concise — max 150 words
- Flag risks clearly with specific figures
- Respond in the same language the user writes in"""

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model='claude-sonnet-4-6',
            max_tokens=1000,
            system=system_prompt,
            messages=messages
        )

        return jsonify({
            'reply': response.content[0].text,
            'usage': {
                'input_tokens':  response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens,
            }
        })

    except anthropic.AuthenticationError:
        return jsonify({'error': 'Invalid API key — check your Anthropic key'}), 401
    except anthropic.RateLimitError:
        return jsonify({'error': 'Rate limit hit — wait a moment and retry'}), 429
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)