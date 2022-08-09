"""
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
"""

BEHAVIORS = ['Drain life', 'Do nothing', 'Recover life']
POSITION_OPTIONS = ['Top', 'Bottom']
STYLE_OPTIONS = [
    'Default', 'Cde', 'Cleanlooks', 'Fusion', 'Gtk', 'Macintosh', 'Motif',
    'Plastique', 'Windows', 'Windows Vista', 'Windows XP'
]
TEXT_FORMAT = [{
    'text': 'None'
}, {
    'text': 'current/total (XX%)',
    'format': '%v/%m (%p%)'
}, {
    'text': 'current/total',
    'format': '%v/%m'
}, {
    'text': 'current',
    'format': '%v'
}, {
    'text': 'XX%',
    'format': '%p%'
}, {
    'text': 'mm:ss',
    'format': 'mm:ss'
}]

DEFAULTS = {
    'maxLife': 120,
    'recover': 5,
    'damage': None,
    'damageNew': None,
    'damageLearning': None,
    'barPosition': POSITION_OPTIONS.index('Bottom'),
    'barHeight': 15,
    'barFgColor': '#489ef6',
    'barBgColor': '#f3f3f2',
    'barBorderRadius': 0,
    'barText': 0,
    'barTextColor': '#000',
    'barStyle': STYLE_OPTIONS.index('Default'),
    'stopOnAnswer': False,
    'stopOnLostFocus': True,
    'enable': True,
    'enableBgColor': False,
    'globalSettingsShortcut': 'Ctrl+L',
    'deckSettingsShortcut': 'L',
    'pauseShortcut': 'P',
    'recoverShortcut': '',
    'behavUndo': BEHAVIORS.index('Drain life'),
    'behavBury': BEHAVIORS.index('Do nothing'),
    'behavSuspend': BEHAVIORS.index('Do nothing'),
    'shareDrain': False,
}
