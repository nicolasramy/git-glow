from emoji import emojize
from termcolor import colored


def log(message):
    print(emojize(message))


def info(message):
    print(colored(emojize(message), "blue"))


def success(message):
    print(colored(emojize(message), "green"))


def warning(message):
    print(colored(emojize(message), "yellow"))


def error(message):
    print(colored(emojize(message), "red"))


def critical(message):
    print(colored(emojize(message), "grey", "on_red"))


def question(message):
    return input(colored(emojize(message), "cyan", attrs=["bold"]))
