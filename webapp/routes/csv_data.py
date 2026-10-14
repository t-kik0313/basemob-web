import glob
import os

import pandas as pd
from flask import redirect, url_for

from webapp import app
from webapp.config import BASE_DIR


def _csv_tables():
    tables = []
    for path in sorted(glob.glob(os.path.join(BASE_DIR, '*.csv'))):
        name = os.path.basename(path)
        try:
            frame = pd.read_csv(path, encoding='utf-8-sig', dtype=str, keep_default_na=False)
        except Exception as error:
            tables.append({'name': name, 'columns': [], 'rows': [], 'error': str(error)})
            continue
        tables.append({
            'name': name,
            'columns': list(frame.columns),
            'rows': frame.to_dict(orient='records'),
            'error': '',
        })
    return tables


@app.route('/csv_data')
def csv_data():
    return redirect(url_for('players'))
