#MenuTitle: Check & Fix GDEF Table
# -*- coding: utf-8 -*-
__doc__="""
書き出し済みフォントのGDEFテーブルを確認し、バージョン0.0の不具合を修正するスクリプト。
"""

import os
from GlyphsApp import Glyphs, GetOpenFile, GetFolder, Message

# fontToolsの読み込みチェック
try:
    from fontTools.ttLib import TTFont
except ImportError:
    Message(
        "エラー",
        "fontToolsモジュールが見つかりません。\n"
        "[ウィンドウ] > [プラグインマネージャー] > [モジュール] から\n"
        "'fontTools' をインストールして再起動してください。"
    )
    raise SystemExit

import vanilla


# GDEFバージョンの定数
GDEF_VERSIONS = {
    0x00000000: "0.0（不正）",
    0x00010000: "1.0",
    0x00010002: "1.2",
    0x00010003: "1.3",
}


def get_version_label(version_int):
    """バージョン整数値を表示用ラベルに変換する"""
    return GDEF_VERSIONS.get(version_int, f"不明（{hex(version_int)}）")


def detect_correct_version(gdef_table):
    """GDEFテーブルの内容から正しいバージョンを判定する"""
    # バリアブルフォント（VarStore あり）→ 1.3
    if hasattr(gdef_table, "VarStore") and gdef_table.VarStore is not None:
        return 0x00010003
    # MarkGlyphSetsDef あり → 1.2
    elif hasattr(gdef_table, "MarkGlyphSetsDef") and gdef_table.MarkGlyphSetsDef is not None:
        return 0x00010002
    # それ以外 → 1.0
    else:
        return 0x00010000


class GDEFCheckerWindow:
    """GDEFテーブルの確認・修正ウィンドウ"""

    def __init__(self):
        # ウィンドウの初期化
        self.font_path = None
        self.font = None
        self.correct_version = None
        self.needs_fix = False

        # ウィンドウサイズ
        w_width = 480
        w_height = 340
        margin = 15
        row_height = 22
        button_width = 120
        y = margin

        self.w = vanilla.FloatingWindow(
            (w_width, w_height),
            "GDEF Table Checker",
            minSize=(w_width, w_height),
            maxSize=(w_width, w_height + 100),
        )

        # --- ファイル選択セクション ---
        self.w.fileLabel = vanilla.TextBox(
            (margin, y, -margin, row_height),
            "フォントファイル:",
            sizeStyle="small",
        )
        y += row_height + 2

        self.w.filePath = vanilla.TextBox(
            (margin, y, -margin - button_width - 10, row_height),
            "（未選択）",
            sizeStyle="small",
        )
        self.w.selectButton = vanilla.Button(
            (-margin - button_width, y, button_width, row_height),
            "ファイルを選択…",
            callback=self.selectFile_,
        )
        y += row_height + 15

        # --- 区切り線 ---
        self.w.divider1 = vanilla.HorizontalLine((margin, y, -margin, 1))
        y += 10

        # --- チェックボタン ---
        self.w.checkButton = vanilla.Button(
            (margin, y, button_width, row_height + 4),
            "チェック",
            callback=self.checkGDEF_,
        )
        self.w.checkButton.enable(False)
        y += row_height + 15

        # --- 結果表示エリア ---
        self.w.resultLabel = vanilla.TextBox(
            (margin, y, -margin, row_height),
            "結果:",
            sizeStyle="small",
        )
        y += row_height + 2

        # 結果テキストボックス（複数行）
        result_height = 80
        self.w.resultBox = vanilla.TextBox(
            (margin + 5, y, -margin, result_height),
            "",
            sizeStyle="small",
        )
        y += result_height + 15

        # --- 区切り線 ---
        self.w.divider2 = vanilla.HorizontalLine((margin, y, -margin, 1))
        y += 15

        # --- 修正・閉じるボタン ---
        self.w.fixButton = vanilla.Button(
            (margin, y, button_width, row_height + 4),
            "修正して保存",
            callback=self.fixGDEF_,
        )
        self.w.fixButton.enable(False)

        self.w.closeButton = vanilla.Button(
            (-margin - button_width, y, button_width, row_height + 4),
            "閉じる",
            callback=self.closeWindow_,
        )

        # ウィンドウを表示
        self.w.open()

    def selectFile_(self, sender):
        """ファイル選択ダイアログを表示する"""
        file_path = GetOpenFile(
            message="GDEFを確認するフォントファイルを選択",
            allowsMultipleSelection=False,
            filetypes=["otf", "ttf"],
        )

        if file_path:
            self.font_path = file_path
            # ファイル名のみ表示（パスが長い場合）
            filename = os.path.basename(file_path)
            self.w.filePath.set(filename)
            self.w.checkButton.enable(True)
            # 前回の結果をクリア
            self.w.resultBox.set("")
            self.w.fixButton.enable(False)
            self.needs_fix = False

    def checkGDEF_(self, sender):
        """GDEFテーブルをチェックする"""
        if not self.font_path:
            return

        try:
            # フォントを読み込む
            self.font = TTFont(self.font_path)

            if "GDEF" not in self.font:
                # GDEFテーブルが存在しない
                result = "GDEFテーブル: なし\n\n修正の必要はありません。"
                self.w.resultBox.set(result)
                self.w.fixButton.enable(False)
                self.needs_fix = False
                return

            gdef_table = self.font["GDEF"].table
            current_version = getattr(gdef_table, "Version", None)
            current_label = get_version_label(current_version) if current_version is not None else "取得不可"

            # 正しいバージョンを判定
            self.correct_version = detect_correct_version(gdef_table)
            correct_label = get_version_label(self.correct_version)

            if current_version == 0x00000000:
                # 不正なバージョン → 修正が必要
                result = (
                    f"GDEFテーブル: あり\n"
                    f"現在のバージョン: {current_label} ⚠️\n"
                    f"修正後のバージョン: {correct_label}\n\n"
                    f"「修正して保存」で修正できます。"
                )
                self.w.fixButton.enable(True)
                self.needs_fix = True
            elif current_version in (0x00010000, 0x00010002, 0x00010003):
                # 正常なバージョン
                result = (
                    f"GDEFテーブル: あり\n"
                    f"現在のバージョン: {current_label} ✅\n\n"
                    f"正常です。修正の必要はありません。"
                )
                self.w.fixButton.enable(False)
                self.needs_fix = False
            else:
                # 不明なバージョン
                result = (
                    f"GDEFテーブル: あり\n"
                    f"現在のバージョン: {current_label} ⚠️\n"
                    f"推奨バージョン: {correct_label}\n\n"
                    f"「修正して保存」で修正できます。"
                )
                self.w.fixButton.enable(True)
                self.needs_fix = True

            self.w.resultBox.set(result)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.w.resultBox.set(f"エラー: {str(e)}")
            self.w.fixButton.enable(False)

    def fixGDEF_(self, sender):
        """GDEFテーブルのバージョンを修正し、fixed_GDEFフォルダに保存する"""
        if not self.font or not self.needs_fix or self.correct_version is None:
            return

        try:
            # バージョンを修正
            gdef_table = self.font["GDEF"].table
            old_version = getattr(gdef_table, "Version", 0)
            gdef_table.Version = self.correct_version

            # 出力先フォルダの作成
            font_dir = os.path.dirname(self.font_path)
            output_dir = os.path.join(font_dir, "fixed_GDEF")
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # 元のファイル名で保存
            filename = os.path.basename(self.font_path)
            output_path = os.path.join(output_dir, filename)

            self.font.save(output_path)

            # 結果表示
            old_label = get_version_label(old_version)
            new_label = get_version_label(self.correct_version)
            result = (
                f"✅ 修正完了\n"
                f"バージョン: {old_label} → {new_label}\n"
                f"保存先: fixed_GDEF/{filename}"
            )
            self.w.resultBox.set(result)
            self.w.fixButton.enable(False)
            self.needs_fix = False

            # マクロパネルにもログ出力
            print(f"GDEF修正完了: {old_label} → {new_label}")
            print(f"保存先: {output_path}")

            # 完了メッセージ
            Message(
                "修正完了",
                f"GDEFバージョンを {new_label} に修正しました。\n\n"
                f"保存先:\n{output_path}"
            )

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.w.resultBox.set(f"保存エラー: {str(e)}")
            Message("エラー", f"保存中にエラーが発生しました:\n{str(e)}")

    def closeWindow_(self, sender):
        """ウィンドウを閉じる"""
        # フォントオブジェクトを解放
        if self.font:
            self.font.close()
            self.font = None
        self.w.close()


# スクリプト実行
GDEFCheckerWindow()
