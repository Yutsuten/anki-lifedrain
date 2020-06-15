"""
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
"""

from unittest import mock

from tests.test_base import LifedrainTestCase


class TestDeckConf(LifedrainTestCase):

    def test_get_default(self):
        main_window = mock.MagicMock()
        main_window.col.decks.current.return_value = {
            'id': 123,
            'name': 'My Deck'}

        deck_conf = self.lifedrain.config.DeckConf(main_window)
        conf = deck_conf.get()

        DEFAULTS = self.lifedrain.defaults.DEFAULTS
        expected_conf = {
            'id': 123,
            'name': 'My Deck',
            'maxLife': DEFAULTS['maxLife'],
            'recover': DEFAULTS['recover'],
            'damage': DEFAULTS['damage']}
        self.assertEqual(conf, expected_conf)

    def test_get_custom(self):
        main_window = mock.MagicMock()
        main_window.col.decks.current.return_value = {
            'id': 123,
            'name': 'My Deck',
            'lifedrain': {
                'maxLife': 200,
                'recover': 15,
                'damage': 10}}

        deck_conf = self.lifedrain.config.DeckConf(main_window)
        conf = deck_conf.get()

        expected_conf = {
            'id': 123,
            'name': 'My Deck',
            'maxLife': 200,
            'recover': 15,
            'damage': 10}
        self.assertEqual(conf, expected_conf)

    def test_set_first_time(self):
        main_window = mock.MagicMock()
        main_window.col.decks.current.return_value = {
            'id': 123,
            'name': 'My Deck'}

        deck_conf = self.lifedrain.config.DeckConf(main_window)
        conf = {
            'maxLife': 200,
            'recover': 15,
            'damage': 10}
        deck_conf.set(conf)

        expected_conf = {
            'id': 123,
            'name': 'My Deck',
            'lifedrain': conf}
        main_window.col.decks.save.assert_called_with(expected_conf)

    def test_set_overwrite(self):
        main_window = mock.MagicMock()
        main_window.col.decks.current.return_value = {
            'id': 123,
            'name': 'My Deck',
            'lifedrain': {
                'maxLife': 150,
                'recover': 10,
                'damage': 0}}

        deck_conf = self.lifedrain.config.DeckConf(main_window)
        conf = {
            'maxLife': 200,
            'recover': 15,
            'damage': 10}
        deck_conf.set(conf)

        expected_conf = {
            'id': 123,
            'name': 'My Deck',
            'lifedrain': conf}
        main_window.col.decks.save.assert_called_with(expected_conf)
