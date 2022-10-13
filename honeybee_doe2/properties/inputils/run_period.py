
from ladybug.analysisperiod import AnalysisPeriod


class RunPeriod(object):
    def __init__(
            self, begin_month=1, begin_day=1, begin_year=2022, end_month=12, end_day=31,
            end_year=2022):
        self.begin_month = begin_month
        self.begin_day = begin_day
        self.begin_year = begin_year
        self.end_month = end_month
        self.end_day = end_day

    @classmethod
    def from_analysis_period(cls, analysis_period: AnalysisPeriod = None):
        analysis_period = analysis_period or AnalysisPeriod()
        cls_ = cls()
        cls_.begin_month = analysis_period.st_month
        cls_.begin_day = analysis_period.st_day
        cls_.end_month = analysis_period.end_month
        cls_.end_day = analysis_period.end_month

        return cls_

    def to_inp(self):
        """Return run period as an inp string."""
        # standard holidays should be exposed.
        return '"Entire Year" = RUN-PERIOD-PD\n   ' \
            'BEGIN-MONTH     = 1\n' \
            '   BEGIN-DAY      = 1\n' \
            '   BEGIN-YEAR     = 2021\n' \
            '   END-MONTH      = 12\n' \
            '   END-DAY        = 31\n' \
            '   END-YEAR       = 2021\n' \
            '   ..\n\n' \
            '"Standard US Holidays" = HOLIDAYS\n   ' \
            'LIBRARY-ENTRY "US"\n   ..'

    def __repr__(self):
        return self.to_inp()
