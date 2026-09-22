"""Shared visual style for the desktop controls."""
STYLE = """
QWidget { background: #18211e; color: #e7eee9; font-family: sans-serif; font-size: 14px; }
QLabel { background: transparent; }
QLabel#title { font-size: 28px; font-weight: bold; }
QLabel#muted { color: #a9bab3; }
QLabel#gesture { font-size: 27px; font-weight: bold; color: #d6e6bc; }
QLabel#symbol { font-size: 58px; color: #d6e6bc; }
QFrame#card { background: #23312b; border-radius: 14px; }
QPushButton { background: #d6e6bc; color: #18211e; border: none; border-radius: 8px; padding: 12px 20px; font-weight: bold; }
QPushButton:hover { background: #e7f3d5; }
QPushButton:disabled { background: #34443c; color: #9ba99f; }
QComboBox { background: #23312b; padding: 8px; border: 1px solid #526258; border-radius: 6px; }
QPushButton#settingsButton, QPushButton#helpButton { background: transparent; color: #d6e6bc; font-size: 28px; padding: 0; }
QPushButton#settingsButton:hover, QPushButton#helpButton:hover { background: #34443c; }
QComboBox QAbstractItemView { background: #23312b; color: #e7eee9; selection-background-color: #526258; }
QLabel#tutorialHeading { font-size: 17px; font-weight: bold; color: #d6e6bc; }
QTabWidget::pane { border: 1px solid #34443c; border-radius: 8px; }
QTabBar::tab { background: #23312b; color: #a9bab3; padding: 12px 16px; }
QTabBar::tab:selected { background: #34443c; color: #d6e6bc; }
QCheckBox { spacing: 8px; }
QToolTip { background: #23312b; color: #e7eee9; }
"""
