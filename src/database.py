"""
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
"""

from .defaults import DEFAULTS


class GlobalConf:
    """Manages lifedrain's global configuration."""
    fields = {'enable', 'stopOnAnswer', 'barPosition', 'barHeight',
              'barBorderRadius', 'barText', 'barStyle', 'barFgColor',
              'barTextColor', 'enableBgColor', 'barBgColor',
              'globalSettingsShortcut', 'deckSettingsShortcut',
              'pauseShortcut', 'recoverShortcut', 'behavUndo', 'behavBury',
              'behavSuspend', 'stopOnLostFocus', 'shareDrain'}
    _main_window = None

    def __init__(self, mw):
        self._main_window = mw

    def get(self):
        """Get global configuration from Anki's database."""
        conf = self._main_window.addonManager.getConfig(__name__)
        if not conf:
            conf = self._main_window.col.get_config('lifedrain', {})
        for field in self.fields:
            if field not in conf:
                conf[field] = DEFAULTS[field]
        for field in DeckConf.fields:
            if field not in conf:
                conf[field] = DEFAULTS[field]
        return conf

    def set(self, new_conf):
        """Saves global configuration into Anki's database."""
        conf = self._main_window.addonManager.getConfig(__name__)
        for field in self.fields:
            if field in new_conf:
                conf[field] = new_conf[field]
        for field in DeckConf.fields:
            conf[field] = new_conf[field]
        self._main_window.addonManager.writeConfig(__name__, conf)


class DeckConf:
    """Manages each lifedrain's deck configuration."""
    fields = {'maxLife', 'recover', 'damage', 'damageNew', 'damageLearning'}
    _main_window = None

    def __init__(self, mw):
        self._main_window = mw
        self._global_conf = GlobalConf(mw)

    def get(self):
        """Get current deck configuration from Anki's database."""
        conf = self._global_conf.get()
        deck = self._main_window.col.decks.current()
        decks = conf.get('decks', {})
        deck_conf = decks.get(str(deck['id']), {})
        if not deck_conf:
            deck_conf = deck.get('lifedrain', {})
        conf_dict = {
            'id': deck['id'],
            'name': deck['name'],
        }
        for field in self.fields:
            conf_dict[field] = deck_conf.get(field, conf[field])
        return conf_dict

    def set(self, new_conf):
        """Saves deck configuration into Anki's database."""
        conf = self._global_conf.get()
        deck = self._main_window.col.decks.current()
        if 'decks' not in conf:
            conf['decks'] = {}
        deck_conf = {}
        for field in self.fields:
            deck_conf[field] = new_conf[field]
        conf['decks'][str(deck['id'])] = deck_conf
        self._main_window.addonManager.writeConfig(__name__, conf)
