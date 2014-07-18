from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
__author__ = 'croxis'
import spacedrive


class MainMenu(object):
    def __init__(self):
        self.path = 'GUI/main_menu.html'
        self.callbacks = {'new_game': self.new_game,
                          'load_game': self.load_game,
                          'join_game': self.join_game,
                          'options': self.options,
                          'exit': self.exit}
    def new_game(self):
        spacedrive.send('new game screen')
    def load_game(self):
        spacedrive.send('load game screen')
    def join_game(self):
        spacedrive.send('join game screen')
    def options(self):
        spacedrive.send('options screen')
    def exit(self):
        spacedrive.send('exit')