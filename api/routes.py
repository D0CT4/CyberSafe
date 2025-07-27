from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import random

bp = Blueprint('dashboard', __name__)

@bp.route('/api/dashboard-data')
def dashboard_data():
    # Generate sample data (replace with real data from your system)
    today = datetime.now()
    dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
    
    data = {
        'dates': dates,
        'totalEvents': random.randint(1000, 5000),
        'activeModels': random.randint(1, 3),
        'errorRate': round(random.uniform(0.1, 2.0), 2),
        'events': [random.randint(50, 200) for _ in dates],
        'errors': [random.randint(0, 10) for _ in dates],
        'responseTimes': [random.randint(100, 500) for _ in dates],
        'recentEvents': [
            {
                'time': (today - timedelta(minutes=i*5)).strftime('%H:%M:%S'),
                'type': random.choice(['INFO', 'WARNING', 'ERROR']),
                'message': f"Sample event message {i+1}",
                'status': random.choice(['success', 'warning', 'danger'])
            } for i in range(10)
        ]
    }
    
    return jsonify(data)
