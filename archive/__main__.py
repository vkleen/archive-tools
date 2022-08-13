from .archive_id import new_archive_id, box_id_bytes, folder_id_bytes
from .labels import box_labels, folder_labels_pdf
from .placement import  ArchiveMap, Box, Folder, compute_folder_placement, compute_box_folders, compute_document_placement

import archive.paperless as paperless

import os
import sys
import logging
import argparse


def box_label_gen():
    p = argparse.ArgumentParser(description='Generate box labels')
    p.add_argument('box', type = int, nargs='+', help = 'which label to generate')
    p.add_argument('--print', action='store_true', help = "Print the label", default=False)
    p.add_argument('--preview', dest='print', action='store_false', help = "Preview the label")
    p.add_argument('--save', type = str, metavar='FILE', help = 'Save label PDF to FILE', default=None)
    opts = p.parse_args()
    print(opts)

    key = os.getenv('ARCHIVE_KEY')
    if not key:
        return
    key = key.encode('utf-8')

    box_labels(sorted(box_id_bytes(str(i).encode('utf-8'), key=key).hex() for i in opts.box), print=opts.print, save=opts.save)

def folder_label_gen():
    p = argparse.ArgumentParser(description='Generate folder label sheet')
    p.add_argument('sheet', type=int, help = 'which sheet to generate')
    p.add_argument('out', type=str, default = '-', nargs='?', help = 'output file or - for stdout (the default)')
    opts = p.parse_args()

    key = os.getenv('ARCHIVE_KEY')
    if not key:
        return
    key = key.encode('utf-8')

    target = opts.out
    if opts.out == '-':
        target = os.fdopen(sys.stdout.fileno(), 'wb')
    
    folder_labels_pdf(sorted(folder_id_bytes(str(i).encode('utf-8'), key = key).hex() for i in range((opts.sheet-1)*39 + 1, opts.sheet*39 + 1)), target)

    if opts.out == '-':
        target.close()


def new_id():
    print(new_archive_id(os.urandom(16)))

def archive_map_cli():
    p = argparse.ArgumentParser(description='Archive mapping')
    subparsers = p.add_subparsers(help='Subcommands', dest='command')

    subparsers.add_parser('show', help='Show the archive map')

    subparsers.add_parser('folder', help='Compute folder location') \
        .add_argument('id', type=str, nargs='+', help='Folder ID')

    subparsers.add_parser('folders', help='Compute box contents') \
        .add_argument('id', type=str, nargs='+', help='Box ID')

    return p

def make_folder(folder_id):
    b = bytes.fromhex(folder_id)
    if len(b) != 8:
        raise ValueError("Folder ID must be 8 bytes long")
    return Folder(b)

def make_box(folder_id):
    b = bytes.fromhex(folder_id)
    if len(b) != 8:
        raise ValueError("Box ID must be 8 bytes long")
    return Box(b)

def archive_map():
    opts = archive_map_cli().parse_args()

    key = os.getenv('ARCHIVE_KEY')
    if not key:
        return
    key = key.encode('utf-8')
    a = ArchiveMap.new(key = key)

    match opts.command:
        case "show":
            print(a.boxes)
            print(a.folders)
        case "folder":
            for i in opts.idL:
                compute_folder_placement(a, make_folder(i))
        case "folders":
            for i in opts.id:
                print(make_box(i))
                compute_box_folders(a, make_box(i))

def documents_cli():
    p = argparse.ArgumentParser(description = 'Paperless document interface')
    subparsers = p.add_subparsers(help='Subcommands', dest='command')

    subparsers.add_parser('list-ids', help='List archive IDs of all documents')
    
    subparsers.add_parser('print-placements', help='Print folder placements for all documents')

    subparsers.add_parser('place-document', help='Print folder placement for specific documents') \
        .add_argument('id', type=int, nargs='+', help = 'Document ID')

    return p

def print_document_placement(archive_map, doc_id):
    folder = compute_document_placement(archive_map, doc_id)
    box = compute_folder_placement(archive_map, folder)
    print(f'{doc_id:010d} -> {folder} -> {box}')

def documents():
    logging.basicConfig(level=logging.DEBUG)
    opts = documents_cli().parse_args()

    match opts.command:
        case 'list-ids':
            print(f'{0x7fffffff:010d}')
            for id in paperless.document_ids():
                print(f'{id:010d}')
        case 'print-placements':
            key = os.getenv('ARCHIVE_KEY')
            if not key:
                return
            key = key.encode('utf-8')
            a = ArchiveMap.new(key = key)

            for id in paperless.document_ids():
                print_document_placement(a, id)
        case 'place-document':
            key = os.getenv('ARCHIVE_KEY')
            if not key:
                return
            key = key.encode('utf-8')
            a = ArchiveMap.new(key = key)

            for id in opts.id:
                print_document_placement(a, id)
