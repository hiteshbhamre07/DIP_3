import os
import pandas as pd
from django.shortcuts import render
from django.http import HttpResponse
import io

def transform_data(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        uploaded_file = request.FILES['excel_file']
        ext = os.path.splitext(uploaded_file.name)[-1]

        try:
            # Read file based on extension
            if ext in ['.xlsx', '.xls']:
                df = pd.read_excel(uploaded_file)
            elif ext == '.csv':
                df = pd.read_csv(uploaded_file)
            else:
                raise ValueError("Unsupported file format")

            # Clean string columns
            for col in df.select_dtypes(include='object').columns:
                df[col] = df[col].map(lambda x: x.strip() if isinstance(x, str) else x)

            # Normalize emails
            for col in df.select_dtypes(include='object').columns:
                df[col] = df[col].map(lambda x: x.strip() if isinstance(x, str) else x)

            # Normalize email
            for col in df.columns:
                if col.lower() == 'email':
                    df[col] = df[col].astype(str).str.strip().str.lower()
                    break

            # Replace empty cells with 'NA'
            df.fillna('NA', inplace=True)

            # Write cleaned data to Excel file in memory
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)

            output.seek(0)
            response = HttpResponse(
                output,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename=cleaned_data.xlsx'
            return response

        except Exception as e:
            return render(request, 'transform/transform.html', {
                'error': f"Error processing file: {e}",
                'segment': 'transform_data'
            })

    return render(request, 'transform/transform.html', {'segment': 'transform_data'})

