import os
import json
import pandas as pd
import numpy as np
from django.conf import settings
from django.shortcuts import render
from django.utils.timezone import now

UPLOAD_DIR = os.path.join(settings.MEDIA_ROOT, 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

def dashboard_home(request):
    context = {'segment': 'dashboard_home'}
    uploaded_filename = None

    # Handle file upload
    if request.method == 'POST' and request.FILES.get('excel_file'):
        uploaded_file = request.FILES['excel_file']
        timestamp = now().strftime('%Y%m%d%H%M%S')
        filename = f"delivery_{timestamp}_{uploaded_file.name}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, 'wb+') as dest:
            for chunk in uploaded_file.chunks():
                dest.write(chunk)

        request.session['last_uploaded'] = file_path
        request.session['uploaded_filename'] = uploaded_file.name

    # Get last uploaded file
    file_path = request.session.get('last_uploaded')
    uploaded_filename = request.session.get('uploaded_filename')

    if not file_path or not os.path.exists(file_path):
        context['error'] = "No file found. Please upload a valid CSV file."
        return render(request, 'dashboard/dashboard.html', context)

    # Load CSV
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        context['error'] = f"Error reading file: {str(e)}"
        return render(request, 'dashboard/dashboard.html', context)

    # Clean column names
    df.columns = [col.strip() for col in df.columns]

    # Identify key columns dynamically
    def find_column(possibilities):
        for col in df.columns:
            if col.strip().lower() in possibilities:
                return col
        return None

    delivery_status_col = find_column({'delivery status'})
    client_status_col = find_column({'client status'})
    ra_name_col = find_column({'ra name'})
    asset_title_col = find_column({'asset title'})
    feedback_col = find_column({'client feedback'})
    delivery_date_col = find_column({'delivery date'})

    # Basic metrics
    total = len(df)
    delivered = df[df[delivery_status_col].str.lower() == 'delivered'].shape[0] if delivery_status_col else 0
    accepted = df[df[client_status_col].str.lower() == 'accepted'].shape[0] if client_status_col else 0
    rejected = total - accepted

    metrics = {
        'total_leads': total,
        'delivered': delivered,
        'accepted': accepted,
        'rejected': rejected,
    }

    # Helper for JSON-safe data
    def to_serializable(d):
        return {str(k): int(v) if isinstance(v, (np.integer, np.int64)) else v for k, v in d.items()}

    # Charts
    status_distribution = to_serializable(
        df[client_status_col].value_counts().to_dict()) if client_status_col else {}

    assets_vs_leads = to_serializable(
        df[asset_title_col].value_counts().to_dict()) if asset_title_col else {}

    ra_performance = to_serializable(
        df[df[client_status_col].str.lower() == 'accepted'][ra_name_col].value_counts().to_dict()
    ) if ra_name_col and client_status_col else {}

    # Trend: Delivery Date over time
    trend_data = {}
    if delivery_date_col:
        df[delivery_date_col] = pd.to_datetime(df[delivery_date_col], errors='coerce')
        df = df.dropna(subset=[delivery_date_col])
        trend_series = df[delivery_date_col].dt.date.value_counts().sort_index()
        trend_data = {str(date): int(count) for date, count in trend_series.items()}

    # Rejection feedback
    rejection_labels, rejection_values = [], []
    if client_status_col and feedback_col:
        rejected_df = df[df[client_status_col].str.lower() != 'accepted']
        feedback_counts = rejected_df[feedback_col].value_counts()
        rejection_labels = [str(label) for label in feedback_counts.index.tolist()]
        rejection_values = [int(val) for val in feedback_counts.values.tolist()]

    charts = {
        "status_distribution": json.dumps(status_distribution),
        "assets_vs_leads": json.dumps(assets_vs_leads),
        "ra_performance": json.dumps(ra_performance),
        "campaign_trend": json.dumps(trend_data),
    }

    context.update({
        "metrics": metrics,
        "charts": charts,
        "uploaded_filename": uploaded_filename,
        "rejection_labels": json.dumps(rejection_labels),
        "rejection_values": json.dumps(rejection_values),

    })

    return render(request, 'dashboard/dashboard.html', context)
