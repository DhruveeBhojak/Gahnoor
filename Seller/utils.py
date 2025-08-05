
import csv
from django.http import HttpResponse

def generate_csv_response(data, filename='report.csv', headers=[]):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    if headers:
        writer.writerow(headers)

    for row in data:
        writer.writerow(row)

    return response
