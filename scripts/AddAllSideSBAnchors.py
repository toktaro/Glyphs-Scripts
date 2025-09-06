#MenuTitle: Add All Side SB Anchors
# -*- coding: utf-8 -*-
__doc__="""
Adds TSB, BSB, LSB, and RSB anchors to selected layers.
A dialog prompts for offsets and positioning mode (from glyph bounds or metrics center).
If an offset is not provided, the corresponding anchors will not be added.
Remembers the last used values.
Rounds anchor coordinates to the nearest integer.
"""

import GlyphsApp
from Foundation import NSPoint
from vanilla import *

class AddAllSideAnchors(object):
    pref_h = "com.toktaro.AddAllSideAnchors.h_offset"
    pref_v = "com.toktaro.AddAllSideAnchors.v_offset"
    pref_mode = "com.toktaro.AddAllSideAnchors.mode"

    def __init__(self):
        self.font = Glyphs.font
        if not self.font:
            print("Error: No font open.")
            return

        self.selected_layers = self.font.selectedLayers
        if not self.selected_layers:
            Glyphs.showMacroWindow()
            print("No layers selected. Please select one or more glyphs in the Font View or open a glyph for editing.")
            return

        h_default = Glyphs.defaults[self.pref_h]
        if h_default is None:
            h_default = "50"
        
        v_default = Glyphs.defaults[self.pref_v]
        if v_default is None:
            v_default = "50"
        
        mode_default = Glyphs.defaults[self.pref_mode]
        if mode_default is None:
            mode_default = 0 

        # --- UI ---
        window_height = 200
        self.w = Window((320, window_height), "Add All Side Anchors")
        
        y_pos = 15
        self.w.text_v = TextBox((15, y_pos, 160, 14), "Vertical Offset (T/B):")
        self.w.offset_v = EditText((190, y_pos - 3, 110, 21), v_default)
        
        y_pos += 30
        self.w.text_h = TextBox((15, y_pos, 160, 14), "Horizontal Offset (L/R):")
        self.w.offset_h = EditText((190, y_pos - 3, 110, 21), h_default)

        y_pos += 40
        self.w.mode_text = TextBox((15, y_pos, 160, 20), "Positioning Mode:")
        y_pos += 20
        self.w.placementMode = RadioGroup((25, y_pos, -15, 45), 
                                          ["From Glyph Bounds (字形の端から)", "From Metrics Center (仮想ボディ中央から)"], 
                                          isVertical=True)
        self.w.placementMode.set(mode_default)
        
        y_pos = window_height - 40
        self.w.runButton = Button((15, y_pos, 140, 20), "Add Anchors", callback=self.addAnchors)
        self.w.deleteButton = Button((165, y_pos, 140, 20), "Delete Anchors", callback=self.deleteAnchors)
        self.w.setDefaultButton(self.w.runButton)
        
        self.w.center()
        self.w.open()

    def addAnchors(self, sender):
        h_offset_str = self.w.offset_h.get().strip()
        v_offset_str = self.w.offset_v.get().strip()
        positioning_mode = self.w.placementMode.get()

        Glyphs.defaults[self.pref_h] = h_offset_str
        Glyphs.defaults[self.pref_v] = v_offset_str
        Glyphs.defaults[self.pref_mode] = positioning_mode

        h_offset = None
        v_offset = None

        try:
            if h_offset_str: h_offset = int(h_offset_str)
            if v_offset_str: v_offset = int(v_offset_str)
        except ValueError:
            print("Error: Invalid offset. Please enter numbers only.")
            return

        if h_offset is None and v_offset is None:
            print("No offsets entered. Nothing to do.")
            self.w.close()
            return

        self.w.close()
        print(f"Processing {len(self.selected_layers)} selected layer(s)...")
        self.font.disableUpdateInterface()

        try:
            for layer in self.selected_layers:
                glyph_name = layer.parent.name
                layer_name = layer.name
                print(f"Processing glyph: '{glyph_name}', layer: '{layer_name}'")

                if not layer.paths and not layer.components:
                    print(f"  -> Skipped (empty layer).")
                    continue

                added_anchors = []

                # --- モードに応じて基準点を設定 ---
                if positioning_mode == 0: # From Glyph Bounds
                    bounds = layer.bounds
                    left_edge = bounds.origin.x
                    right_edge = bounds.origin.x + bounds.size.width
                    bottom_edge = bounds.origin.y
                    top_edge = bounds.origin.y + bounds.size.height
                    center_x = left_edge + bounds.size.width / 2.0
                    center_y = bottom_edge + bounds.size.height / 2.0
                else: # From Metrics Center
                    master = layer.master
                    center_x = layer.width / 2.0
                    center_y = (master.ascender + master.descender) / 2.0
                
                # Horizontal anchors (LSB, RSB)
                if h_offset is not None:
                    if layer.anchors["LSB"]: del(layer.anchors["LSB"])
                    if layer.anchors["RSB"]: del(layer.anchors["RSB"])
                    
                    if positioning_mode == 0: # From Glyph Bounds
                        lsb_x = left_edge - h_offset
                        rsb_x = right_edge + h_offset
                    else: # From Metrics Center
                        lsb_x = center_x - h_offset
                        rsb_x = center_x + h_offset
                        
                    lsb_pos = NSPoint(round(lsb_x), round(center_y))
                    rsb_pos = NSPoint(round(rsb_x), round(center_y))
                    
                    layer.anchors.append(GSAnchor("LSB", lsb_pos))
                    layer.anchors.append(GSAnchor("RSB", rsb_pos))
                    added_anchors.extend(["LSB", "RSB"])

                # Vertical anchors (TSB, BSB)
                if v_offset is not None:
                    if layer.anchors["TSB"]: del(layer.anchors["TSB"])
                    if layer.anchors["BSB"]: del(layer.anchors["BSB"])

                    if positioning_mode == 0: # From Glyph Bounds
                        tsb_y = top_edge + v_offset
                        bsb_y = bottom_edge - v_offset
                    else: # From Metrics Center
                        tsb_y = center_y + v_offset
                        bsb_y = center_y - v_offset

                    tsb_pos = NSPoint(round(center_x), round(tsb_y))
                    bsb_pos = NSPoint(round(center_x), round(bsb_y))

                    layer.anchors.append(GSAnchor("TSB", tsb_pos))
                    layer.anchors.append(GSAnchor("BSB", bsb_pos))
                    added_anchors.extend(["TSB", "BSB"])
                
                if added_anchors:
                    print(f"  -> Added/updated {', '.join(added_anchors)} anchors.")
                else:
                    print(f"  -> No new anchors added.")

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self.font.enableUpdateInterface()
            print("Done.")

        if self.font.currentTab:
            self.font.currentTab.redraw()

    def deleteAnchors(self, sender):
        self.w.close()
        print(f"Processing {len(self.selected_layers)} selected layer(s) for anchor deletion...")
        self.font.disableUpdateInterface()
        try:
            for layer in self.selected_layers:
                glyph_name = layer.parent.name
                layer_name = layer.name
                print(f"Processing glyph: '{glyph_name}', layer: '{layer_name}'")
                anchors_to_delete = [a.name for a in layer.anchors if a.name in ["LSB", "RSB", "TSB", "BSB"]]
                if anchors_to_delete:
                    print(f"  -> Deleting anchors: {', '.join(anchors_to_delete)}")
                    for anchor_name in anchors_to_delete:
                        del(layer.anchors[anchor_name])
                else:
                    print(f"  -> No side anchors found to delete.")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self.font.enableUpdateInterface()
            print("Done.")
        if self.font.currentTab:
            self.font.currentTab.redraw()

# Run the script
AddAllSideAnchors()