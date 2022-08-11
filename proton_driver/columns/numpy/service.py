from ... import errors
from .datecolumn import NumpyDateColumn
from .datetimecolumn import create_numpy_datetime_column
from .floatcolumn import NumpyFloat32Column, NumpyFloat64Column
from .intcolumn import (
    NumpyInt8Column, NumpyInt16Column, NumpyInt32Column, NumpyInt64Column,
    NumpyUInt8Column, NumpyUInt16Column, NumpyUInt32Column, NumpyUInt64Column
)
from .lowcardinalitycolumn import create_numpy_low_cardinality_column
from .stringcolumn import create_string_column
from ..nullablecolumn import create_nullable_column

column_by_type = {c.ch_type: c for c in [
    NumpyDateColumn,
    NumpyFloat32Column, NumpyFloat64Column,
    NumpyInt8Column, NumpyInt16Column, NumpyInt32Column, NumpyInt64Column,
    NumpyUInt8Column, NumpyUInt16Column, NumpyUInt32Column, NumpyUInt64Column
]}


def get_numpy_column_by_spec(spec, column_options):
    def create_column_with_options(x):
        return get_numpy_column_by_spec(x, column_options)

    if spec == 'string' or spec.startswith('fixed_string'):
        return create_string_column(spec, column_options)

    elif spec.startswith('datetime'):
        return create_numpy_datetime_column(spec, column_options)

    elif spec.startswith('nullable'):
        return create_nullable_column(spec, create_column_with_options)

    elif spec.startswith('low_cardinality'):
        return create_numpy_low_cardinality_column(spec,
                                                   create_column_with_options)
    else:
        if spec in column_by_type:
            cls = column_by_type[spec]
            return cls(**column_options)

        raise errors.UnknownTypeError('Unknown type {}'.format(spec))
