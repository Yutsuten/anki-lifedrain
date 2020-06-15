"""
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
"""

from unittest import TestCase, mock


class LifedrainTestCase(TestCase):

    @mock.patch('aqt.qt')
    def setUp(self, *args):
        import lifedrain
        self.lifedrain = lifedrain
