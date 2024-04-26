# Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
# See the LICENCE file in the repository root for full licence text.

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from .defaults import DEFAULTS
from .exceptions import GetCollectionError, LoadConfigurationError

if TYPE_CHECKING:
    from aqt.main import AnkiQt


class GlobalConf:
    """Manages Life Drain's global configuration."""
    FIELDS: ClassVar[set[str]] = {
        'enable', 'stopOnAnswer', 'barPosition', 'barHeight', 'barBorderRadius', 'barText',
        'barStyle', 'barFgColor', 'barTextColor', 'enableBgColor', 'barBgColor',
        'globalSettingsShortcut', 'deckSettingsShortcut', 'pauseShortcut', 'recoverShortcut',
        'behavUndo', 'behavBury', 'behavSuspend', 'stopOnLostFocus', 'shareDrain',
        'barThresholdWarn', 'barFgColorWarn', 'barThresholdDanger', 'barFgColorDanger',
        'startEmpty', 'invert',
    }

    def __init__(self, mw: AnkiQt):
        self._mw = mw

    def get(self) -> dict[str, Any]:
        """Get global configuration from Anki's database."""
        conf = self._mw.addonManager.getConfig(__name__)
        if conf is None:
            raise LoadConfigurationError

        for field in self.FIELDS:
            if field not in conf:
                conf[field] = DEFAULTS[field]
        for field in DeckConf.FIELDS:
            if field not in conf:
                conf[field] = DEFAULTS[field]
        return conf

    def update(self, new_conf: dict[str, Any]) -> None:
        """Saves global configuration into Anki's database.

        Args:
            new_conf: The new configuration dictionary.
        """
        conf = self._mw.addonManager.getConfig(__name__)
        if conf is None:
            raise LoadConfigurationError

        for field in self.FIELDS:
            if field in new_conf:
                conf[field] = new_conf[field]
        for field in DeckConf.FIELDS:
            conf[field] = new_conf[field]
        self._mw.addonManager.writeConfig(__name__, conf)


class DeckConf:
    """Manages Life Drain's deck configuration."""
    FIELDS: ClassVar[set[str]] = {
        'enable', 'maxLife', 'recover', 'damage', 'damageNew', 'damageLearning', 'fullRecoverSpeed',
    }

    def __init__(self, mw: AnkiQt):
        self._mw = mw
        self._global_conf = GlobalConf(mw)

    def get(self) -> dict:
        """Get current deck configuration from Anki's database."""
        if self._mw.col is None:
            raise GetCollectionError

        conf = self._global_conf.get()
        deck = self._mw.col.decks.current()
        decks = conf.get('decks', {})
        deck_conf = decks.get(str(deck['id']), {})
        conf_dict = {
            'id': deck['id'],
            'name': deck['name'],
        }
        for field in self.FIELDS:
            conf_dict[field] = deck_conf.get(field, conf[field])
        return conf_dict

    def update(self, new_conf: dict[str, Any]) -> None:
        """Saves deck configuration into Anki's database.

        Args:
            new_conf: The new configuration dictionary.
        """
        if self._mw.col is None:
            raise GetCollectionError

        conf = self._global_conf.get()
        deck = self._mw.col.decks.current()
        if 'decks' not in conf:
            conf['decks'] = {}
        deck_conf = {}
        for field in self.FIELDS:
            deck_conf[field] = new_conf[field]
        conf['decks'][str(deck['id'])] = deck_conf
        self._mw.addonManager.writeConfig(__name__, conf)
