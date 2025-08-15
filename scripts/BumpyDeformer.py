# MenuTitle: Bumpy Deformer
# Move Points & Handles by Formula (Realtime, Dual XY Independent k and Offsets)
# -*- coding: utf-8 -*-
from vanilla import FloatingWindow, Slider, EditText, TextBox, Button

class MovePointsDualXYIndependentUI:
    def __init__(self):
        self.font = Glyphs.font
        self.layer = self.font.selectedLayers[0]
        self.master = self.layer.master

        # 元座標
        self.original_positions = self.capturePositions()

        # 初期値
        self.ky = 0.0
        self.kx = 0.0
        self.yc_offset = 0.0
        self.xc_offset = 0.0

        # UI
        self.w = FloatingWindow((350, 200), "Bumpy Deformer")

        # ky
        self.w.text_ky = TextBox((10, 12, 80, 20), "Horizontal:")
        self.w.slider_ky = Slider((90, 10, -60, 20),
                                  minValue=-1.0, maxValue=1.0,
                                  value=self.ky, tickMarkCount=9,
                                  callback=self.updateFromUI)
        self.w.kyValue = EditText((-50, 10, -10, 20),
                                  f"{self.ky:.2f}",
                                  callback=self.updateFromText)
        
        # Yc offset
        self.w.text_yc = TextBox((10, 42, 80, 20), "H Offset")
        self.w.slider_yc = Slider((90, 40, -60, 20),
                                  minValue=-500, maxValue=500,
                                  value=self.yc_offset, tickMarkCount=11,
                                  callback=self.updateFromUI)
        self.w.ycValue = EditText((-50, 40, -10, 20),
                                  f"{self.yc_offset:.0f}",
                                  callback=self.updateFromText)
        
        # kx
        self.w.text_kx = TextBox((10, 72, 80, 20), "Vertical:")
        self.w.slider_kx = Slider((90, 70, -60, 20),
                                  minValue=-1.0, maxValue=1.0,
                                  value=self.kx, tickMarkCount=9,
                                  callback=self.updateFromUI)
        self.w.kxValue = EditText((-50, 70, -10, 20),
                                  f"{self.kx:.2f}",
                                  callback=self.updateFromText)

        # Xc offset
        self.w.text_xc = TextBox((10, 102, 80, 20), "V Offset")
        self.w.slider_xc = Slider((90, 100, -60, 20),
                                  minValue=-500, maxValue=500,
                                  value=self.xc_offset, tickMarkCount=11,
                                  callback=self.updateFromUI)
        self.w.xcValue = EditText((-50, 100, -10, 20),
                                  f"{self.xc_offset:.0f}",
                                  callback=self.updateFromText)

        # Buttons
        self.w.resetButton = Button((10, 140, 150, 20), "Reset", callback=self.resetPoints)
        self.w.applyButton = Button((-160, 140, 150, 20), "Apply", callback=self.applyChanges)

        self.w.open()

    def capturePositions(self):
        return [[(node.x, node.y) for node in path.nodes] for path in self.layer.paths]

    def restorePositions(self, positions):
        for p_idx, path in enumerate(self.layer.paths):
            for n_idx, node in enumerate(path.nodes):
                node.x, node.y = positions[p_idx][n_idx]
        self.font.currentTab.redraw()

    def calcIndependentXY(self, xa, ya, ky, kx, yc_offset, xc_offset):
        # 中心座標とハーフサイズ
        Xc = (self.layer.width / 2.0) + xc_offset
        Yc = (self.master.ascender + self.master.descender) / 2.0 + yc_offset
        Xh = (self.layer.width / 2.0)
        Yh = (self.master.ascender - self.master.descender) / 2.0

        Xa = xa - Xc
        Ya = ya - Yc

        # Y変形だけ
        y_new = Ya * (ky * Xa + Yh) / Yh + Yc
        # X変形だけ
        x_new = Xa * (kx * Ya + Xh) / Xh + Xc

        return (x_new, y_new)

    def applyTransform(self, ky, kx, yc_offset, xc_offset):
        for p_idx, path in enumerate(self.layer.paths):
            for n_idx, node in enumerate(path.nodes):
                xa, ya = self.original_positions[p_idx][n_idx]
                new_x, new_y = self.calcIndependentXY(xa, ya, ky, kx, yc_offset, xc_offset)
                node.x, node.y = new_x, new_y
        self.font.currentTab.redraw()

    def updateFromUI(self, sender):
        self.ky = self.w.slider_ky.get()
        self.kx = self.w.slider_kx.get()
        self.yc_offset = self.w.slider_yc.get()
        self.xc_offset = self.w.slider_xc.get()
        self.w.kyValue.set(f"{self.ky:.2f}")
        self.w.kxValue.set(f"{self.kx:.2f}")
        self.w.ycValue.set(f"{self.yc_offset:.0f}")
        self.w.xcValue.set(f"{self.xc_offset:.0f}")
        self.applyTransform(self.ky, self.kx, self.yc_offset, self.xc_offset)

    def updateFromText(self, sender):
        try:
            if sender == self.w.kyValue:
                val = float(sender.get()); self.ky = max(-1.0, min(1.0, val)); self.w.slider_ky.set(self.ky)
            elif sender == self.w.kxValue:
                val = float(sender.get()); self.kx = max(-1.0, min(1.0, val)); self.w.slider_kx.set(self.kx)
            elif sender == self.w.ycValue:
                val = float(sender.get()); self.yc_offset = max(-500, min(500, val)); self.w.slider_yc.set(self.yc_offset)
            elif sender == self.w.xcValue:
                val = float(sender.get()); self.xc_offset = max(-500, min(500, val)); self.w.slider_xc.set(self.xc_offset)
        except ValueError:
            return
        self.applyTransform(self.ky, self.kx, self.yc_offset, self.xc_offset)

    def resetPoints(self, sender):
        self.restorePositions(self.original_positions)
        self.ky = 0.0
        self.kx = 0.0
        self.yc_offset = 0.0
        self.xc_offset = 0.0
        self.w.slider_ky.set(self.ky); self.w.kyValue.set(f"{self.ky:.2f}")
        self.w.slider_kx.set(self.kx); self.w.kxValue.set(f"{self.kx:.2f}")
        self.w.slider_yc.set(self.yc_offset); self.w.ycValue.set(f"{self.yc_offset:.0f}")
        self.w.slider_xc.set(self.xc_offset); self.w.xcValue.set(f"{self.xc_offset:.0f}")

    def applyChanges(self, sender):
        self.original_positions = self.capturePositions()
        print(f"確定しました (ky={self.ky:.2f}, kx={self.kx:.2f}, Yc+={self.yc_offset:.0f}, Xc+={self.xc_offset:.0f})")
        self.w.close()

MovePointsDualXYIndependentUI()
