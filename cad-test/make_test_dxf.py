#!/usr/bin/env python3
"""CAD 能力验证: 生成 1000mm x 500mm 矩形 + 中心线 + 尺寸标注的 DXF"""
import ezdxf
from ezdxf.enums import TextEntityAlignment

W, H = 1000.0, 500.0
out = "/home/ubuntu/.openclaw/workspace/cad-test/test.dxf"

import os
os.makedirs(os.path.dirname(out), exist_ok=True)

doc = ezdxf.new("R2010", setup=False)
msp = doc.modelspace()

# 图层
doc.layers.new("OUTLINE", dxfattribs={"color": 7})
doc.layers.new("CENTER", dxfattribs={"color": 1, "linetype": "CENTER"})
doc.layers.new("DIM", dxfattribs={"color": 3})
doc.layers.new("TEXT", dxfattribs={"color": 2})

# 矩形 (0,0) 到 (1000,500)
msp.add_lwpolyline(
    [(0, 0), (W, 0), (W, H), (0, H)],
    close=True,
    dxfattribs={"layer": "OUTLINE"},
)

# 中心线
msp.add_line((-100, H / 2), (W + 100, H / 2), dxfattribs={"layer": "CENTER"})
msp.add_line((W / 2, -100), (W / 2, H + 100), dxfattribs={"layer": "CENTER"})

# 尺寸标注
dimstyle = doc.dimstyles.new("TESTDIM")
dimstyle.dxf.dimdec = 0
dimstyle.dxf.dimtxt = 25
dimstyle.dxf.dimasz = 15
dimstyle.dxf.dimexe = 5
dimstyle.dxf.dimexo = 5
dimstyle.dxf.dimgap = 3

# 宽度 1000 (底部)
msp.add_linear_dim(
    base=(W / 2, -60),
    p1=(0, 0),
    p2=(W, 0),
    dimstyle="TESTDIM",
    override={"layer": "DIM", "dimtxt": 30},
).render()

# 高度 500 (右侧)
msp.add_linear_dim(
    base=(W + 60, H / 2),
    p1=(W, 0),
    p2=(W, H),
    angle=90,
    dimstyle="TESTDIM",
    override={"layer": "DIM", "dimtxt": 30},
).render()

# 文字
msp.add_text("1000 x 500 mm", height=40, dxfattribs={"layer": "TEXT"}).set_placement(
    (W / 2, H / 2),
    align=TextEntityAlignment.MIDDLE_CENTER,
)

doc.saveas(out)
print(f"DXF saved: {out}")

# ===== 验证: 重新打开并检查结构 =====
doc2 = ezdxf.readfile(out)
msp2 = doc2.modelspace()
layers = [l.dxf.name for l in doc2.layers]
entities = list(msp2)
types = {}
for e in entities:
    types[e.dxftype()] = types.get(e.dxftype(), 0) + 1
print(f"Layers: {layers}")
print(f"Entity types: {types}")

assert "OUTLINE" in layers and "CENTER" in layers and "DIM" in layers and "TEXT" in layers, "missing layers"
assert any(e.dxftype() == "LWPOLYLINE" for e in entities), "missing rectangle"
assert types.get("LINE", 0) >= 2, "missing center lines"
assert types.get("DIMENSION", 0) == 2, f"missing/extra dimensions: {types}"
print("VERIFY OK: 文件可重读, 图层/几何/标注齐全")
