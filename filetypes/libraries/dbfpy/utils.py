"""String utilities.

TODO:
  - allow strings in getDateTime routine;
"""
"""History (most recent first):
11-feb-2007 [als]   added INVALID_VALUE
10-feb-2007 [als]   allow date strings padded with spaces instead of zeroes
20-dec-2005 [yc]    handle long objects in getDate/getDateTime
16-dec-2005 [yc]    created from ``strutil`` module.
"""

__version__ = "$Revision: 1.4 $"[11:-2]
__date__ = "$Date: 2007/02/11 08:57:17 $"[7:-2]

import datetime
import time
import re

DATEPATTERN = r'[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]'
TIMEPATTERN = r'[0-2][0-9]:[0-5][0-9]:[0-5][0-9]'
DATETIMEPATTERN = r'[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9] [0-2][0-9]:[0-5][0-9]:[0-5][0-9]'

         
def unzfill(str):
    """Return a string without ASCII NULs.

    This function searchers for the first NUL (ASCII 0) occurance
    and truncates string till that position.

    """
    try:
        return str[:str.index('\0')]
    except ValueError:
        return str


def getDate(value=None):
    """Return `datetime.date` instance.

    Type of the ``value`` argument could be one of the following:
        None:
            use current date value;
        datetime.date:
            this value will be returned;
        datetime.datetime:
            the result of the date.date() will be returned;
        string:
            assuming "%Y%m%d" or "%y%m%d" format;
        number:
            assuming it's a timestamp (returned for example
            by the time.time() call;
        sequence:
            assuming (year, month, day, ...) sequence;

    Additionaly, if ``value`` has callable ``ticks`` attribute,
    it will be used and result of the called would be treated
    as a timestamp value.

    """
    if value is None:
        # use current value
        return datetime.date.today()
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, (int, long, float)):
        # date is a timestamp
        return datetime.date.fromtimestamp(value)
    if isinstance(value, basestring):
        # check if the string begins with a date
        if re.match(DATEPATTERN, value):
            # '2005-05-05 00:00:00'
            datestr = value.split()[0]
            # '2005-05-05'
            justdate = time.strptime(datestr, "%Y-%m-%d")[:3]
            # (2005, 5, 5)
            return datetime.date(*justdate)
        value = value.replace(" ", "0")
        if len(value) == 6:
            # yymmdd
            return datetime.date(*time.strptime(value, "%y%m%d")[:3])
        # yyyymmdd
        return datetime.date(*time.strptime(value, "%Y%m%d")[:3])
    if hasattr(value, "__getitem__"):
        # a sequence (assuming date/time tuple)
        return datetime.date(*value[:3])
    return datetime.date.fromtimestamp(value.ticks())


def getDateTime(value=None):
    """Return `datetime.datetime` instance.

    Type of the ``value`` argument could be one of the following:
        None:
            use current date value;
        datetime.date:
            result will be converted to the `datetime.datetime` instance
            using midnight;
        datetime.datetime:
            ``value`` will be returned as is;
        string:
            datetime: '2005-05-05 16:20:00'
            date: '2005-05-05'
            time: '16:20:00'
        number:
            assuming it's a timestamp (returned for example
            by the time.time() call;
        sequence:
            assuming (year, month, day, ...) sequence;

    Additionaly, if ``value`` has callable ``ticks`` attribute,
    it will be used and result of the called would be treated
    as a timestamp value.

    """
    if value is None:
        # use current value
        return datetime.datetime.today()
    if isinstance(value, datetime.datetime):
        return value
    if isinstance(value, datetime.date):
        return datetime.datetime.fromordinal(value.toordinal())
    if isinstance(value, (int, long, float)):
        # value is a timestamp
        return datetime.datetime.fromtimestamp(value)
    if isinstance(value, basestring):
        if re.match(DATETIMEPATTERN, value):
            # '2005-05-05 16:20:01'
            structtime = time.strptime(value, "%Y-%m-%d %H:%M:%S")[:6]
            # (2005, 5, 5, 16, 20, 1)
            return datetime.datetime(*structtime)
        elif re.match(DATEPATTERN, value):
            # '2005-05-05 16:20:01'
            structtime = time.strptime(value, "%Y-%m-%d")[:6]
            # (2005, 5, 5, 16, 20, 1)
            return datetime.datetime(*structtime)
        elif re.match(TIMEPATTERN, value):
            # '16:20:01'
            structtime = time.strptime(value, "%H:%M:%S")[:6]
            # (1900, 1, 1, 16, 20, 1)
            return datetime.datetime(*structtime)
    if hasattr(value, "__getitem__"):
        # a sequence (assuming date/time tuple)
        return datetime.datetime(*tuple(value)[:6])
    return datetime.datetime.fromtimestamp(value.ticks())


class classproperty(property):
    """Works in the same way as a ``property``, but for the classes."""

    def __get__(self, obj, cls):
        return self.fget(cls)


class _InvalidValue(object):

    """Value returned from DBF records when field validation fails

    The value is not equal to anything except for itself
    and equal to all empty values: None, 0, empty string etc.
    In other words, invalid value is equal to None and not equal
    to None at the same time.

    This value yields zero upon explicit conversion to a number type,
    empty string for string types, and False for boolean.

    """

    def __eq__(self, other):
        return not other

    def __ne__(self, other):
        return not (other is self)

    def __nonzero__(self):
        return False

    def __int__(self):
        return 0
    __long__ = __int__

    def __float__(self):
        return 0.0

    def __str__(self):
        return ""

    def __unicode__(self):
        return u""

    def __repr__(self):
        return "<INVALID>"

# invalid value is a constant singleton
INVALID_VALUE = _InvalidValue()

# vim: set et sts=4 sw=4 :
