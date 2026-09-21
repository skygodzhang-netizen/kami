#!/usr/bin/env python3
"""法兰盘 CAD 生成: 外径100mm, 中心孔φ20, 6xφ10均布(孔圈φ80), 输出 DXF"""
import ezdxf
import math

OUT = "/home/ubuntu/.openclaw/workspace/cad-test/flange.dxf"

# 设计参数
OD_R = 50.0        # 外径 R50 (直径100)
CTR_R = 10.0       # 中心孔 R10 (φ20)
BOLT_R = 5.0       # 螺栓孔 R5 (φ10), 6个
PCD_R = 40.0       # 孔圈 R40 (φ80)
N_BOLTS = 6

doc = ezdxf.new("R2010", setup=False)
msp = doc.modelspace()

# 图层
doc.layers.new("FLANGE_OUT", dxfattribs={"color": 7})
doc.layers.new("HOLE_CTR", dxfattribs={"color": 1})
doc.layers.new("BOLT_HOLES", dxfattribs={"color": 2})
doc.layers.new("CENTERLINES", dxfattribs={"color": 1, "linetype": "CENTER"})

# 中心线 (水平+垂直, 加长)
cl_ext = 60.0
msp.add_line((-cl_ext, 0), (OD_R + cl_ext, 0), dxfattribs={"layer": "CENTERLINES"})
msp.add_line((0, -cl_ext), (0, OD_R + cl_ext), dxfattribs={"layer": "CENTERLINES"})

# 外径圆
msp.add_circle((0, 0), OD_R, dxfattribs={"layer": "FLANGE_OUT"})

# 中心孔
msp.add_circle((0, 0), CTR_R, dxfattribs={"layer": "HOLE_CTR"})

# 6个螺栓孔 (均布, 从0度起每60度)
for i in range(N_BOLTS):
    ang = math.radians(i * 360.0 / N_BOLTS)
    cx = PCD_R * math.cos(ang)
    cy = PCD_R * math.sin(ang)
    msp.add_circle((cx, cy), BOLT_R, dxfattribs={"layer": "BOLT_HOLES"})
    # 各螺栓孔的中心线 (过圆心到中心)
    msp.add_line((0, 0), (cx, cy), dxfattribs={"layer": "CENTERLINES"})

# 孔圈 (PCC 定位圆, 虚线/中心线层)
msp.add_circle((0, 0), PCD_R, dxfattribs={"layer": "CENTERLINES"})

# 尺寸标注
doc.dimstyles.new("FLANGE_DIM")
dim = doc.dimstyles.get("FLANGE_DIM")
dim.dxf.dimtxt = 8
dim.dxf.dimasz = 5
dim.dxf.dimexe = 2
dim.dxf.dimexo = 2
dim.dxf.dimgap = 1

# 外径标注 (45度方向放射线标注, 简化: 用半径文字代替)
msp.add_text(f"Φ100 (OD)", height=8, dxfattribs={"layer": "FLANGE_OUT", "color": 3}).set_placement((OD_R+5, OD_R+5))
msp.add_text(f"6×Φ10 on PCD Φ80", height=8, dxfattribs={"layer": "BOLT_HOLES", "color": 4}).set_placement((-OD_R, OD_R+5))
msp.add_text(f"CTR φ20", height=6, dxfattribs={"layer": "HOLE_CTR", "color": 5}).set_placement((0, -OD_R-5))

doc.saveas(OUT)
print(f"DXF saved: {OUT}")

# 验证
doc2 = ezdxf.readfile(OUT)
msp2 = doc2.modelspace()
layers = [l.dxf.name for l in doc2.layers]
types = {}
for e in msp2:
    types[e.dxftype()] = types.get(e.dxftype(), 0) + 1
print(f"Layers: {layers}")
print(f"Entities: {types}")
assert "FLANGE_OUT" in layers and "HOLE_CTR" in layers and "BOLT_HOLES" in layers and "CENTERLINES" in layers
assert types.get("CIRCLE", 0) == 9  # 外径1 + 中心孔1 + 螺栓孔6 + PCD圆1
assert types.get("LINE", 0) == 8     # 中心线2 + 螺栓中心线6
print("FLANGE OK: 9 circles (1 OD + 1 center + 6 bolts + 1 PCD), 8 lines")
