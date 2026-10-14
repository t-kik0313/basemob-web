from webapp.presentation import page_route, screen_response
from webapp import app
from webapp.data import load_merged_data

@page_route('/record_summary')
def record_summary():
    merged = load_merged_data()
    records = merged.to_dict(orient='records') if not merged.empty else []
    return screen_response('record_summary.html', records=records)
