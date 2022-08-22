from blake3 import blake3
from dataclasses import dataclass

@dataclass(frozen=True)
class Document:
    data: bytes
    id: int

ARCHIVE_ID_CONTEXT = 'paperless.kleen.org/v1 archive id generator'
BOX_ID_CONTEXT = 'paperless.kleen.org/v1 box id generator'
FOLDER_ID_CONTEXT = 'paperless.kleen.org/v1 folder id generator'

def new_archive_id(data):
    return int.from_bytes(blake3(data).digest(length=4), byteorder='little') & 0x7fffffff

def box_id_bytes(data, key=b''):
    return blake3(
        data,
        key=blake3(key, derive_key_context=BOX_ID_CONTEXT).digest()) \
        .digest(length=8)

def folder_id_bytes(data, key=b''):
    return blake3(
        data,
        key=blake3(key, derive_key_context=FOLDER_ID_CONTEXT).digest()) \
        .digest(length=8)
