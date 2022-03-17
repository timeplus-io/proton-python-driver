from .intcolumn import Int64Column


class IntervalColumn(Int64Column):
    pass


class IntervalDayColumn(IntervalColumn):
    ch_type = 'interval_day'


class IntervalWeekColumn(IntervalColumn):
    ch_type = 'interval_week'


class IntervalMonthColumn(IntervalColumn):
    ch_type = 'interval_month'


class IntervalYearColumn(IntervalColumn):
    ch_type = 'interval_year'


class IntervalHourColumn(IntervalColumn):
    ch_type = 'interval_hour'


class IntervalMinuteColumn(IntervalColumn):
    ch_type = 'interval_minute'


class IntervalSecondColumn(IntervalColumn):
    ch_type = 'interval_second'
