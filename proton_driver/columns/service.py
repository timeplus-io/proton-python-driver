import logging

from .. import errors
from .arraycolumn import create_array_column
from .boolcolumn import BoolColumn
from .datecolumn import DateColumn, Date32Column
from .datetimecolumn import create_datetime_column
from .decimalcolumn import create_decimal_column
from . import exceptions as column_exceptions
from .enumcolumn import create_enum_column
from .floatcolumn import Float32Column, Float64Column
from .intcolumn import (
    Int8Column, Int16Column, Int32Column, Int64Column,
    Int128Column, UInt128Column, Int256Column, UInt256Column,
    UInt8Column, UInt16Column, UInt32Column, UInt64Column
)
from .lowcardinalitycolumn import create_low_cardinality_column
from .mapcolumn import create_map_column
from .nothingcolumn import NothingColumn
from .nullcolumn import NullColumn
from .nullablecolumn import create_nullable_column
from .simpleaggregatefunctioncolumn import (
    create_simple_aggregate_function_column
)
from .stringcolumn import create_string_column
from .tuplecolumn import create_tuple_column
from .nestedcolumn import create_nested_column
from .uuidcolumn import UUIDColumn
from .intervalcolumn import (
    IntervalYearColumn, IntervalMonthColumn, IntervalWeekColumn,
    IntervalDayColumn, IntervalHourColumn, IntervalMinuteColumn,
    IntervalSecondColumn
)
from .ipcolumn import IPv4Column, IPv6Column
from .jsoncolumn import create_json_column


column_by_type = {c.ch_type: c for c in [
    DateColumn, Date32Column, Float32Column, Float64Column,
    Int8Column, Int16Column, Int32Column, Int64Column,
    Int128Column, UInt128Column, Int256Column, UInt256Column,
    UInt8Column, UInt16Column, UInt32Column, UInt64Column,
    NothingColumn, NullColumn, UUIDColumn,
    IntervalYearColumn, IntervalMonthColumn, IntervalWeekColumn,
    IntervalDayColumn, IntervalHourColumn, IntervalMinuteColumn,
    IntervalSecondColumn, IPv4Column, IPv6Column, BoolColumn
]}

logger = logging.getLogger(__name__)


def get_column_by_spec(spec, column_options, use_numpy=None):
    context = column_options['context']

    if use_numpy is None:
        use_numpy = context.client_settings['use_numpy'] if context else False

    if use_numpy:
        from .numpy.service import get_numpy_column_by_spec

        try:
            return get_numpy_column_by_spec(spec, column_options)
        except errors.UnknownTypeError:
            use_numpy = False
            logger.warning('NumPy support is not implemented for %s. '
                           'Using generic column', spec)

    def create_column_with_options(x, settings=None):
        if settings:
            client_settings = column_options['context'].client_settings
            client_settings.update(settings)
            column_options['context'].client_settings = client_settings
        return get_column_by_spec(x, column_options, use_numpy=use_numpy)

    if spec == 'string' or spec.startswith('fixed_string'):
        return create_string_column(spec, column_options)

    elif spec.startswith('enum'):
        return create_enum_column(spec, column_options)

    elif spec.startswith('datetime'):
        return create_datetime_column(spec, column_options)

    elif spec.startswith('decimal'):
        return create_decimal_column(spec, column_options)

    elif spec.startswith('array'):
        return create_array_column(
            spec, create_column_with_options, column_options
        )

    elif spec.startswith('tuple'):
        return create_tuple_column(
            spec, create_column_with_options, column_options
        )
    elif spec.startswith('json'):
        return create_json_column(
            spec, create_column_with_options, column_options
        )

    elif spec.startswith('nested'):
        return create_nested_column(
            spec, create_column_with_options, column_options
        )

    elif spec.startswith('nullable'):
        return create_nullable_column(spec, create_column_with_options)

    elif spec.startswith('low_cardinality'):
        return create_low_cardinality_column(spec, create_column_with_options)

    elif spec.startswith('simple_aggregate_function'):
        return create_simple_aggregate_function_column(
            spec, create_column_with_options)

    elif spec.startswith('map'):
        return create_map_column(spec, create_column_with_options)

    else:
        try:
            cls = column_by_type[spec]
            return cls(**column_options)

        except KeyError:
            raise errors.UnknownTypeError('Unknown type {}'.format(spec))


def read_column(context, column_spec, n_items, buf):
    column_options = {'context': context}
    column = get_column_by_spec(column_spec, column_options)
    column.read_state_prefix(buf)
    return column.read_data(n_items, buf)


def write_column(context, column_name, column_spec, items, buf,
                 types_check=False):
    column_options = {
        'context': context,
        'types_check': types_check
    }
    column = get_column_by_spec(column_spec, column_options)

    try:
        column.write_state_prefix(buf)
        column.write_data(items, buf)

    except column_exceptions.ColumnTypeMismatchException as e:
        raise errors.TypeMismatchError(
            'Type mismatch in VALUES section. '
            'Expected {} got {}: {} for column "{}".'.format(
                column_spec, type(e.args[0]), e.args[0], column_name
            )
        )

    except (column_exceptions.StructPackException, OverflowError) as e:
        error = e.args[0]
        raise errors.TypeMismatchError(
            'Type mismatch in VALUES section. '
            'Repeat query with types_check=True for detailed info. '
            'Column {}: {}'.format(
                column_name, str(error)
            )
        )
