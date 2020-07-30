"""
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
"""

from .defaults import DEFAULTS


class GlobalConf:
    """Manages lifedrain's global configuration."""
    fields = ['stopOnAnswer', 'barPosition', 'barHeight',
              'barBorderRadius', 'barText', 'barStyle', 'barFgColor',
              'barTextColor', 'enableBgColor', 'barBgColor']
    _main_window = None

    def __init__(self, mw):
        self._main_window = mw

    def get(self):
        """Get global configuration from Anki's database."""
        conf = self._main_window.col.conf
        global_conf = conf.get('lifedrain')
        if global_conf is None:
            conf_dict = {}
            for field in self.fields:
                conf_dict[field] = conf.get(field, DEFAULTS[field])
            enable = not conf.get('disable', not DEFAULTS['enable'])
            conf_dict['enable'] = enable
            return conf_dict

        return global_conf.copy()

    def set(self, new_conf):
        """Saves global configuration into Anki's database."""
        col = self._main_window.col
        conf = col.conf

        if 'lifedrain' not in conf:
            conf['lifedrain'] = {}
        for field in self.fields:
            conf['lifedrain'][field] = new_conf[field]
        conf['lifedrain']['enable'] = new_conf['enable']
        col.setMod()


class DeckConf:
    """Manages each lifedrain's deck configuration."""
    fields = ['maxLife', 'recover', 'damage']
    _main_window = None

    def __init__(self, mw):
        self._main_window = mw

    def get(self):
        """Get current deck configuration from Anki's database."""
        deck = self._main_window.col.decks.current()
        conf = deck.get('lifedrain', {})
        conf_dict = {
            'id': deck['id'],
            'name': deck['name'],
        }
        for field in self.fields:
            conf_dict[field] = conf.get(field, DEFAULTS[field])
        return conf_dict

    def set(self, new_conf):
        """Saves deck configuration into Anki's database."""
        col = self._main_window.col
        deck = col.decks.current()

        if 'lifedrain' not in deck:
            deck['lifedrain'] = {}
        for field in self.fields:
            deck['lifedrain'][field] = new_conf[field]
        col.decks.save(deck)
