from django.shortcuts import render,redirect
from django.http import HttpResponse,JsonResponse
# from django.core.files.storage import FileSystemStorage
import logging
import csv
import pandas as pd
from .models import MasterSupp
from django.contrib.auth.decorators import login_required
from io import StringIO
from django.db.models import Q
import chardet

# Show Supp Data function
@login_required(login_url="/login/")
def suppression_master(request):
    # Fetch all records from MasterSupp model
    supp_data = MasterSupp.objects.all()

    # Define context with suppression data
    context = {
        'segment': 'suppression_master',
        'supp_data': supp_data
    }
    # Render the template with the context
    return render(request, 'suppression/suppression.html', context)

# Download Supp Data function
def download_suppression_csv(request):
    """
    View to download suppression data as a CSV file.
    """
    # Create the response object with CSV content type
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="suppression_data.csv"'

    # Create a CSV writer object and write the header row
    writer = csv.writer(response)
    writer.writerow(['CID', 'Campaign', 'First Name', 'Last Name', 'Company', 'Domain', 'Email', 'Industry', 'Employees', 'Job Title', 'Phone', 'Country'])

    # Query suppression data from the database and write each row
    suppression_data = MasterSupp.objects.all()
    for supp in suppression_data:
        writer.writerow([supp.campaign_id, supp.campaign_name, supp.first_name, supp.last_name, supp.company, supp.domain, supp.email_address, supp.industry, supp.number_of_employees, supp.job_title, supp.phone, supp.country])

    return response


@login_required(login_url="/login/")
def suppression_option(request):
    # Fetch all records from MasterSupp model
    supp_data = MasterSupp.objects.all()

    # Define context with suppression data
    context = {
        'segment': 'suppression_master',
        'supp_data': supp_data
    }
    # Render the template with the context
    return render(request, 'suppression/supp_types.html', context)


logger = logging.getLogger(__name__)

def get_file_encoding(file):
    """Detect file encoding using chardet."""
    raw_data = file.read(10000)  # Read the first 10,000 bytes to detect encoding
    result = chardet.detect(raw_data)  # Detect encoding
    return result['encoding']

@login_required(login_url="/login/")
def upload_file(request):
    if request.method == 'POST' and request.FILES.get('upload_file'):
        uploaded_file = request.FILES['upload_file']

        # Check if file type is supported
        if uploaded_file.name.endswith('.csv'):
            try:
                # Ensure the file is not empty
                if uploaded_file.size == 0:
                    return JsonResponse({'error': 'The uploaded file is empty.'}, status=400)

                # Read the file and replace non-breaking spaces with regular spaces
                file_content = uploaded_file.read().decode('utf-8', errors='ignore')
                cleaned_content = file_content.replace('\xa0', ' ')  # Replace non-breaking spaces

                # Use csv.reader to process the cleaned content
                csvfile = StringIO(cleaned_content)
                reader = csv.reader(csvfile)
                rows = [row for row in reader]  # Store rows as a list

                # Check if the CSV has data
                if not rows or len(rows[0]) == 0:
                    raise ValueError("The uploaded file is empty or has no columns.")

                # Log the successful file read
                logger.info(f"Successfully read CSV file with {len(rows)} rows.")

                # Convert CSV rows to a DataFrame
                df = pd.DataFrame(rows[1:], columns=rows[0])  # The first row is the header

                # Check if the dataframe is empty or has no columns
                if df.empty or df.shape[1] == 0:
                    raise ValueError("No columns to parse from the CSV file.")

                # Log the DataFrame shape
                logger.info(f"DataFrame created with {df.shape[0]} rows and {df.shape[1]} columns.")

            except Exception as e:
                # Handle errors during file reading
                logger.error(f"Error reading CSV file: {str(e)}")
                return JsonResponse({'error': f'Error reading CSV file: {str(e)}'}, status=400)

        elif uploaded_file.name.endswith('.xls') or uploaded_file.name.endswith('.xlsx'):
            try:
                # Read Excel file
                df = pd.read_excel(uploaded_file)

                # Check if the dataframe is empty or has no columns
                if df.empty or df.shape[1] == 0:
                    raise ValueError("No columns to parse from the Excel file.")

            except Exception as e:
                logger.error(f"Error reading Excel file: {str(e)}")
                return JsonResponse({'error': f'Error reading Excel file: {str(e)}'}, status=400)
        else:
            return JsonResponse({'error': 'Unsupported file type. Please upload a CSV or Excel file.'}, status=400)

        # Convert Timestamps to string
        def convert_timestamps(obj):
            if isinstance(obj, pd.Timestamp):
                return obj.isoformat()  # Convert to ISO 8601 string
            raise TypeError(f"Object of type {obj.__class__.__name__} is not serializable")

        # Apply conversion to DataFrame records
        file_data = df.to_dict(orient='records')
        file_data = [
            dict((key, convert_timestamps(value) if isinstance(value, pd.Timestamp) else value) for key, value in record.items())
            for record in file_data
        ]

        # Store file data in session
        request.session['uploaded_fields'] = df.columns.tolist()
        request.session['file_data'] = file_data

        # Redirect to map columns page
        return redirect('map_columns')

    return render(request, 'suppression/upload_file.html')
# Map columns and process the data
# @login_required(login_url="/login/")
# def map_columns(request):
#     if request.method == 'POST':
#         # Get the uploaded and master field names from the request
#         uploaded_field = request.POST.get('uploaded_field')
#         master_field = request.POST.get('master_field')
#
#         # Validate the presence of the necessary fields
#         if not uploaded_field or not master_field:
#             return render(request, 'suppression/map_columns.html', {
#                 'error': "Uploaded field or master field is missing. Please select both fields."
#             })
#
#         # Fetch the values from the MasterSupp model for faster lookups
#         master_values = set(MasterSupp.objects.values_list(master_field, flat=True))
#
#         # Get the uploaded file data from the session
#         uploaded_fields = request.session.get('uploaded_fields')
#         file_data = request.session.get('file_data')
#
#         if not uploaded_fields or not file_data:
#             return render(request, 'suppression/map_columns.html', {
#                 'error': "No file data or fields found in session. Please upload a file first."
#             })
#
#         # Process the file data and map the columns
#         mapped_data = []
#         for row in file_data:
#             # Skip rows that are completely empty (no relevant data)
#             if all(value is None or value == '' for value in row.values()):
#                 continue
#
#             # For each row, check if the uploaded field matches the master field (case-sensitive)
#             row_status = 'True' if row.get(uploaded_field) in master_values else 'False'
#
#             # Add status and mapping information to the row
#             mapped_row = {
#                 **row,
#                 'status': row_status,  # Add the status column
#                 'mapped_column': uploaded_field  # Explicitly show the uploaded field name
#             }
#
#             # Add any additional fields, if necessary (no case change)
#             for field in uploaded_fields:
#                 if field != uploaded_field:  # Skip the uploaded field since it's already mapped
#                     mapped_row[field] = row.get(field)
#
#             # Only append rows that contain at least one valid field (non-empty)
#             if any(value not in [None, ''] for value in mapped_row.values()):
#                 mapped_data.append(mapped_row)
#
#         # Convert the mapped data into a DataFrame
#         df = pd.DataFrame(mapped_data)
#
#         # If no rows are mapped, return an error
#         if df.empty:
#             return render(request, 'suppression/map_columns.html', {
#                 'error': "No valid data available after mapping. Please check the file and try again."
#             })
#
#         # Create a CSV buffer in memory
#         csv_buffer = StringIO()
#         df.to_csv(csv_buffer, index=False)
#         csv_buffer.seek(0)
#
#         # Prepare the response as a downloadable CSV file with utf-8 encoding
#         response = HttpResponse(csv_buffer, content_type='text/csv; charset=utf-8')
#         response['Content-Disposition'] = 'attachment; filename="mapped_file.csv"'
#
#         # Return the CSV file as a response to the user
#         return response
#
#     # Initial page load or GET request
#     uploaded_fields = request.session.get('uploaded_fields', [])
#     master_fields = [field.name for field in MasterSupp._meta.fields]
#
#     return render(request, 'suppression/map_columns.html', {
#         'uploaded_fields': uploaded_fields,
#         'master_fields': master_fields,
#     })

@login_required(login_url="/login/")
def map_columns(request):
    if request.method == 'POST':
        uploaded_fields = request.POST.getlist('uploaded_fields')  # List of selected columns
        master_fields = request.POST.getlist('master_fields')  # List of master field selections

        # Validate the presence of necessary fields
        if not uploaded_fields or not master_fields:
            return render(request, 'suppression/map_columns.html', {
                'error': "Uploaded fields or master fields are missing. Please select fields for mapping."
            })

        # Fetch the master data from the database for the selected master fields
        try:
            master_values = {field: set(MasterSupp.objects.values_list(field, flat=True)) for field in master_fields}
        except MasterSupp.DoesNotExist:
            return render(request, 'suppression/map_columns.html', {
                'error': "Error fetching master data. Please check the database."
            })

        # Get the uploaded file data from the session
        file_data = request.session.get('file_data', [])
        if not file_data:
            return render(request, 'suppression/map_columns.html', {
                'error': "No file data found. Please upload a CSV file first."
            })

        # Process the uploaded data and map columns
        mapped_data = []
        for row in file_data:
            mapped_row = {}
            # Iterate over the selected uploaded fields and master fields
            for i, uploaded_field in enumerate(uploaded_fields):
                # Ensure that we do not go out of bounds if uploaded_fields is smaller than master_fields
                if i < len(master_fields):
                    master_field = master_fields[i]
                    if uploaded_field in row:
                        # Check if the uploaded field's value matches any of the master values
                        row_status = 'Matched' if row.get(uploaded_field) in master_values.get(master_field, set()) else 'Not Matched'
                        mapped_row[uploaded_field] = row.get(uploaded_field)
                        mapped_row[f'{master_field}_status'] = row_status

            # Only append rows with non-empty values
            if any(value not in [None, ''] for value in mapped_row.values()):
                mapped_data.append(mapped_row)

        # Convert the mapped data into a DataFrame
        df = pd.DataFrame(mapped_data)
        if df.empty:
            return render(request, 'suppression/map_columns.html', {
                'error': "No valid data available after mapping. Please check the file and try again."
            })

        # Create a CSV buffer in memory and return as a downloadable file
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        response = HttpResponse(csv_buffer, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="mapped_file.csv"'
        return response

    # Handle GET request (initial page load or refresh)
    csv_columns = request.session.get('csv_columns', [])
    return render(request, 'suppression/map_columns.html', {
        'csv_columns': csv_columns
    })

# Download the mapped file
def download_mapped_file(request):
    # Retrieve updated data from session
    updated_file_data = request.session.get('updated_file_data')

    if not updated_file_data:
        return JsonResponse({'error': 'No mapped file data found.'}, status=400)

    # Convert data to CSV
    df = pd.DataFrame(updated_file_data)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="mapped_file_with_status.csv"'

    # Write data to CSV
    df.to_csv( response,index=False)
    return response





def map_fields(uploaded_fields, master_fields, file_data):
    """
    Map uploaded fields to master fields and check for matches in the database.
    """
    try:
        # Fetch master values for the selected fields
        master_values = {
            field: set(MasterSupp.objects.values_list(field, flat=True))
            for field in master_fields
        }

        # Map fields and check for matches
        mapped_data = []
        for row in file_data:
            mapped_row = {}
            for i, uploaded_field in enumerate(uploaded_fields):
                if i < len(master_fields):
                    master_field = master_fields[i]
                    value = row.get(uploaded_field, None)
                    status = 'Matched' if value in master_values.get(master_field, set()) else 'Not Matched'
                    mapped_row[uploaded_field] = value
                    mapped_row[f'{master_field}_status'] = status
            mapped_data.append(mapped_row)

        return pd.DataFrame(mapped_data)
    except Exception as e:
        logger.error(f"Error during field mapping: {str(e)}")
        raise




# Upload function for dumpo data

@login_required(login_url="/login/")
def map_uploaded_columns(request):
    if request.method == 'POST':
        # Retrieve mapping information
        mappings = {key: value for key, value in request.POST.items() if key != 'csrfmiddlewaretoken'}

        # Retrieve file data from the session
        file_data = request.session.get('file_data', [])
        if not file_data:
            return render(request, 'suppression/map_columns.html', {
                'error': 'No file data found in session. Please upload a file first.'
            })

        # Apply mappings to the data
        mapped_data = []
        for row in file_data:
            mapped_row = {master_field: row.get(csv_column, None) for master_field, csv_column in mappings.items() if csv_column}
            mapped_data.append(mapped_row)

        # Check for uniqueness based on email
        unique_emails = set(MasterSupp.objects.values_list('email_address', flat=True))
        unique_rows = [row for row in mapped_data if row.get('email_address') not in unique_emails]

        # Insert unique rows into the database
        new_records = [MasterSupp(**row) for row in unique_rows]
        MasterSupp.objects.bulk_create(new_records)

        # Redirect to the suppression master page after successful insertion
        return redirect('suppression_master')

    # Initial GET request: Load uploaded fields and master fields
    uploaded_fields = request.session.get('uploaded_fields', [])
    master_fields = [field.name for field in MasterSupp._meta.fields]

    return render(request, 'suppression/map_columns.html', {
        'csv_columns': uploaded_fields,
        'db_fields': master_fields,
    })


@login_required(login_url="/login/")
def upload_dump(request):
    # Define a max file size (e.g., 10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    if request.method == 'POST' and request.FILES.get('upload_file'):
        uploaded_file = request.FILES['upload_file']

        # Check file size
        if uploaded_file.size > MAX_FILE_SIZE:
            return render(request, 'suppression/upload_dump.html', {
                'error': f'The uploaded file is too large. Maximum allowed size is 10MB.'
            })

        # Ensure the uploaded file is CSV
        if not uploaded_file.name.endswith('.csv'):
            return render(request, 'suppression/upload_dump.html', {
                'error': 'Only CSV files are supported. Please upload a valid CSV file.'
            })

        try:
            # Read the file and replace non-breaking spaces with regular spaces
            file_content = uploaded_file.read().decode('utf-8', errors='ignore')
            cleaned_content = file_content.replace('\xa0', ' ')  # Replace non-breaking spaces

            # Use csv.reader to process the cleaned content
            csvfile = StringIO(cleaned_content)
            reader = csv.reader(csvfile)
            rows = [row for row in reader]  # Store rows as a list

            # Check if the CSV has data
            if not rows or len(rows[0]) == 0:
                raise ValueError("The uploaded file is empty or has no columns.")

            # Log the successful file read
            logger.info(f"Successfully read CSV file with {len(rows)} rows.")

            # Convert CSV rows to a DataFrame
            df = pd.DataFrame(rows[1:], columns=rows[0])  # The first row is the header

            # Log the DataFrame shape
            logger.info(f"DataFrame created with {df.shape[0]} rows and {df.shape[1]} columns.")

        except pd.errors.ParserError:
            # Handle CSV parsing errors
            logger.error(f"Error parsing the CSV file: {uploaded_file.name}")
            return render(request, 'suppression/upload_dump.html', {
                'error': 'Error reading the CSV file. Please ensure it is a valid CSV file.'
            })
        except Exception as e:
            # Handle other exceptions (e.g., empty file, no columns)
            logger.error(f"Error processing the file: {str(e)}")
            return render(request, 'suppression/upload_dump.html', {
                'error': f'Error processing the file: {str(e)}'
            })

        # Store file data in the session for column mapping
        request.session['uploaded_fields'] = df.columns.tolist()
        request.session['file_data'] = df.to_dict(orient='records')

        # Redirect to the column mapping page
        return redirect('map_columns_dump')

    # Render the upload page for GET request
    return render(request, 'suppression/upload_dump.html')


@login_required(login_url="/login/")
def map_columns_dump(request):
    if request.method == 'POST':
        # Retrieve mapping information from the form
        mappings = {key: value for key, value in request.POST.items() if key != 'csrfmiddlewaretoken'}

        # Retrieve file data from the session
        file_data = request.session.get('file_data', [])
        if not file_data:
            return render(request, 'suppression/map_columns_dump.html', {
                'error': 'No file data found in session. Please upload a file first.'
            })

        # Apply mappings to the data
        mapped_data = []
        for row in file_data:
            mapped_row = {master_field: row.get(csv_column, None) for master_field, csv_column in mappings.items() if
                          csv_column}
            mapped_data.append(mapped_row)

        # Check for uniqueness based on email_address
        unique_emails = set(MasterSupp.objects.values_list('email_address', flat=True))
        unique_rows = [row for row in mapped_data if row.get('email_address') not in unique_emails]

        # Insert unique rows into the database
        new_records = [MasterSupp(**row) for row in unique_rows]
        MasterSupp.objects.bulk_create(new_records)

        # Redirect to the suppression master page after successful insertion
        return redirect('suppression_master')

    # Initial GET request: Load uploaded fields and master fields
    uploaded_fields = request.session.get('uploaded_fields', [])

    # Exclude the 'id' field (auto-increment) from the list of database fields
    master_fields = [field.name for field in MasterSupp._meta.fields if field.name != 'id']

    return render(request, 'suppression/map_columns_dump.html', {
        'csv_columns': uploaded_fields,
        'db_fields': master_fields,
    })


