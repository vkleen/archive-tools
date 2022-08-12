from collections.abc import Iterable
import subprocess

from blabel import LabelWriter
from weasyprint import CSS
from pikepdf import Pdf, Page, Rectangle
from io import BytesIO

from typing import Iterable

def print_command(print):
    print_pipeline = "| dymopipe compile -t label --density normal -l c | dymopipe label"
    preview_pipeline = "| imv -"
    return f"convert -density 300x300 pdf:- -colorspace gray -type grayscale -auto-threshold OTSU png:- {print_pipeline if print else preview_pipeline}"

label_template = """
<div class='page'>
  <div class='code'>
    <img class='code' src="{{label_tools.datamatrix(url)}}"/>
  </div>
  <div class='label'>
    {{id}}
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
  height: 30mm;
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

folder_label_css = """
@page {
  size: 60mm 20.5mm;
  padding: 2mm;
  display: flex;
  align-items: center;
}
.page {
  width: 56mm;
  height: 16.5mm;

  display: flex;
  align-items: center;
  justify-items: center;
}
div.code {
  padding: 3mm;
  display: inline-block;
}
img.code {
  height: 14mm;
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

def box_label(id_str: str, print=False):
    writer = LabelWriter(item_template=label_template, default_stylesheets=(CSS(string=box_label_css),))
    id_split = '<br/>'.join(id_str[i:i+16] for i in range(0, len(id_str), 16))
    records =  [ {
        "url": f"https://paperless.kleen.org/archive/box/{id_str}",
        "id": id_split,
    } ]
    label_pdf = writer.write_labels(records)
    subprocess.run(print_command(print), shell = True, input = label_pdf)

# PDF units are 1/72", 1" = 25.4mm, 1mm = 72/25.4 1/72"
PDF_MM = 72/25.4

def nup_rectangle(index):
    column = index % 3
    row = index // 3
    
    top = 12 + row * 21
    left = 14.5 + 60 * column
    right = 74.5 + 60 * column
    bottom = top + 21

    pdf_top = 297 - top
    pdf_bottom = 297 - bottom

    return Rectangle(left*PDF_MM, pdf_bottom*PDF_MM, right*PDF_MM, pdf_top*PDF_MM)

def pdf_to_bytes(pdf):
    bytes = BytesIO()
    pdf.save(bytes)
    return bytes.getvalue()

def folder_labels_pdf(id_strs: Iterable[str], target=None):
    def make_record(id_str):
        id_split = '<br/>'.join(id_str[i:i+8] for i in range(0, len(id_str), 8))
        return {
            "url": f"https://paperless.kleen.org/archive/{id_str}",
            "id": id_split,
        }

    writer = LabelWriter(item_template=label_template, default_stylesheets=(CSS(string=folder_label_css),))
    records = list(make_record(id_str) for id_str in id_strs)

    pdf_bytes = writer.write_labels(records)
    if not pdf_bytes:
        return
    pdf = Pdf.open(BytesIO(pdf_bytes))

    dst = Pdf.new()
    dst.add_blank_page(page_size=(210*PDF_MM, 297*PDF_MM))
    dst_page = dst.pages[0]

    for i,p in enumerate(pdf.pages[0:39]):
        dst_page.add_overlay(p, nup_rectangle(i))

    if target:
        dst.save(target)
        return None
    else:
        return pdf_to_bytes(dst)
