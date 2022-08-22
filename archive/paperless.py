import os
import urllib3
import json

from .archive_id import Document

def pool_manager():
    paperless_cert = os.getenv('PAPERLESS_CERT')
    paperless_cert_key = os.getenv('PAPERLESS_CERT_KEY')
    return urllib3.PoolManager(cert_file = paperless_cert, key_password = paperless_cert_key)

def authorization_header():
    token = os.getenv('PAPERLESS_TOKEN')
    return { 'Authorization': f'Token {token}' }

def paperless_endpoint():
    return os.getenv('PAPERLESS_ENDPOINT')

def stream_paginated(http, method, url, **kwargs):
    next_page_url = url
    while True:
        page = json.loads(http.request(method, next_page_url, **kwargs).data.decode('utf-8'))
        yield page
        if not page['next']:
            return
        next_page_url = urllib3.util.parse_url(page['next'])._replace(scheme = 'https').url

def document_ids():
    with pool_manager() as http:
        for docs in stream_paginated(http, 'GET', f'{paperless_endpoint()}/api/documents/',
                                     fields = { 'archive_serial_number__isnull': 'false', 'ordering': 'archive_serial_number' },
                                     headers = authorization_header()):
            for x in docs['results']:
                yield x['archive_serial_number']

def push_document(http, doc: Document):
    http.request('POST', f'{paperless_endpoint()}/api/documents/post_document/',
                 headers = authorization_header(),
                 fields = {
                     'title': f'{doc.id:010d}',
                     'document': ('document.pdf', doc.data, 'application/pdf')
                 })
