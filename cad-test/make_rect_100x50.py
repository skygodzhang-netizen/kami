#!/usr/bin/env python3
import ezdxf

OUT = "/home/ubuntu/.openclaw/workspace/cad-test/rect_100x50.dxf"
W, H = 100.0, 50.0

doc = ezdxf.new("R2010", setup=False)
msp = doc.modelspace()
doc.layers.new("OUTLINE", dxfattribs={"color": 7})
doc.layers.new("CENTER", dxfattribs={"color": 1, "linetype": "CENTER"})

msp.add_lwpolyline([(0,0),(W,0),(W,H),(0,H)], close=True, dxfattribs={"layer": "OUTLINE"})
msp.add_line((-15, H/2), (W+15, H/2), dxfattribs={"layer": "CENTER"})
msp.add_line((W/2, -15), (W/2, H+15), dxfattribs={"layer": "CENTER"})
msp.add_text("100 x 50", height=8, dxfattribs={"layer": "OUTLINE"}).set_placement((W/2, H+5))

doc.saveas(OUT)
print("saved", OUT)

d2 = ezdxf.readfile(OUT)
m2 = d2.modelspace()
types = {}
for e in m2:
    types[e.dxftype()] = types.get(e.dxftype(), 0) + 1
print("entities:", types)
