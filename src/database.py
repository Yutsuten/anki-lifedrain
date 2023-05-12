# Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
# See the LICENCE file in the repository root for full licence text.

from aqt.main import AnkiQt

from .defaults import DEFAULTS


class GlobalConf:
    """Manages lifedrain's global configuration."""
    fields = {'enable', 'stopOnAnswer', 'barPosition', 'barHeight',
              'barBorderRadius', 'barText', 'barStyle', 'barFgColor',
              'barTextColor', 'enableBgColor', 'barBgColor',
              'globalSettingsShortcut', 'deckSettingsShortcut',
              'pauseShortcut', 'recoverShortcut', 'behavUndo', 'behavBury',
              'behavSuspend', 'stopOnLostFocus', 'shareDrain'}

    def __init__(self, mw: AnkiQt):
        self._mw = mw

    def get(self) -> dict:
        """Get global configuration from Anki's database."""
        conf = self._mw.addonManager.getConfig(__name__)
        if not conf:
            raise RuntimeError

        for field in self.fields:
            if field not in conf:
                conf[field] = DEFAULTS[field]
        for field in DeckConf.fields:
            if field not in conf:
                conf[field] = DEFAULTS[field]
        return conf

    def update(self, new_conf: dict) -> None:
        """Saves global configuration into Anki's database."""
        conf = self._mw.addonManager.getConfig(__name__)
        if not conf:
            raise RuntimeError

        for field in self.fields:
            if field in new_conf:
                conf[field] = new_conf[field]
        for field in DeckConf.fields:
            conf[field] = new_conf[field]
        self._mw.addonManager.writeConfig(__name__, conf)

        # Cleanup old configuration saved in mw.col.conf
        if self._mw.col is not None and 'lifedrain' in self._mw.col.conf:
            self._mw.col.conf.remove('lifedrain')


class DeckConf:
    """Manages each lifedrain's deck configuration."""
    fields = {'maxLife', 'recover', 'damage', 'damageNew', 'damageLearning'}

    def __init__(self, mw: AnkiQt):
        self._mw = mw
        self._global_conf = GlobalConf(mw)

    def get(self) -> dict:
        """Get current deck configuration from Anki's database."""
        if self._mw.col is None:
            raise RuntimeError

        conf = self._global_conf.get()
        deck = self._mw.col.decks.current()
        decks = conf.get('decks', {})
        deck_conf = decks.get(str(deck['id']), {})
        conf_dict = {
            'id': deck['id'],
            'name': deck['name'],
        }
        for field in self.fields:
            conf_dict[field] = deck_conf.get(field, conf[field])
        return conf_dict

    def update(self, new_conf: dict) -> None:
        """Saves deck configuration into Anki's database."""
        if self._mw.col is None:
            raise RuntimeError

        conf = self._global_conf.get()
        deck = self._mw.col.decks.current()
        if 'decks' not in conf:
            conf['decks'] = {}
        deck_conf = {}
        for field in self.fields:
            deck_conf[field] = new_conf[field]
        conf['decks'][str(deck['id'])] = deck_conf
        self._mw.addonManager.writeConfig(__name__, conf)

        # Cleanup old configuration saved in mw.col.decks
        if 'lifedrain' in deck:
            del deck['lifedrain']
            self._mw.col.decks.save(deck)
