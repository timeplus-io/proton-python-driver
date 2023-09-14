from .base import FormatColumn


class BoolColumn(FormatColumn):
    ch_type = 'bool'
    py_types = (bool, )
    format = '?'
