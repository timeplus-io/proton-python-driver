
from .arraycolumn import create_array_column
from .util import get_inner_spec


def create_nested_column(spec, column_by_spec_getter, column_options):
    return create_array_column(
        'array(tuple({}))'.format(get_inner_spec('nested', spec)),
        column_by_spec_getter, column_options
    )
