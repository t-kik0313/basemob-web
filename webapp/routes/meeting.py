from flask import render_template
from webapp import app
from webapp.data import load_merged_data

@app.route('/record_summary')
def record_summary():
    merged = load_merged_data()
    records = merged.to_dict(orient='records') if not merged.empty else []
    return render_template('record_summary.html', records=records)
