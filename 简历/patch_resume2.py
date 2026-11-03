# -*- coding: utf-8 -*-
"""修正 GitHub 地址；把 ARPG 段落改写为「完整游戏流程」叙述。"""

import copy
import sys

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

DOCX = r"E:\个人作品网站\简历\简历-客户端开发.docx"

OLD_LOGIN = "AKI12345"
NEW_LOGIN = "AKI12345asa"

BULLETS = [
    (None,
     "打通完整游戏闭环：主菜单 → 建角（外观装配）→ 场景异步加载 → 战斗 / 探索 → 对话接取任务 → "
     "背包 / 装备 / 商店 → 存档 → 返回主菜单，流程可反复进入，场景之间用返回点与自动存档衔接。"),
    ("配置驱动的内容扩展",
     "：角色、敌人、物品、任务、场景统一抽象为配置资产，新增职业 / 敌人 / 物品 / 任务靠配表完成而不改代码；"
     "技能、GOAP、对话树、UI 窗口均由框架的特性 + 反射机制自动注册，业务层只负责填内容。"),
    ("聚合式存档",
     "：存档系统只负责序列化，各业务模块（玩家、任务、NPC、商店）在自己的回调里保存自己那一段，"
     "新增要存档的系统不需要改存档代码；自动存档挂在切场景钩子上，配合手动槽位与读档恢复。"),
    ("任务与对话打通",
     "：任务参数区分自动完成与交付完成，对话树里可直接挂接取 / 完成 / 条件判断节点；"
     "NPC 参数按场景隔离并持久化，同名 NPC 在不同场景互不影响。"),
    ("操作与表现收口",
     "：窗口按四层 Layout 管理遮罩与互斥，打开窗口自动锁角色操作与相机；"
     "交互选中用射线 + Bounds 求交 + 角度筛选，描边走 CommandBuffer 蒙版而非 URP Renderer Feature。"),
    (None,
     "项目复盘后将可复用部分抽象为 MyFrame 并重写战斗层，即上述前两个项目。"),
]


def unique_cells(row):
    seen, out = set(), []
    for c in row.cells:
        if id(c._tc) in seen:
            continue
        seen.add(id(c._tc))
        out.append(c)
    return out


def build_paragraph(template_el, bullet_rpr, body_rpr, lead, rest):
    p = copy.deepcopy(template_el)
    for r in p.findall(qn("w:r")):
        p.remove(r)

    def make_run(rpr, text, bold=False):
        r = OxmlElement("w:r")
        rpr_copy = copy.deepcopy(rpr) if rpr is not None else OxmlElement("w:rPr")
        if bold and rpr_copy.find(qn("w:b")) is None:
            rpr_copy.insert(0, OxmlElement("w:b"))
        r.append(rpr_copy)
        t = OxmlElement("w:t")
        t.set(qn("xml:space"), "preserve")
        t.text = text
        r.append(t)
        return r

    p.append(make_run(bullet_rpr, "• "))
    if lead:
        p.append(make_run(body_rpr, lead, bold=True))
    p.append(make_run(body_rpr, rest))
    return p


def main():
    doc = Document(DOCX)
    table = doc.tables[0]

    # ---------- 1. 修正 GitHub 用户名 ----------
    hits = 0
    for row in table.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                for run in p.runs:
                    if OLD_LOGIN in run.text and NEW_LOGIN not in run.text:
                        run.text = run.text.replace(OLD_LOGIN, NEW_LOGIN)
                        hits += 1
    print(f"[GitHub] 替换 {hits} 处 {OLD_LOGIN} -> {NEW_LOGIN}")

    # ---------- 2. 重写 ARPG 段落 ----------
    target = None
    for row in table.rows:
        cells = unique_cells(row)
        if cells[0].text.strip() == "主要工作" and "复盘" in cells[-1].text:
            target = cells[-1]
            break
    if target is None:
        print("[ARPG] 未找到目标单元格")
        return 1

    template_el = copy.deepcopy(target.paragraphs[0]._element)
    runs = template_el.findall(qn("w:r"))
    bullet_rpr = runs[0].find(qn("w:rPr")) if runs else None
    body_rpr = runs[1].find(qn("w:rPr")) if len(runs) > 1 else bullet_rpr

    for p in target.paragraphs:
        p._element.getparent().remove(p._element)

    prev = None
    for lead, rest in BULLETS:
        new_p = build_paragraph(template_el, bullet_rpr, body_rpr, lead, rest)
        if prev is None:
            target._tc.append(new_p)
        else:
            prev.addnext(new_p)
        prev = new_p
    print(f"[ARPG] 重写为 {len(BULLETS)} 条")

    doc.save(DOCX)

    # ---------- 校验 ----------
    doc2 = Document(DOCX)
    rows = doc2.tables[0].rows
    print(f"rows={len(rows)}")
    for i, r in enumerate(rows):
        cs = unique_cells(r)
        txt = " || ".join(c.text.replace("\n", " / ")[:80] for c in cs)
        if i >= 27 or "github" in txt.lower():
            print(f"{i:02d} | {txt}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
