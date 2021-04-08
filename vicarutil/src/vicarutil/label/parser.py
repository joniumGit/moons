from enum import Enum


class Token(Enum):
    LINK = '^'
    COMMENT_START = r'/*'
    COMMENT_END = r'*/'


class Words(Enum):
    GROUP = 'GROUP'
    OBJECT = 'OBJECT'
    END = 'END'


def create_end_token(t: Words):
    return f"{Words.END.value}_{t.value}"
