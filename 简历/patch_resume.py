# -*- coding: utf-8 -*-
"""在用户已手改过的 docx 上做增量修改，不重新生成整份文档。"""

import copy
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.table import _Row

DOCX = Path(r"E:\个人作品网站\简历\简历-客户端开发.docx")
GITHUB = "https://github.com/AKI12345"


def unique_cells(row):
    seen, out = set(), []
    for c in row.cells:
        if id(c._tc) in seen:
            continue
        seen.add(id(c._tc))
        out.append(c)
    return out


def first_run(cell):
    for p in cell.paragraphs:
        if p.runs:
            return p.runs[0]
    return None


def write_cell(cell, text):
    """保留第一段第一个 run 的格式，替换整段文字。"""
    for p in cell.paragraphs[1:]:
        p._element.getparent().remove(p._element)
    p = cell.paragraphs[0]
    if p.runs:
        p.runs[0].text = text
        for r in p.runs[1:]:
            r._element.getparent().remove(r._element)
    else:
        p.add_run(text)


def append_run_like(cell, text):
    """在单元格末尾追加一段文字，格式沿用已有 run。"""
    p = cell.paragraphs[0]
    run = p.add_run(text)
    src = first_run(cell)
    if src is None:
        return run
    if src.font.size:
        run.font.size = src.font.size
    if src.font.name:
        run.font.name = src.font.name
        rPr = run._element.get_or_add_rPr()
        rFonts = rPr.find(qn("w:rFonts"))
        if rFonts is None:
            from docx.oxml import OxmlElement
            rFonts = OxmlElement("w:rFonts")
            rPr.append(rFonts)
        rFonts.set(qn("w:eastAsia"), src.font.name)
        rFonts.set(qn("w:ascii"), src.font.name)
        rFonts.set(qn("w:hAnsi"), src.font.name)
    if src.font.color is not None and src.font.color.rgb is not None:
        run.font.color.rgb = src.font.color.rgb
    run.font.bold = src.font.bold
    return run


def main():
    doc = Document(DOCX)
    table = doc.tables[0]

    # ---------- 1. 基本信息：去掉「作品站」，GitHub 占满右侧 ----------
    for row in list(table.rows):
        cells = unique_cells(row)
        if len(cells) >= 4 and cells[0].text.strip() == "GitHub":
            url = cells[1].text.strip()
            merged = cells[1].merge(cells[3])
            write_cell(merged, url)
            print(f"[基本信息] 删除「作品站」，GitHub 合并为全宽: {url}")
            break

    # ---------- 2. 教育背景：删除「补充信息」占位行 ----------
    for row in list(table.rows):
        cells = unique_cells(row)
        if cells and cells[0].text.strip() == "补充信息" and any("GPA" in c.text for c in cells):
            row._tr.getparent().remove(row._tr)
            print("[教育背景] 删除「补充信息」占位行")
            break

    # ---------- 3. 删除「其他」整节 ----------
    rows = list(table.rows)
    idx = None
    for i, row in enumerate(rows):
        cells = unique_cells(row)
        if len(cells) == 1 and cells[0].text.strip() == "其他":
            idx = i
            break
    if idx is not None:
        removed = 0
        for row in rows[idx:]:
            row._tr.getparent().remove(row._tr)
            removed += 1
        print(f"[其他] 删除整节，共 {removed} 行")

    # ---------- 4. 英语六级：在「主修课程」后插入一行 ----------
    src = None
    for row in table.rows:
        cells = unique_cells(row)
        if len(cells) >= 2 and cells[0].text.strip() == "主修课程":
            src = row
            break
    if src is not None:
        new_tr = copy.deepcopy(src._tr)
        src._tr.addnext(new_tr)
        new_row = _Row(new_tr, table)
        cells = unique_cells(new_row)
        write_cell(cells[0], "英语水平")
        write_cell(cells[-1], "CET-6（英语六级）")
        print("[教育背景] 主修课程后新增「英语水平 / CET-6」")

    # ---------- 5. 技术栈补 GitHub 链接 ----------
    targets = [
        ("Unity 2022.3", f"{GITHUB}/MyFrame"),
        ("JobSystem", f"{GITHUB}/ColliderSystem"),
    ]
    for row in table.rows:
        cells = unique_cells(row)
        if len(cells) >= 2 and cells[0].text.strip() == "技术栈":
            body = cells[-1]
            text = body.text
            for key, url in targets:
                if key in text and url not in text:
                    append_run_like(body, f"  ｜  {url}")
                    print(f"[{key}] 技术栈补链接: {url}")
                    break

    doc.save(DOCX)

    # ---------- 校验 ----------
    print("\n=== 修改后 ===")
    doc2 = Document(DOCX)
    for i, row in enumerate(doc2.tables[0].rows):
        cells = unique_cells(row)
        print(f"{i:02d} | " + " || ".join(c.text.replace("\n", " / ")[:70] for c in cells))


if __name__ == "__main__":
    sys.exit(main())
