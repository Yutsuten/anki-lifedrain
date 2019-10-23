'''
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
'''

POSITION_OPTIONS = ['Top', 'Bottom']
STYLE_OPTIONS = [
    'Default', 'Cde', 'Cleanlooks', 'Fusion', 'Gtk', 'Macintosh',
    'Motif', 'Plastique', 'Windows', 'Windows Vista', 'Windows XP'
]
TEXT_FORMAT = [
    {'text': 'None'},
    {'text': 'current/total (XX%)', 'format': '%v/%m (%p%)'},
    {'text': 'current/total', 'format': '%v/%m'},
    {'text': 'current', 'format': '%v'},
    {'text': 'XX%', 'format': '%p%'},
    {'text': 'mm:ss', 'format': 'mm:ss'}
]
TEXT_OPTIONS = []
for text_format in TEXT_FORMAT:
    TEXT_OPTIONS.append(text_format['text'])

DEFAULTS = {
    'maxLife': 120,
    'recover': 5,
    'enableDamage': False,
    'damage': 5,
    'barPosition': POSITION_OPTIONS.index('Bottom'),
    'barHeight': 15,
    'barBgColor': '#f3f3f2',
    'barFgColor': '#489ef6',
    'barBorderRadius': 0,
    'barText': 0,
    'barTextColor': '#000',
    'barStyle': STYLE_OPTIONS.index('Default'),
    'stopOnAnswer': False,
    'disable': False
}
