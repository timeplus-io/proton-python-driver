import numpy as np

from .base import NumpyColumn


class NumpyInt8Column(NumpyColumn):
    dtype = np.dtype(np.int8)
    ch_type = 'int8'


class NumpyUInt8Column(NumpyColumn):
    dtype = np.dtype(np.uint8)
    ch_type = 'uint8'


class NumpyInt16Column(NumpyColumn):
    dtype = np.dtype(np.int16)
    ch_type = 'int16'


class NumpyUInt16Column(NumpyColumn):
    dtype = np.dtype(np.uint16)
    ch_type = 'uint16'


class NumpyInt32Column(NumpyColumn):
    dtype = np.dtype(np.int32)
    ch_type = 'int32'


class NumpyUInt32Column(NumpyColumn):
    dtype = np.dtype(np.uint32)
    ch_type = 'uint32'


class NumpyInt64Column(NumpyColumn):
    dtype = np.dtype(np.int64)
    ch_type = 'int64'


class NumpyUInt64Column(NumpyColumn):
    dtype = np.dtype(np.uint64)
    ch_type = 'uint64'
