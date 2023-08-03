from .archive_id import new_archive_id, box_id_bytes, folder_id_bytes
from .labels import box_labels, folder_labels_pdf
from .placement import  ArchiveMap, Box, Folder, compute_folder_placement, compute_box_folders, compute_document_placement
from .scan import scan_documents
from .mnemonic.encode import encode

import archive.paperless as paperless

import os
import sys
import argparse

def new_id():
    print(encode(box_id_bytes(os.urandom(16)) + b'\xff\xff\xff'))

def get_archive_key() -> bytes:
    key = os.getenv('ARCHIVE_KEY')
    if not key:
        raise ValueError('ARCHIVE_KEY is not set')

    key = key.encode('utf-8')
    if not key:
        raise ValueError('ARCHIVE_KEY is not valid UTF-8')

    return key

def get_archive_map():
    key = get_archive_key()
    return ArchiveMap.new(key = key)

def box_label_gen():
    p = argparse.ArgumentParser(description='Generate box labels')
    p.add_argument('box', type = int, nargs='+', help = 'which label to generate')
    p.add_argument('--print', action='store_true', help = "Print the label", default=False)
    p.add_argument('--preview', dest='print', action='store_false', help = "Preview the label")
    p.add_argument('--save', type = str, metavar='FILE', help = 'Save label PDF to FILE', default=None)
    opts = p.parse_args()

    key = get_archive_key()

    box_labels(sorted(box_id_bytes(str(i).encode('utf-8'), key=key) for i in opts.box), print=opts.print, save=opts.save)

def folder_label_gen():
    p = argparse.ArgumentParser(description='Generate folder label sheet')
    p.add_argument('sheet', type=int, help = 'which sheet to generate')
    p.add_argument('out', type=str, default = '-', nargs='?', help = 'output file or - for stdout (the default)')
    opts = p.parse_args()

    key = get_archive_key()

    target = opts.out
    if opts.out == '-':
        target = os.fdopen(sys.stdout.fileno(), 'wb')
    
    folder_labels_pdf(sorted(folder_id_bytes(str(i).encode('utf-8'), key = key) for i in range((opts.sheet-1)*39 + 1, opts.sheet*39 + 1)), target)

    if opts.out == '-':
        target.close()

def archive_map_cli():
    p = argparse.ArgumentParser(description='Archive mapping')
    subparsers = p.add_subparsers(help='Subcommands', dest='command')

    subparsers.add_parser('show', help='Show the archive map')

    subparsers.add_parser('place-folder', help='Compute folder location') \
        .add_argument('id', type=str, nargs='+', help='Folder ID')

    subparsers.add_parser('folders-in-box', help='Compute box contents') \
        .add_argument('id', type=str, nargs='+', help='Box ID')

    return p

def make_folder(folder_id):
    b = bytes.fromhex(folder_id)
    if len(b) != 8:
        raise ValueError("Folder ID must be 8 bytes long")
    return Folder(b)

def make_box(box_id):
    b = bytes.fromhex(box_id)
    if len(b) != 8:
        raise ValueError("Box ID must be 8 bytes long")
    return Box(b)

def archive_map():
    opts = archive_map_cli().parse_args()

    a = get_archive_map()

    match opts.command:
        case "show":
            print(a.boxes)
            print(a.folders)

        case "place-folder":
            for i in opts.id:
                folder = make_folder(i)
                box = compute_folder_placement(a, folder)
                print(f'{folder} -> {box}')
                print(f'{encode(folder.id)} -> {encode(box.id)}')

        case "folders-in-box":
            for i in opts.id:
                b = make_box(i)
                print(f'{b} {encode(b.id)}')
                for f in compute_box_folders(a, b):
                    print(f'{f} {encode(f.id)}')


def documents_cli():
    DEFAULT_SCANNER = 'forst.forstheim.kleen.org'
    DEFAULT_SCAN_FP = 'E4:17:14:E2:89:C3:54:FD:22:F2:9B:DF:5E:0F:7B:D2:33:C3:59:4C:AF:B9:14:34:EA:46:92:A6:7D:38:14:98'
    DEFAULT_SCAN_SOURCE = 'ADF'
    DEFAULT_SCAN_DPI = 300
    
    DEFAULT_SEPARATOR_CODE = "Document separator 5d6067b98de37c129051ff34f78dddd86ce9fb6f4c9802b4f67a80bcae89bea93909b4ad84c124afdb40f02fe19a9a100c9eb2bfa399dab12bee67e9816f601a"
    DEFAULT_SIMPLEX_CODE = "Simplex Document 9b9466ff1dfcbb765c74f2bc529f92146c217e8d1ab71bf99e428cb6b524f52026653230fee8f8e80ed802ffacc78503a6cbc8e56b83cff5aaee85671f70c4b7"

    p = argparse.ArgumentParser(description = 'Paperless document interface')
    subparsers = p.add_subparsers(help='Subcommands', dest='command')

    subparsers.add_parser('list-ids', help='List archive IDs of all documents')
    
    subparsers.add_parser('print-placements', help='Print folder placements for all documents')

    subparsers.add_parser('place-document', help='Print folder placement for specific documents') \
        .add_argument('id', type=int, nargs='+', help = 'Document ID')

    s = subparsers.add_parser('scan', help='Scan new documents and upload to paperless')
    s.add_argument('-u', '--scanner-host', help=f'Address of the scanner, defaults to {DEFAULT_SCANNER}', default=DEFAULT_SCANNER)
    s.add_argument('-S', '--scanner-source', help=f'Scanner source, can be "Flatbed" or "ADF", defaults to "{DEFAULT_SCAN_SOURCE}"', default=DEFAULT_SCAN_SOURCE)
    s.add_argument('-r', '--scanner-dpi', help=f'Scan resolution in DPI, defaults to {DEFAULT_SCAN_DPI}', default=DEFAULT_SCAN_DPI)
    s.add_argument('-f', '--scanner-https-fingerprint', help=f'Scanner certificate fingerprint, defaults to {DEFAULT_SCAN_FP}', default=DEFAULT_SCAN_FP)
    s.add_argument('-s', '--simplex', help=f'Run simplex cycle', action='store_false', dest='duplex', default=True)
    s.add_argument('--document-separator', help=f'Page separator barcode value', default=DEFAULT_SEPARATOR_CODE)
    s.add_argument('--document-simplex', help=f'Barcode value for a simplex document', default=DEFAULT_SIMPLEX_CODE)

    subparsers.add_parser('new-id', help='Generate a fresh document ID')

    subparsers.add_parser('push', help='Push a PDF from stdin into paperless') \
        .add_argument('file', nargs='?', type=argparse.FileType('rb'), default=sys.stdin.buffer)

    return p

class DocumentPlacement:
    doc_id: int
    folder: Folder
    box: Box

    def __init__(self, archive_map, doc_id):
        self.doc_id = doc_id
        self.folder = compute_document_placement(archive_map, self.doc_id)
        self.box = compute_folder_placement(archive_map, self.folder)

    def print(self):
        print(f'{self.doc_id:010d} -> {self.folder} -> {self.box}')
        print(f'{self.doc_id:010d} -> {encode(self.folder.id)} -> {encode(self.box.id)}')

def with_edges_on(gen, f):
    last = None
    for g in gen:
        if last and last != f(g):
            yield (g, True)
        else:
            yield (g, False)
        last = f(g)

def print_placements(archive_map, ids):
    placements = sorted((DocumentPlacement(archive_map, id) for id in ids), key = lambda p: (p.box, p.doc_id))
    for (p, do_nl) in with_edges_on(placements, lambda p: p.box):
        if do_nl:
            print()
        p.print()

def documents():
    opts = documents_cli().parse_args()

    match opts.command:
        case 'list-ids':
            for id in paperless.document_ids():
                print(f'{id:010d}')

        case 'print-placements':
            a = get_archive_map()
            print_placements(a, paperless.document_ids())

        case 'place-document':
            a = get_archive_map()
            print_placements(a, opts.id)

        case 'new-id':
            print(f'{new_archive_id(os.urandom(16)):010d}')

        case 'scan':
            docs = scan_documents(opts)
            with paperless.pool_manager() as http:
                for d in docs:
                    paperless.push_document(http, d)

            a = get_archive_map()
            ids = [d.id for d in docs]
            for i in ids:
               print(f'{i:010d}')
            print('')
            print_placements(a, ids)

        case 'push':
            filename = opts.file.name
            doc = opts.file.read()
            with paperless.pool_manager() as http:
                paperless.push(http, doc, filename, filename)
