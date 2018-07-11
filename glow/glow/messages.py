# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from termcolor import colored


def log(message):
    print(message)


def info(message):
    print(colored(message, "blue"))


def success(message):
    print(colored(message, "green"))


def warning(message):
    print(colored(message, "yellow"))


def error(message):
    print(colored(message, "red"))


def critical(message):
    print(colored(message, "white", "on_red"))


def question(message):
    return raw_input(colored(message, "cyan", attrs=["bold"]))
