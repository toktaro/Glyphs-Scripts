# MenuTitle: Fit Metrics to SB Anchors
# -*- coding: utf-8 -*-
from GlyphsApp import *
import vanilla

class FitMetricsWindow(object):
    def __init__(self):
        # ウィンドウ作成
        self.w = vanilla.FloatingWindow(
            (220, 160),  # 幅, 高さ
            "Fit Metrics to Anchors"
        )
        
        # ボタン配置
        self.w.checkAnchorPairs = vanilla.Button(
            (10, 10, -10, 30),
            "Check Anker Pairs",
            callback=self.checkAnchorPairs
        )
        self.w.fitHeight = vanilla.Button(
            (10, 50, -10, 30),
            "Fit Height (TSB / BSB)",
            callback=self.fitHeightCallback
        )
        self.w.fitWidth = vanilla.Button(
            (10, 80, -10, 30),
            "Fit Width (LSB / RSB)",
            callback=self.fitWidthCallback
        )
        self.w.closeButton = vanilla.Button(
            (10, 130, -10, 20),
            "Close",
            callback=self.closeCallback
        )
        
        self.w.open()

    def checkAnchorPairs(self, sender):
        font = Glyphs.font
        layers = font.selectedLayers
        
        missingPairs = []
        
        for layer in layers:
            glyph = layer.parent
            anchors = layer.anchors
            
            has_TSB = anchors["TSB"] is not None
            has_BSB = anchors["BSB"] is not None
            has_LSB = anchors["LSB"] is not None
            has_RSB = anchors["RSB"] is not None
            
            problems = []
            if not (has_TSB and has_BSB):
                problems.append("TSB/BSB")
            if not (has_LSB and has_RSB):
                problems.append("LSB/RSB")
            
            if problems:
                missingPairs.append(f"{glyph.name}: missing {', '.join(problems)}")
        
        # 結果まとめ
        if missingPairs:
            msg = "⚠️ Missing anchor pairs:\n\n" + "\n".join(missingPairs)
        else:
            msg = "✅ All selected glyphs contain both anchor pairs."
        
        # GlyphsApp の Message を使う
        Message(
            title="Anchor Pair Checker",
            message=msg,
            OKButton="OK"
        )
    
    def fitHeightCallback(self, sender):
        for thisLayer in Glyphs.font.selectedLayers:
            tsb_anchor = thisLayer.anchors["TSB"]
            bsb_anchor = thisLayer.anchors["BSB"]

            bounds = thisLayer.bounds
            top_edge = bounds.origin.y + bounds.size.height
            bottom_edge = bounds.origin.y
   
            thisLayer.TSB = tsb_anchor.position.y - top_edge
            thisLayer.BSB = bottom_edge - bsb_anchor.position.y
    
    def fitWidthCallback(self, sender):
        for thisLayer in Glyphs.font.selectedLayers:
            lsb_anchor = thisLayer.anchors["LSB"]
            rsb_anchor = thisLayer.anchors["RSB"]

            bounds = thisLayer.bounds
            right_edge = bounds.origin.x + bounds.size.width
            left_edge = bounds.origin.x
   
            thisLayer.RSB = rsb_anchor.position.x - right_edge
            thisLayer.LSB = left_edge - lsb_anchor.position.x
    
    def closeCallback(self, sender):
        self.w.close()

FitMetricsWindow()
