import os
import subprocess
import urllib3
import json

def stream_paginated(http, method, url, **kwargs):
    first_page = json.loads(http.request(method, url, **kwargs).data.decode('utf-8'))
    yield first_page

    if not first_page['next']:
        return

    next_page_url = urllib3.util.parse_url(first_page['next'])._replace(scheme = 'https').url
    while True:
        page = json.loads(http.request(method, next_page_url, **kwargs).data.decode('utf-8'))
        yield page
        if page['next']:
            next_page_url = urllib3.util.parse_url(page['next'])._replace(scheme = 'https').url
        else:
            break

def document_ids():
    endpoint = os.getenv('PAPERLESS_ENDPOINT')
    token = os.getenv('PAPERLESS_TOKEN')
    paperless_cert = os.getenv('PAPERLESS_CERT')
    paperless_cert_key = os.getenv('PAPERLESS_CERT_KEY')

    with urllib3.PoolManager(cert_file = paperless_cert, key_password = paperless_cert_key) as http:
        for docs in stream_paginated(http, 'GET', f'{endpoint}/api/documents/',
                                     fields = { 'archive_serial_number__isnull': 'false', 'ordering': 'archive_serial_number' },
                                     headers = {
                                        'Authorization': f'Token {token}'
                                     }):
            for x in docs['results']:
                yield x['archive_serial_number']
