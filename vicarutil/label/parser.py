from enum import Enum


class Token(Enum):
    LINK = '^'


class Words(Enum):
    GROUP = 'GROUP'
    OBJECT = 'OBJECT'
    END = 'END'


def create_end_token(t: Words):
    return f"{Words.END.value}_{t.value}"
