import os
import pandas as pd
import matplotlib
from django.shortcuts import render
from django.http import HttpResponse,JsonResponse
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from weasyprint import HTML
import logging
from django import template
import matplotlib.pyplot as plt
from django.conf import settings
import json
from django.views.decorators.csrf import csrf_exempt
import requests
from django.http import JsonResponse



# Set up logging
logger = logging.getLogger(__name__)

matplotlib.use('Agg')


# Set the upload folder and ensure it exists
UPLOAD_FOLDER = os.path.join(settings.MEDIA_ROOT, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)



register = template.Library()

@login_required(login_url="/login/")
def reports_option(request):
    """Render the main reports page."""
    context = {
        'segment': 'reports_option',
    }
    return render(request, 'reports/reports_option.html', context)

@login_required(login_url="/login/")
def upload_form(request):
    """Render the upload form page."""
    return render(request, 'reports/upload.html')

@login_required(login_url="/login/")
def submit_report(request):
    """Handle CSV file uploads and generate reports."""
    try:
        if request.method == "POST":
            if 'file' not in request.FILES:
                return HttpResponse('No file part', status=400)

            file = request.FILES['file']

            if not file.name.endswith('.csv'):
                return HttpResponse('The uploaded file is not a CSV.', status=400)

            filepath = os.path.join(UPLOAD_FOLDER, file.name)
            with open(filepath, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

            try:
                df = pd.read_csv(filepath)
            except Exception as e:
                logger.error(f"Error reading CSV file: {str(e)} - File: {file.name}")
                return HttpResponse(f"Error reading CSV file: {str(e)}", status=400)

            # Generate the reports and analyses
            image_paths = generate_reports(df)
            analyses = get_report_analysis(df)

            # Pass image paths and analysis results to the template
            return render(request, 'reports/report.html', {
                'filename': file.name,
                'analyses': analyses,
                'image_paths': image_paths,
            })

        return HttpResponse('Invalid request method.', status=405)

    except Exception as e:
        logger.error(f"Error in submit_report: {str(e)} - User: {request.user.username}")
        return HttpResponse(f"Internal server error: {str(e)}", status=500)

def generate_reports(df):
    """Generate visual reports from the CSV data and save as images."""
    report_folder = os.path.join(settings.MEDIA_ROOT, 'uploads', 'reports')
    os.makedirs(report_folder, exist_ok=True)

    # Image paths
    allocation_vs_pacing_path = os.path.join(report_folder, 'allocation_vs_pacing.png')
    asset_promotion_split_path = os.path.join(report_folder, 'asset_promotion_split.png')
    geo_vs_asset_promotions_path = os.path.join(report_folder, 'geo_vs_asset_promotions.png')
    asset_allocation_path = os.path.join(report_folder, 'asset_allocation.png')
    industry_distribution_path = os.path.join(report_folder, 'industry_distribution.png')

    # 1. Allocation vs Pacing (Bar Chart)
    plt.figure(figsize=(10, 6))
    bar_width = 0.35
    index = range(len(df['date']))

    allocated = df['allocated_resources']
    actual = df['actual_resources']

    plt.bar(index, allocated, bar_width, label='Allocated Resources', color='blue')
    plt.bar([i + bar_width for i in index], actual, bar_width, label='Actual Resources', color='orange')

    plt.xlabel('Date')
    plt.ylabel('Resources')
    plt.title('Allocation vs Pacing')
    plt.xticks([i + bar_width / 2 for i in index], df['date'], rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig(allocation_vs_pacing_path)
    plt.close()

    # 2. Asset Promotion Split
    df['asset_split'] = df['actual_resources'] / 10  # Assuming 1 Campaign == 10 Assets
    plt.figure(figsize=(10, 6))
    plt.bar(df['asset_title'], df['asset_split'], color='blue')
    plt.xlabel('Asset Title')
    plt.ylabel('Promoted Assets')
    plt.title('Asset Promotion Split')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(asset_promotion_split_path)
    plt.close()

    # 3. Geo vs Asset Promotions (Stacked Bar Chart)
    geo_asset = df.groupby(['country', 'asset_title']).size().unstack(fill_value=0)
    geo_asset.plot(kind='bar', stacked=True)
    plt.title('Geo vs Asset Promotions')
    plt.xlabel('Country')
    plt.ylabel('Number of Promotions')
    plt.tight_layout()
    plt.savefig(geo_vs_asset_promotions_path)
    plt.close()

    # 4. Asset Allocation Bar Chart
    plt.figure(figsize=(10, 6))
    plt.bar(df['asset_title'], df['allocated_resources'], color='green')
    plt.xlabel('Asset Title')
    plt.ylabel('Allocated Resources')
    plt.title('Asset Allocation')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(asset_allocation_path)
    plt.close()

    # 5. Pie Chart for Industry Distribution
    industry_distribution = df['industry'].value_counts()
    plt.figure(figsize=(8, 8))
    plt.pie(industry_distribution, labels=industry_distribution.index, autopct='%1.1f%%', startangle=140)
    plt.title('Industry Distribution')
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig(industry_distribution_path)
    plt.close()

    # Return the image paths for use in the template
    return [
        'uploads/reports/allocation_vs_pacing.png',
        'uploads/reports/asset_promotion_split.png',
        'uploads/reports/geo_vs_asset_promotions.png',
        'uploads/reports/asset_allocation.png',
        'uploads/reports/industry_distribution.png'
    ]

def get_report_analysis(df):
    """Generate textual analysis based on the data in the CSV."""
    analyses = {}

    # Allocation vs Pacing
    allocated_avg = df['allocated_resources'].mean()
    actual_avg = df['actual_resources'].mean()
    allocation_gap = allocated_avg - actual_avg
    analyses['allocation_vs_pacing'] = (
        f"On average, {allocated_avg:.2f} resources were allocated, while {actual_avg:.2f} were used. "
        f"This shows a gap of {allocation_gap:.2f} resources." if allocation_gap > 0 else
        f"Resources were utilized optimally with no significant gap."
    )

    # Asset Promotion Split
    max_promotion = df['asset_split'].max()
    analyses['asset_promotion_split'] = (
        f"Promotions were evenly distributed with a maximum promotion of {max_promotion:.2f} per asset."
    )

    # Geo vs Asset Promotions
    top_geo = df.groupby('country').size().idxmax()
    analyses['geo_vs_asset_promotions'] = (
        f"The highest number of promotions occurred in {top_geo}."
    )

    # Asset Allocation
    best_allocated_asset = df.iloc[df['allocated_resources'].idxmax()]['asset_title']
    analyses['asset_allocation'] = (
        f"The asset '{best_allocated_asset}' received the highest allocation of resources."
    )

    # Industry Distribution
    top_industry = df['industry'].value_counts().idxmax()
    analyses['industry_distribution'] = (
        f"The '{top_industry}' industry had the highest engagement."
    )

    return analyses

def download_report_as_pdf(request, filename):
    """
    Generate a PDF of the report and return it as a downloadable file.
    """
    try:
        # Get data for the report (you may need to query based on the filename)
        image_paths = [
            'uploads/reports/allocation_vs_pacing.png',
            'uploads/reports/asset_promotion_split.png',
            'uploads/reports/geo_vs_asset_promotions.png',
            'uploads/reports/asset_allocation.png',
            'uploads/reports/industry_distribution.png',
        ]

        analyses = {
            'allocation_vs_pacing': 'Allocated resources matched expectations for the majority of the campaign.',
            'asset_promotion_split': 'Assets were promoted evenly, achieving expected distribution.',
            'geo_vs_asset_promotions': 'Promotions were strongest in North America and Europe.',
            'asset_allocation': 'Asset allocation was consistent across all campaigns.',
            'industry_distribution': 'Healthcare and IT industries had the highest engagement.',
        }

        # Render the report as HTML
        html_content = render_to_string('reports/pdf_template.html', {
            'filename': filename,
            'analyses': analyses,
            'image_paths': image_paths,
            'MEDIA_URL': settings.MEDIA_URL,
        })

        # Convert the HTML to PDF
        pdf = HTML(string=html_content, base_url=request.build_absolute_uri('/')).write_pdf()

        # Return the PDF as an HTTP response
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}_report.pdf"'
        return response

    except Exception as e:
        return HttpResponse(f"Error generating PDF: {str(e)}", status=500)

@register.filter
def get_item(dictionary, key):
    """Retrieve an item from a dictionary by its index."""
    return dictionary.get(key)


# def api_home(request):
#     return JsonResponse({'message': 'Welcome to the API!'})
#
# @csrf_exempt
# def receive_data(request):
#     if request.method == 'POST':
#         try:
#             print("Request Headers:", request.headers)
#             print("Request Body:", request.body)
#             data = json.loads(request.body)  # Parse JSON data
#             print("Data received:", data)
#             return JsonResponse({'status': 'success', 'message': 'Data received successfully'})
#         except json.JSONDecodeError:
#             return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
#     return JsonResponse({'status': 'error', 'message': 'Only POST requests allowed'}, status=405)


# @csrf_exempt
# def receive_data(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#
#             # Log for debugging
#             print("Received data:", data)
#
#             # You can validate, transform, or store this data
#             # Example: Loop through leads
#             for lead in data:
#                 print("Lead:", lead["lead_id"], lead["email"])
#
#                 # Save to DB or run analytics
#
#             return JsonResponse({"status": "success", "message": "Leads received successfully"}, status=200)
#
#         except Exception as e:
#             return JsonResponse({"status": "error", "message": str(e)}, status=400)
#
#     return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)





# def fetch_from_php(request):
#     try:
#         response = requests.get('http://192.168.0.73/sentpost/', timeout=5)
#         if response.status_code == 200:
#             # Try to parse JSON
#             try:
#                 data = response.json()
#             except ValueError:
#                 data = {'raw_response': response.text}
#
#             return JsonResponse({'success': True, 'data': data})
#         else:
#             return JsonResponse({'success': False, 'error': 'Failed with status ' + str(response.status_code)})
#     except requests.RequestException as e:
#         return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def receive_data(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            leads_list = data.get('leads')  # Expecting a key 'leads' with list of dicts

            if not leads_list or not isinstance(leads_list, list):
                return JsonResponse({'error': 'Invalid or missing leads data'}, status=400)

            # Load leads data into DataFrame
            df = pd.DataFrame(leads_list)

            # Example analysis: count leads per campaign_name
            campaign_counts = df['campaign_name'].value_counts().to_dict()

            # Example: filter leads with email ending with 'example.com'
            filtered_leads = df[df['email'].str.endswith('example.com', na=False)]

            # Prepare filtered leads data for JSON response (convert to dict)
            filtered_leads_list = filtered_leads.to_dict(orient='records')

            return JsonResponse({
                'total_leads_received': len(df),
                'leads_per_campaign': campaign_counts,
                'filtered_leads': filtered_leads_list
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid HTTP method'}, status=405)

    return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)
