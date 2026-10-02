"""Shared visual style for the desktop controls."""
STYLE = """
QWidget { background: #182031; color: #e7edf7; font-family: sans-serif; font-size: 14px; }
QLabel { background: transparent; }
QLabel#title { font-size: 28px; font-weight: bold; }
QLabel#muted { color: #a9b9d0; }
QLabel#gesture { font-size: 27px; font-weight: bold; color: #bcd6f6; }
QLabel#symbol { font-size: 58px; color: #bcd6f6; }
QFrame#card { background: #233149; border-radius: 14px; }
QPushButton { background: #bcd6f6; color: #182031; border: none; border-radius: 8px; padding: 12px 20px; font-weight: bold; }
QPushButton:hover { background: #d5e7fc; }
QPushButton:disabled { background: #34445f; color: #9ba9bf; }
QComboBox { background: #233149; padding: 8px; border: 1px solid #526888; border-radius: 6px; }
QPushButton#settingsButton, QPushButton#helpButton { background: transparent; color: #bcd6f6; font-size: 28px; padding: 0; }
QPushButton#settingsButton:hover, QPushButton#helpButton:hover { background: #34445f; }
QComboBox QAbstractItemView { background: #233149; color: #e7edf7; selection-background-color: #526888; }
QLabel#tutorialHeading { font-size: 17px; font-weight: bold; color: #bcd6f6; }
QTabWidget::pane { border: 1px solid #34445f; border-radius: 8px; }
QTabBar::tab { background: #233149; color: #a9b9d0; padding: 12px 16px; }
QTabBar::tab:selected { background: #34445f; color: #bcd6f6; }
QCheckBox { spacing: 8px; }
QToolTip { background: #233149; color: #e7edf7; }
"""
