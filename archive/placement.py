from .archive_id import box_id_bytes, folder_id_bytes
from dataclasses import dataclass
from blake3 import blake3

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
    def __init__(self):
        self.boxes = []
        self.folders = []

    def new(*, boxes=3, folders=50, key = b''):
        a = ArchiveMap()
        a.boxes = list(sorted(
            Box(box_id_bytes(str(i).encode('utf-8'), key=key)) for i in range(1,boxes+1)
        ))
        a.folders = list(sorted(
            Folder(folder_id_bytes(str(i).encode('utf-8'), key=key)) for i in range(1,folders+1)
        ))
        return a

def compute_box_folders(archive_map, box):
    return list(filter(lambda f: compute_folder_placement(archive_map, f) == box, archive_map.folders))

def box_straw_weight(box, folder):
    return int.from_bytes(blake3(box.id + folder.id).digest(length=8), byteorder='little')

def compute_folder_placement(archive_map, folder):
    return sorted((box_straw_weight(box, folder), box) for box in archive_map.boxes)[0][1]

def folder_straw_weight(folder, doc_id):
    return int.from_bytes(blake3(folder.id + f'{doc_id:010d}'.encode('utf-8')).digest(length=8), byteorder='little')

def compute_document_placement(archive_map, doc_id):
    return sorted((folder_straw_weight(folder, doc_id), folder) for folder in archive_map.folders)[0][1]
