from .archive_id import new_archive_id, box_id_bytes, folder_id_bytes
from .labels import box_label, folder_labels_pdf

from dataclasses import dataclass

import os
import sys
import struct
import hashlib
import argparse

folders = list(range(1,21))

@dataclass(frozen=True, order=True)
class Box:
    id: bytes

    def __repr__(self):
        return f'Box({self.id.hex()})'

@dataclass(frozen=True, order=True)
class Folder:
    id: bytes

    def __repr__(self):
        return f'Folder({self.id.hex()})'

class ArchiveMap:
    def __init__(self, key=b''):
        self.boxes = list(sorted(
            Box(box_id_bytes(str(i).encode('utf-8'), key=key)) for i in range(1,4)
        ))
        self.folders = list(sorted(
            Folder(folder_id_bytes(str(i).encode('utf-8'), key=key)) for i in range(1,51)
        ))
        pass

def label_gen():
    key = os.getenv('ARCHIVE_KEY')
    if not key:
        return
    key = key.encode('utf-8')

    a = ArchiveMap(key = key)
    box_label(a.boxes[0].id.hex(), print=True)

def label_sheet():
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

def archive_map():
    print(ArchiveMap().boxes)
    print(ArchiveMap().folders)

def compute_rendezvous_weight(doc_id, folder_id):
    encoded = struct.pack('<ll', doc_id, folder_id)
    return int.from_bytes(hashlib.blake2b(encoded, digest_size=4).digest(), byteorder='little')

def compute_folder(doc_id, folders):
    return sorted(((f, compute_rendezvous_weight(doc_id, f)) for f in folders), key = lambda t: t[1])[0]
