# -*- coding: utf-8 -*-
"""生成表格式简历（docx）与纯文本版（md），单一数据源。"""

import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

OUT_DIR = Path(r"E:\个人作品网站\简历")
DOCX = OUT_DIR / "简历-客户端开发.docx"
MD = OUT_DIR / "简历-客户端开发.md"

FONT = "微软雅黑"
MONO = "Consolas"
BODY = 9.5
GRAY = RGBColor(0x5A, 0x5A, 0x5A)
INK = RGBColor(0x1A, 0x1A, 0x1A)
ACCENT = RGBColor(0xB4, 0x53, 0x09)

# ---------------------------------------------------------------- 内容数据

NAME = "【姓名】"
INTENT = "Unity 客户端开发（实习 / 校招）"

BASIC = [
    ("姓　　名", NAME, "求职意向", INTENT),
    ("手　　机", "【手机号】", "电子邮箱", "【邮箱】"),
    ("GitHub", "github.com/【账号】", "作品站", "【可选】"),
]

EDU_ROWS = [
    ("起止时间", "【20XX.09 – 20XX.06】"),
    ("学　　校", "【学校】"),
    ("专　　业", "【专业】"),
    ("学　　历", "【本科 / 硕士】"),
    ("主修课程", "数据结构与算法、计算机图形学、操作系统、线性代数"),
    ("补充信息", "【可选：GPA / 专业排名 / 奖学金，无则删除本行】"),
]

SKILLS = [
    ("语言与引擎",
     "C#（主力）、C++（能读能改）、Lua（了解）；Unity 2022 LTS，熟悉 URP、Addressables、"
     "Cinemachine、Odin Inspector、UniTask；熟悉 Unity 生命周期、协程与异步。"),
    ("架构能力",
     "能独立设计并落地分层框架（框架 / 业务 / 配置三层），熟悉配置驱动、接口隔离、对象池、"
     "事件系统、状态机，以及**优先级抢占式行为仲裁**。"),
    ("性能与内存",
     "熟悉 GC 来源与优化手段、托管与原生内存边界；熟练使用 `NativeArray` / `NativeStream` / "
     "JobSystem + Burst；有结构体 SoA 布局、避免每帧分配、原生容器生命周期与引用计数的实践经验。"),
    ("底层与算法",
     "手写 GJK / EPA 凸体碰撞检测、Morton 码 LBVH、两层 BVH 空间加速；"
     "理解坐标变换、支撑函数与 Minkowski 差。"),
    ("工具链",
     "能写编辑器扩展（技能时间轴编辑器、GOAP 编辑器、节点树编辑器），"
     "熟悉 Odin 多态序列化与资产化配置。"),
    ("工程素养",
     "关注原生内存泄漏、配置健壮性、大文件拆分；有把设计沉淀成文档的习惯。"),
]

PROJECTS = [
    {
        "name": "MyFrame",
        "role": "独立开发",
        "stack": "C# · Unity 2022.3 · URP · Addressables · Cinemachine · Odin · UniTask"
                 " ｜ 206 个脚本 / 约 2.4 万行",
        "bullets": [
            "从零设计并实现 **10 个子系统**（动画、技能、战斗、GOAP、节点树、对象池、UI、事件、"
            "存档、时间），全部收敛在单一 asmdef 内，业务层不依赖任何第三方框架。",
            "**动画系统**：放弃 Animator Controller，改用 Playable 手动编排——转场逻辑写在脚本里"
            "便于调试；片段与混合数据独立成配置便于复用；提供统一动画事件与可跨节点类型混排的 "
            "`AnimationChain`。",
            "**技能系统**：把配置里的每个数据都视为“某一帧触发的事件”，用累计时间推进时间轴而非"
            "帧计数，一次 Update 可推进多个逻辑帧，使技能表现与帧率解耦。",
            "**GOAP**：实现 AND/OR 树搜索而非 A*——启发函数取“最便宜前置条件满足者代价之和”，"
            "效果匹配采用乐观判定；在短规划生命周期、高决策频率的场景下优先保证可解释性与可视化调试。",
            "**节点树**：框架只提供链路与编辑器、不内置执行器，执行语义交由使用方实现"
            "（在 ARPG 项目中以 NPC 对话树落地验证）。",
        ],
    },
    {
        "name": "ARPG 战斗原型",
        "role": "独立开发",
        "stack": "C# · Unity · MyFrame · Odin ｜ 88 个脚本 / 8,800 行",
        "bullets": [
            "在 MyFrame 之上搭建完整战斗原型：两套可插拔动作模块（自由移动 6 个状态、剑盾 10 个状态）、"
            "9 个技能行为、锁定相机、以及 GOAP 驱动的敌人 AI。",
            "**优先级抢占式行为仲裁**：用 `struct` 描述一次行为申请（动作 / 优先级 / 检查函数 / ID），"
            "handler 走对象池，使“切状态”这一高频操作几乎零分配；高优先级可打断低优先级，"
            "同时支持用检查函数让“条件满足”覆盖“优先级更高”。",
            "**状态与外部解耦**：状态自身持续持有行为槽位，外部可用不同 behaviour 借入；"
            "当被低优先级行为占用时，状态能凭自身占位重新夺回，避免优先级反转。",
            "**技能与输入解耦**：按键只负责 `ReleaseSkill(KeyData)`，具体释放哪个技能由配置决定，"
            "因此同一套输入代码可适配不同武器。",
            "**表现层注册制**：相机与打击检测以处理器形式在角色初始化时注册"
            "（玩家 6 个相机处理器 + 5 个检测处理器，敌人按需），"
            "同一份技能配置在不同角色上表现不同，无需修改技能数据。",
        ],
    },
    {
        "name": "自定义碰撞检测系统",
        "role": "独立开发",
        "stack": "C# · JobSystem · Burst · NativeContainer · unsafe"
                 " ｜ 25 个脚本 / 5,300 行 / 12 处 `[BurstCompile]`",
        "bullets": [
            "从零实现凸体碰撞系统，完整覆盖物理管线四段：**实体收集 → 粗筛 → 精算 → 求解与事件**。",
            "**粗筛**：基于 Morton 码排序构建 LBVH（线性 BVH），天然适合并行；"
            "网格三角形另外维护本地 BVH 并做引用计数缓存，与物体级顶层 BVH 组成两层结构。",
            "**精算**：手写 GJK 判交与 EPA 求穿透深度，按“点集 / 三角形 / 盒 / 球 / 胶囊”的组合"
            "提供多套支撑函数重载。",
            "**并行**：全流程跑在 JobSystem + Burst 上；用 `NativeStream` 收集并行结果避免写竞争，"
            "用 `IJobParallelForTransform` 并行回写变换。",
            "**事件与求解**：双缓冲 `HashSet` 对比前后两帧碰撞对，无分配地判定 Trigger 的 "
            "Enter / Stay / Exit；MTV 按逆质量加权分配，使重的一方位移更小。",
            "**内存治理**：把实体与包围盒数组改为容量池 + 逻辑计数，所有 Job 只接收 "
            "`GetSubArray(0, count)` 视图，杜绝“把容量当成物体数量”；补齐 `Dispose` 与运行时"
            "生命周期钩子，使 Persistent 原生内存在退出时零泄漏。",
        ],
    },
    {
        "name": "ARPG 原型（早期版本）",
        "role": "独立开发",
        "stack": "C# · Unity ｜ 194 个脚本",
        "bullets": [
            "手写状态机、技能、背包、商店、任务与对话，跑通完整流程。",
            "**对话系统**：用节点树搭建——顺序执行器与分支执行器作为结构节点，显示对话、任务、"
            "条件判断作为动作节点；节点以 `async Task<NodeState> Execute()` 递归执行，"
            "用 `SemaphoreSlim` 把“等待玩家点击”变成 `await` 而非状态机轮询。",
            "**选项可见性由节点自述**：执行前由各选项节点自行判断条件与任务是否满足并过滤，"
            "避免在对话流程里硬编码业务规则。",
            "**UI 架构**：窗口 / 控件 / 数据三层分离，控件通过回调注入业务、不引用任何 Manager，"
            "使背包、装备、商店复用同一套槽位组件。",
            "项目复盘后将可复用部分抽象为 MyFrame 并重写战斗层，即上述前两个项目。",
        ],
    },
]

OTHERS = [
    ("设计文档", "框架设计文档 11 篇，架构图与流程图 9 张。"),
    ("补充信息", "【英语水平、竞赛获奖、开源仓库链接，无则删除本行】"),
]

# ---------------------------------------------------------------- 通用工具

INLINE = re.compile(r"(\*\*.+?\*\*|`.+?`|【.+?】)")


def _font(run, name, size, bold, color):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    if color is not None:
        run.font.color.rgb = color
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    for attr in ("w:eastAsia", "w:ascii", "w:hAnsi"):
        rFonts.set(qn(attr), name)


def write_inline(p, text, size=BODY, bold=False, color=INK):
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            r = p.add_run(part[2:-2])
            _font(r, FONT, size, True, color)
        elif part.startswith("`") and part.endswith("`"):
            r = p.add_run(part[1:-1])
            _font(r, MONO, size - 0.5, bold, color)
        elif part.startswith("【") and part.endswith("】"):
            r = p.add_run(part)
            _font(r, FONT, size, bold, ACCENT)
        else:
            r = p.add_run(part)
            _font(r, FONT, size, bold, color)


def clear_cell(cell):
    """合并后的单元格会保留多个空段落，只留第一个。"""
    for p in cell.paragraphs[1:]:
        p._element.getparent().remove(p._element)
    p = cell.paragraphs[0]
    for r in list(p.runs):
        r._element.getparent().remove(r._element)
    return p


def fill_cell(cell, blocks, size=BODY, bold=False, color=INK, bullet=False,
              align=None):
    if isinstance(blocks, str):
        blocks = [blocks]
    for i, block in enumerate(blocks):
        p = clear_cell(cell) if i == 0 else cell.add_paragraph()
        pf = p.paragraph_format
        pf.space_before = Pt(0.4)
        pf.space_after = Pt(0.4)
        pf.line_spacing = 1.02
        if align is not None:
            p.alignment = align
        if bullet:
            pf.left_indent = Cm(0.34)
            pf.first_line_indent = Cm(-0.34)
            r = p.add_run("• ")
            _font(r, FONT, size, False, GRAY)
        write_inline(p, block, size=size, bold=bold, color=color)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER


def shade(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def set_table_borders(table, color="BFBFBF", sz="4"):
    tblPr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement("w:" + edge)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), sz)
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        borders.append(el)
    tblPr.append(borders)


def set_cell_margins(table, top=16, bottom=16, left=80, right=80):
    tblPr = table._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for name, val in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        el = OxmlElement("w:" + name)
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tblPr.append(mar)


def fixed_layout(table, widths):
    table.autofit = False
    tblPr = table._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)
    for col, w in zip(table.columns, widths):
        col.width = Cm(w)


def no_split(row):
    """保留调用点。表格行允许跨页拆分——否则整块内容会跳到下一页，留下大片空白。"""
    return


# ---------------------------------------------------------------- docx 构建

WIDTHS = [2.3, 6.5, 2.3, 6.1]  # cm，合计 17.2


def section_row(table, title):
    row = table.add_row()
    no_split(row)
    cell = row.cells[0].merge(row.cells[3])
    shade(cell, "E4E4E4")
    p = clear_cell(cell)
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(1)
    r = p.add_run(title)
    _font(r, FONT, 10.5, True, INK)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER


def kv_row(table, label, blocks, bullet=False):
    row = table.add_row()
    no_split(row)
    shade(row.cells[0], "F7F7F7")
    fill_cell(row.cells[0], label, size=9.5, color=GRAY)
    merged = row.cells[1].merge(row.cells[3])
    fill_cell(merged, blocks, bullet=bullet)


def project_head(table, name, role):
    row = table.add_row()
    no_split(row)
    for cell, text, bold, size in ((row.cells[0], "项目名称", False, 9),
                                   (row.cells[1], name, True, 10),
                                   (row.cells[2], "项目角色", False, 9),
                                   (row.cells[3], role, False, 9)):
        shade(cell, "FAFAFA")
        fill_cell(cell, text, size=size, bold=bold, color=INK if bold else GRAY)


def edu_head(table, heads):
    row = table.add_row()
    no_split(row)
    for cell, text in zip(row.cells, heads):
        shade(cell, "F7F7F7")
        fill_cell(cell, text, size=9.5, color=GRAY)


def quad_values(table, values):
    row = table.add_row()
    no_split(row)
    for cell, text in zip(row.cells, values):
        fill_cell(cell, text)


def build_docx():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.top_margin = Cm(1.2)
    sec.bottom_margin = Cm(1.0)
    sec.left_margin = Cm(1.9)
    sec.right_margin = Cm(1.9)

    normal = doc.styles["Normal"]
    normal.font.name = FONT
    normal.font.size = Pt(BODY)
    rPr = normal.element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:eastAsia"), FONT)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(NAME)
    _font(r, FONT, 20, True, INK)

    table = doc.add_table(rows=0, cols=4)
    set_table_borders(table)
    set_cell_margins(table)
    fixed_layout(table, WIDTHS)

    section_row(table, "基本信息")
    for label, value, label2, value2 in BASIC:
        row = table.add_row()
        no_split(row)
        for cell, text, is_label in ((row.cells[0], label, True),
                                     (row.cells[1], value, False),
                                     (row.cells[2], label2, True),
                                     (row.cells[3], value2, False)):
            if is_label:
                shade(cell, "F7F7F7")
            fill_cell(cell, text, size=9.5 if is_label else BODY,
                      color=GRAY if is_label else INK)

    section_row(table, "教育背景")
    for label, text in EDU_ROWS:
        kv_row(table, label, text)

    section_row(table, "专业技能")
    for label, text in SKILLS:
        kv_row(table, label, text)

    section_row(table, "项目经历")
    for proj in PROJECTS:
        project_head(table, proj["name"], proj["role"])
        kv_row(table, "技术栈", proj["stack"])
        kv_row(table, "主要工作", proj["bullets"], bullet=True)

    section_row(table, "其他")
    for label, text in OTHERS:
        kv_row(table, label, text)

    # 表格后必须有段落，压到 1pt 避免挤出一个空白页
    tail = doc.add_paragraph()
    tail.paragraph_format.space_before = Pt(0)
    tail.paragraph_format.space_after = Pt(0)
    tail.paragraph_format.line_spacing = Pt(1)
    tr = tail.add_run("\u200b")
    _font(tr, FONT, 1, False, INK)

    doc.save(DOCX)
    return DOCX


# ---------------------------------------------------------------- md 构建

def build_md():
    out = ["# " + NAME, "", "**求职意向：" + INTENT + "**", "",
           "【手机号】 ｜ 【邮箱】 ｜ github.com/【账号】 ｜ 【个人作品站（可选）】", "",
           "## 教育背景", "", ""]
    for label, text in EDU_ROWS:
        out.append("- **" + label.replace("　", "") + "**：" + text)
    out += ["", "## 专业技能", ""]
    for label, text in SKILLS:
        out.append("- **" + label + "**：" + text)
    out += ["", "## 项目经历", ""]
    for proj in PROJECTS:
        stack_parts = [s.strip() for s in proj["stack"].split("｜")]
        out += ["### " + proj["name"] + " ｜ " + proj["role"], "",
                "`" + stack_parts[0] + "` ｜ " + stack_parts[1], ""]
        for b in proj["bullets"]:
            out.append("- " + b)
        out.append("")
    out += ["## 其他", ""]
    for label, text in OTHERS:
        out.append("- **" + label + "**：" + text)
    MD.write_text("\n".join(out) + "\n", encoding="utf-8")
    return MD


if __name__ == "__main__":
    print("docx:", build_docx())
    print("md  :", build_md())
    sys.exit(0)
