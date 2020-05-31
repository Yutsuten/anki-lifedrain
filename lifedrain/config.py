"""
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
"""

from lifedrain.defaults import DEFAULTS


class DeckConf:
    """Manages each lifedrain's deck configuration."""
    fields = ['maxLife', 'recover', 'damage']
    _main_window = None

    def __init__(self, mw):
        self._main_window = mw

    def get(self):
        """Get current deck configuration from Anki's database."""
        col = self._main_window.col
        deck = col.decks.current()
        conf = deck.get('lifedrain')

        if conf is None:
            old_conf = col.decks.confForDid(deck['id'])
            dmg_value = old_conf.get('damage', DEFAULTS['damage'])
            dmg_enable = old_conf.get('enableDamage', False)
            return {
                'id': deck['id'],
                'name': deck['name'],
                'maxLife': old_conf.get('maxLife', DEFAULTS['maxLife']),
                'recover': old_conf.get('recover', DEFAULTS['recover']),
                'damage': dmg_value if dmg_enable else None
            }
        conf_dict = {
            'id': deck['id'],
            'name': deck['name'],
        }
        for field in self.fields:
            conf_dict[field] = conf.get(field, DEFAULTS[field])
        return conf_dict

    def set(self, new_conf):
        """Set and saves deck configuration into Anki's database."""
        col = self._main_window.col
        deck = col.decks.current()

        if 'lifedrain' not in deck:
            deck['lifedrain'] = {}
        for field in self.fields:
            deck['lifedrain'][field] = new_conf[field]
        col.decks.save(deck)
