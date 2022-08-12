from .archive_id import new_archive_id, box_id_bytes

import os
import struct
import hashlib
import subprocess

from blabel import LabelWriter
from weasyprint import CSS

folders = list(range(1,21))

class ArchiveMap:
    def __init__(self):
        self.boxes = []
        self.folders = list(range(1,21))
        pass

def print_command(preview):
    convert_output = "png:-" \
        if not preview else "png:test.png"
    post_process = "| nix run github:vkleen/dymopipe -- compile -t label --density normal -l c | nix run github:vkleen/dymopipe -- label" \
        if not preview else ""
    return f"nix shell nixpkgs#imagemagick nixpkgs#ghostscript -c convert -density 300x300 pdf:- -colorspace gray -type grayscale -auto-threshold OTSU {convert_output} {post_process}"

box_label_template = """
<div class='page'>
  <div class='code'>
    <img class='code' src="{{label_tools.datamatrix(box_url)}}"/>
  </div>
  <div class='label'>
    {{box_id}}
  </div>
</div>
"""

box_label_css = """
@page {
  size: 101mm 54mm;
  padding: 5mm;
  display: flex;
  align-items: center;
}
.page {
  width: 91mm;
  height: 44mm;

  display: flex;
  align-items: center;
  justify-items: center;
}
div.code {
  padding: 4mm;
  display: inline-block;
}
img.code {
  height: 25mm;
  image-rendering: pixelated;
}
.label {
  font-family: PragmataPro Mono;
  font-weight: normal;
  line-height: 1em;
  font-size: 24px;
  vertical-align: middle;
  text-align: center;
}
"""

def label_gen():
    writer = LabelWriter(item_template=box_label_template, default_stylesheets=(CSS(string=box_label_css),))
    box_id = box_id_bytes(os.urandom(16)).hex()
    box_id_string = '<br/>'.join(box_id[i:i+16] for i in range(0, len(box_id), 16))
    records =  [ {
        "box_url": f"https://paperless.kleen.org/archive/box/{box_id}",
        "box_id": box_id_string,
    } ]
    label_pdf = writer.write_labels(records)
    subprocess.run(print_command(True), shell = True, input = label_pdf)

def new_id():
    print(new_archive_id(os.urandom(16)))

def compute_rendezvous_weight(doc_id, folder_id):
    encoded = struct.pack('<ll', doc_id, folder_id)
    return int.from_bytes(hashlib.blake2b(encoded, digest_size=4).digest(), byteorder='little')

def compute_folder(doc_id, folders):
    return sorted(((f, compute_rendezvous_weight(doc_id, f)) for f in folders), key = lambda t: t[1])[0]
