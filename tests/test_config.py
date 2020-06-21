"""
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
"""

from unittest import mock

from tests.test_base import LifedrainTestCase


class TestGlobalConf(LifedrainTestCase):

    def test_get_default(self):
        main_window = mock.MagicMock()
        main_window.col.conf = {}

        global_conf = self.lifedrain.config.GlobalConf(main_window)
        conf = global_conf.get()

        DEFAULTS = self.lifedrain.defaults.DEFAULTS
        expected_conf = {
            'enable': DEFAULTS['enable'],
            'stopOnAnswer': DEFAULTS['stopOnAnswer'],
            'barPosition': DEFAULTS['barPosition'],
            'barHeight': DEFAULTS['barHeight'],
            'barBorderRadius': DEFAULTS['barBorderRadius'],
            'barText': DEFAULTS['barText'],
            'barStyle': DEFAULTS['barStyle'],
            'barFgColor': DEFAULTS['barFgColor'],
            'barTextColor': DEFAULTS['barTextColor'],
            'enableBgColor': DEFAULTS['enableBgColor'],
            'barBgColor': DEFAULTS['barBgColor']}
        self.assertEqual(conf, expected_conf)

    def test_get_previous_settings(self):
        main_window = mock.MagicMock()
        main_window.col.conf = {
            'disable': True,
            'stopOnAnswer': True,
            'barPosition': 1,
            'barHeight': 20,
            'barBorderRadius': 3,
            'barText': 2,
            'barStyle': 6,
            'barFgColor': '#abcdef',
            'barTextColor': '#123456',
            'enableBgColor': True,
            'barBgColor': '#foobar'}

        global_conf = self.lifedrain.config.GlobalConf(main_window)
        conf = global_conf.get()

        expected_conf = main_window.col.conf.copy()
        expected_conf['enable'] = not expected_conf.pop('disable')
        self.assertEqual(conf, expected_conf)

    def test_get_custom(self):
        main_window = mock.MagicMock()
        main_window.col.conf = {
            'lifedrain': {
                'enable': False,
                'stopOnAnswer': True,
                'barPosition': 1,
                'barHeight': 20,
                'barBorderRadius': 3,
                'barText': 2,
                'barStyle': 6,
                'barFgColor': '#abcdef',
                'barTextColor': '#123456',
                'enableBgColor': True,
                'barBgColor': '#foobar'}}

        global_conf = self.lifedrain.config.GlobalConf(main_window)
        conf = global_conf.get()

        expected_conf = main_window.col.conf['lifedrain']
        self.assertEqual(conf, expected_conf)

    def test_set_first_time(self):
        main_window = mock.MagicMock()
        main_window.col.conf = {}

        global_conf = self.lifedrain.config.GlobalConf(main_window)
        conf = {
            'enable': False,
            'stopOnAnswer': True,
            'barPosition': 1,
            'barHeight': 20,
            'barBorderRadius': 3,
            'barText': 2,
            'barStyle': 6,
            'barFgColor': '#abcdef',
            'barTextColor': '#123456',
            'enableBgColor': True,
            'barBgColor': '#foobar'}
        global_conf.set(conf)

        expected_conf = {'lifedrain': conf}
        self.assertEqual(main_window.col.conf, expected_conf)
        main_window.col.setMod.assert_called_once_with()

    def test_set_overwrite(self):
        main_window = mock.MagicMock()
        main_window.col.conf = {
            'lifedrain': {
                'enable': True,
                'stopOnAnswer': False,
                'barPosition': 1,
                'barHeight': 15,
                'barBorderRadius': 0,
                'barText': 0,
                'barStyle': 0,
                'barFgColor': '#aaaaaa',
                'barTextColor': '#a1b2c3',
                'enableBgColor': False,
                'barBgColor': '#555444'}}

        global_conf = self.lifedrain.config.GlobalConf(main_window)
        conf = {
            'enable': False,
            'stopOnAnswer': True,
            'barPosition': 1,
            'barHeight': 20,
            'barBorderRadius': 3,
            'barText': 2,
            'barStyle': 6,
            'barFgColor': '#abcdef',
            'barTextColor': '#123456',
            'enableBgColor': True,
            'barBgColor': '#foobar'}
        global_conf.set(conf)

        expected_conf = {'lifedrain': conf}
        self.assertEqual(main_window.col.conf, expected_conf)
        main_window.col.setMod.assert_called_once_with()


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
