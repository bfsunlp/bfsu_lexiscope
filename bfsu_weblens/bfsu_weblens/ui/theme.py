# -*- coding: utf-8 -*-
"""Consistent fixed-light Qt theme for BFSU WebLens.

WebLens uses standard PySide6 widgets, but applies Qt's Fusion style together
with a complete light palette.  This avoids operating-system dark-mode colors
leaking into a warm light interface while retaining the platform UI font and
normal Qt sizing behaviour on Windows, macOS and Linux.
"""
from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from ..resources import resource_path

BG = "#F7F2EC"
CARD = "#FFFCF8"
EDITOR = "#FFFDFB"
HEADER = "#F2E2D2"
BORDER = "#D9C8B8"
TEXT = "#2D2926"
MUTED = "#746A62"
DISABLED_TEXT = "#9D948D"
ACCENT = "#C96F32"
ACCENT_HOVER = "#AD5D28"
ACCENT_SOFT = "#F4DED0"
SELECTION = "#E7C7AE"
PLACEHOLDER = "#91877F"


def _set_group(palette: QPalette, group: QPalette.ColorGroup, *, disabled: bool = False) -> None:
    foreground = QColor(DISABLED_TEXT if disabled else TEXT)
    palette.setColor(group, QPalette.ColorRole.Window, QColor(BG))
    palette.setColor(group, QPalette.ColorRole.WindowText, foreground)
    palette.setColor(group, QPalette.ColorRole.Base, QColor(EDITOR))
    palette.setColor(group, QPalette.ColorRole.AlternateBase, QColor("#FBF6F1"))
    palette.setColor(group, QPalette.ColorRole.Text, foreground)
    palette.setColor(group, QPalette.ColorRole.Button, QColor(CARD))
    palette.setColor(group, QPalette.ColorRole.ButtonText, foreground)
    palette.setColor(group, QPalette.ColorRole.Highlight, QColor(ACCENT_SOFT))
    palette.setColor(group, QPalette.ColorRole.HighlightedText, QColor(TEXT))
    palette.setColor(group, QPalette.ColorRole.ToolTipBase, QColor(CARD))
    palette.setColor(group, QPalette.ColorRole.ToolTipText, QColor(TEXT))
    palette.setColor(group, QPalette.ColorRole.PlaceholderText, QColor(PLACEHOLDER))
    palette.setColor(group, QPalette.ColorRole.BrightText, QColor(TEXT))
    palette.setColor(group, QPalette.ColorRole.Light, QColor("#FFFFFF"))
    palette.setColor(group, QPalette.ColorRole.Midlight, QColor("#EEE2D7"))
    palette.setColor(group, QPalette.ColorRole.Mid, QColor(BORDER))
    palette.setColor(group, QPalette.ColorRole.Dark, QColor("#B7A597"))
    palette.setColor(group, QPalette.ColorRole.Shadow, QColor("#9B8B80"))
    palette.setColor(group, QPalette.ColorRole.Link, QColor(ACCENT))
    palette.setColor(group, QPalette.ColorRole.LinkVisited, QColor(ACCENT_HOVER))
    try:
        palette.setColor(group, QPalette.ColorRole.Accent, QColor(ACCENT))
    except AttributeError:
        pass


def apply_app_palette(app: QApplication) -> None:
    palette = QPalette()
    _set_group(palette, QPalette.ColorGroup.Active)
    _set_group(palette, QPalette.ColorGroup.Inactive)
    _set_group(palette, QPalette.ColorGroup.Disabled, disabled=True)
    app.setPalette(palette)


def application_stylesheet() -> str:
    """Complete color rules without forcing a font family or font size."""
    down_arrow = resource_path("assets/chevron_down.png").as_posix()
    up_arrow = resource_path("assets/chevron_up.png").as_posix()
    return f"""
    QWidget {{
        color: {TEXT};
    }}

    QMainWindow,
    QDialog,
    QWidget#centralRoot {{
        background-color: {BG};
        color: {TEXT};
    }}

    QLabel {{
        color: {TEXT};
        background: transparent;
    }}
    QLabel[muted="true"] {{
        color: {MUTED};
    }}

    QMenuBar {{
        background-color: {HEADER};
        color: {TEXT};
        border-bottom: 1px solid {BORDER};
        spacing: 2px;
    }}
    QMenuBar::item {{
        color: {TEXT};
        background: transparent;
        padding: 5px 9px;
        border-radius: 4px;
    }}
    QMenuBar::item:selected,
    QMenuBar::item:pressed {{
        color: {TEXT};
        background: {ACCENT_SOFT};
    }}

    QMenu {{
        background-color: {CARD};
        color: {TEXT};
        border: 1px solid {BORDER};
        padding: 4px;
    }}
    QMenu::item {{
        color: {TEXT};
        background: transparent;
        padding: 6px 30px 6px 24px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background: {ACCENT_SOFT};
        color: {TEXT};
    }}
    QMenu::item:disabled {{
        color: {DISABLED_TEXT};
    }}
    QMenu::separator {{
        height: 1px;
        background: {BORDER};
        margin: 4px 8px;
    }}

    QToolBar {{
        background-color: {HEADER};
        color: {TEXT};
        border: none;
        border-bottom: 1px solid {BORDER};
        spacing: 5px;
        padding: 5px 8px;
    }}
    QToolBar QToolButton {{
        color: {TEXT};
        background: {CARD};
        padding: 6px 10px;
        border: 1px solid {BORDER};
        border-radius: 6px;
        margin: 1px;
    }}
    QToolBar QToolButton:hover {{
        background: {ACCENT_SOFT};
        border-color: {BORDER};
    }}
    QToolBar QToolButton:pressed {{
        background: #E8C9B3;
    }}
    QToolBar QToolButton:disabled {{
        color: {DISABLED_TEXT};
    }}

    QToolBar QToolButton[toolbarRole="start"] {{
        background-color: {ACCENT};
        color: #FFFFFF;
        border-color: {ACCENT};
        font-weight: 600;
    }}
    QToolBar QToolButton[toolbarRole="start"]:hover {{
        background-color: {ACCENT_HOVER};
        border-color: {ACCENT_HOVER};
    }}
    QToolBar QToolButton[toolbarRole="stop"] {{
        background-color: #B85B52;
        color: #FFFFFF;
        border-color: #B85B52;
        font-weight: 600;
    }}
    QToolBar QToolButton[toolbarRole="stop"]:hover {{
        background-color: #9F4B44;
        border-color: #9F4B44;
    }}
    QToolBar QToolButton[toolbarRole="start"]:disabled,
    QToolBar QToolButton[toolbarRole="stop"]:disabled {{
        color: {DISABLED_TEXT};
        background-color: #F0EAE4;
        border-color: #DDD2C8;
    }}


    QFrame#environmentBanner {{
        background-color: #FFF1E5;
        border: 1px solid #E4B58F;
        border-radius: 7px;
    }}
    QFrame#browserStatusPanel {{
        background-color: #FCF7F1;
        border: 1px solid {BORDER};
        border-radius: 7px;
    }}
    QFrame#browserStatusPanel QLabel {{
        background: transparent;
    }}
    QFrame#engineSelector {{
        background: transparent;
        border: none;
    }}
    QPushButton[engineSelector="true"] {{
        background-color: {CARD};
        border: 1px solid {BORDER};
        border-radius: 0;
        padding: 7px 24px;
        min-width: 96px;
    }}
    QPushButton[engineSelector="true"][enginePosition="first"] {{
        border-top-left-radius: 7px;
        border-bottom-left-radius: 7px;
    }}
    QPushButton[engineSelector="true"][enginePosition="last"] {{
        border-left: 0;
        border-top-right-radius: 7px;
        border-bottom-right-radius: 7px;
    }}
    QPushButton[engineSelector="true"]:checked {{
        background-color: {ACCENT};
        border-color: {ACCENT};
        color: white;
    }}
    QPushButton[engineSelector="true"]:hover:!checked {{
        background-color: {ACCENT_SOFT};
    }}

    QTabWidget {{
        background: transparent;
        color: {TEXT};
    }}
    QTabWidget::pane {{
        border: 1px solid {BORDER};
        background: {CARD};
        top: -1px;
    }}
    QTabBar::tab {{
        color: {TEXT};
        background: #F7EFE7;
        border: 1px solid {BORDER};
        padding: 6px 14px;
        margin-right: 2px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
    }}
    QTabBar::tab:selected {{
        color: #FFFFFF;
        background: {ACCENT};
        border-color: {ACCENT};
    }}
    QTabBar::tab:hover:!selected {{
        background: {ACCENT_SOFT};
    }}

    QGroupBox {{
        color: {TEXT};
        background-color: {CARD};
        border: 1px solid {BORDER};
        border-radius: 8px;
        margin-top: 14px;
        padding: 12px 8px 8px 8px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 10px;
        padding: 0 5px;
        color: {TEXT};
        background-color: {CARD};
        font-weight: 600;
    }}

    QPushButton {{
        background-color: {CARD};
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 5px 10px;
        min-height: 20px;
    }}
    QPushButton:hover {{
        background-color: {ACCENT_SOFT};
    }}
    QPushButton:pressed {{
        background-color: #E8C9B3;
    }}
    QPushButton:default {{
        border-color: {ACCENT};
    }}
    QPushButton:disabled {{
        color: {DISABLED_TEXT};
        background-color: #F6F1EC;
        border-color: #E3D8CE;
    }}

    QPushButton[dangerAction="true"] {{
        color: #8E3E38;
        border-color: #D7A39E;
        background-color: #FFF8F7;
    }}
    QPushButton[dangerAction="true"]:hover {{
        color: #FFFFFF;
        border-color: #B85B52;
        background-color: #B85B52;
    }}
    QPushButton[dangerAction="true"]:disabled {{
        color: {DISABLED_TEXT};
        border-color: #E3D8CE;
        background-color: #F6F1EC;
    }}

    QFrame#helpHeader {{
        background-color: {CARD};
        border: 1px solid {BORDER};
        border-radius: 9px;
    }}
    QLabel#helpHeading {{
        color: {ACCENT};
        font-size: 22px;
        font-weight: 700;
    }}
    QLabel#helpHeadingSecondary {{
        color: {TEXT};
        font-size: 16px;
        font-weight: 600;
    }}
    QLabel#aboutIdentity {{
        color: {TEXT};
    }}
    QTextBrowser#helpTextBrowser {{
        background-color: {CARD};
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 10px;
    }}

    QLineEdit,
    QTextEdit,
    QPlainTextEdit,
    QComboBox,
    QSpinBox,
    QDateEdit {{
        background-color: {EDITOR};
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 4px 7px;
        selection-background-color: {SELECTION};
        selection-color: {TEXT};
    }}
    QLineEdit:focus,
    QTextEdit:focus,
    QPlainTextEdit:focus,
    QComboBox:focus,
    QSpinBox:focus,
    QDateEdit:focus {{
        border-color: {ACCENT};
    }}
    QLineEdit:disabled,
    QTextEdit:disabled,
    QPlainTextEdit:disabled,
    QComboBox:disabled,
    QSpinBox:disabled,
    QDateEdit:disabled {{
        color: {DISABLED_TEXT};
        background-color: #F6F1EC;
    }}
    QComboBox, QDateEdit {{
        padding-right: 32px;
    }}
    QComboBox::drop-down, QDateEdit::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 28px;
        border-left: 1px solid #E8DDD3;
        background-color: {EDITOR};
        border-top-right-radius: 5px;
        border-bottom-right-radius: 5px;
    }}
    QComboBox::drop-down:hover, QDateEdit::drop-down:hover {{
        background-color: {ACCENT_SOFT};
    }}
    QComboBox::down-arrow,
    QDateEdit::down-arrow {{
        image: url("{down_arrow}");
        width: 14px;
        height: 14px;
    }}
    QComboBox::down-arrow:disabled,
    QDateEdit::down-arrow:disabled {{
        image: url("{down_arrow}");
    }}
    QSpinBox {{
        padding-right: 28px;
    }}
    QSpinBox::up-button, QSpinBox::down-button {{
        subcontrol-origin: border;
        width: 24px;
        border-left: 1px solid #E8DDD3;
        background-color: {EDITOR};
    }}
    QSpinBox::up-button {{
        border-top-right-radius: 5px;
    }}
    QSpinBox::down-button {{
        border-bottom-right-radius: 5px;
    }}
    QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
        background-color: {ACCENT_SOFT};
    }}
    QSpinBox::up-arrow {{
        image: url("{up_arrow}");
        width: 12px;
        height: 10px;
    }}
    QSpinBox::down-arrow {{
        image: url("{down_arrow}");
        width: 12px;
        height: 10px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {CARD};
        color: {TEXT};
        selection-background-color: {ACCENT_SOFT};
        selection-color: {TEXT};
        border: 1px solid {BORDER};
        outline: 0;
    }}

    QCalendarWidget QWidget#qt_calendar_navigationbar {{
        background-color: {HEADER};
    }}
    QCalendarWidget QToolButton {{
        color: {TEXT};
        background: transparent;
        border: 0;
        padding: 4px 7px;
    }}
    QCalendarWidget QToolButton:hover {{
        background-color: {ACCENT_SOFT};
        border-radius: 4px;
    }}
    QCalendarWidget QToolButton#qt_calendar_monthbutton {{
        min-width: 112px;
    }}
    QCalendarWidget QToolButton#qt_calendar_yearbutton {{
        min-width: 68px;
    }}

    QListWidget,
    QTableView {{
        background-color: {EDITOR};
        alternate-background-color: #FBF6F1;
        color: {TEXT};
        border: 1px solid {BORDER};
        gridline-color: #E7DBD0;
        selection-background-color: {ACCENT_SOFT};
        selection-color: {TEXT};
        outline: 0;
    }}
    QListWidget::item,
    QTableView::item {{
        color: {TEXT};
        padding: 3px 5px;
    }}
    QListWidget::item:selected,
    QTableView::item:selected {{
        color: {TEXT};
        background: {ACCENT_SOFT};
    }}

    QHeaderView {{
        background-color: #F6EADF;
        color: {TEXT};
    }}
    QHeaderView::section {{
        background-color: #F6EADF;
        color: {TEXT};
        border: none;
        border-right: 1px solid {BORDER};
        border-bottom: 1px solid {BORDER};
        padding: 6px 7px;
    }}

    QProgressBar {{
        background-color: #EFE7DF;
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 5px;
        text-align: center;
        min-height: 16px;
    }}
    QProgressBar::chunk {{
        background-color: {ACCENT};
        border-radius: 4px;
    }}

    QCheckBox {{
        color: {TEXT};
        spacing: 6px;
    }}
    QCheckBox:disabled {{
        color: {DISABLED_TEXT};
    }}

    QScrollArea {{
        background: transparent;
        border: none;
    }}
    QScrollArea > QWidget > QWidget {{
        background: transparent;
    }}

    QSplitter::handle:horizontal {{
        background-color: {BG};
        width: 7px;
    }}
    QSplitter::handle:horizontal:hover {{
        background-color: {ACCENT_SOFT};
    }}
    QSplitter::handle:vertical {{
        background-color: {BG};
        height: 7px;
    }}
    QSplitter::handle:vertical:hover {{
        background-color: {ACCENT_SOFT};
    }}

    QStatusBar {{
        background-color: {HEADER};
        color: {MUTED};
        border-top: 1px solid {BORDER};
    }}
    QStatusBar::item {{
        border: none;
    }}

    QScrollBar:vertical {{
        background: #F2E9E1;
        width: 13px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: #CDB7A5;
        min-height: 28px;
        border-radius: 6px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: #B99C86;
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: #F2E9E1;
        height: 13px;
        margin: 0;
    }}
    QScrollBar::handle:horizontal {{
        background: #CDB7A5;
        min-width: 28px;
        border-radius: 6px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: #B99C86;
    }}
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0;
    }}

    QDialogButtonBox QPushButton {{
        min-width: 78px;
    }}

    QToolTip {{
        background-color: {CARD};
        color: {TEXT};
        border: 1px solid {BORDER};
        padding: 4px;
    }}
    """


def apply_global_theme(app: QApplication) -> None:
    # Fusion is a Qt-provided cross-platform style.  It keeps widgets standard
    # PySide6 controls while preventing Windows/macOS system theme foregrounds
    # from leaking into this fixed-light interface.
    app.setStyle("Fusion")
    apply_app_palette(app)
    app.setStyleSheet(application_stylesheet())
