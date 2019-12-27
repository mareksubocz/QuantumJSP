"""Simple python 2/3 compatibility fixes to avoid dependance on the `six`
package."""


# for simpler string detection
try:
    basestring = basestring
except:
    basestring = str

# for simpler integer detection
try:
    baseinteger = (int, long)
except:
    baseinteger = (int, )

# for simpler detection of valid index values
baseindex = baseinteger + (slice, )

# xrange for python3
try:
    xrange = xrange
except:
    xrange = range

# safe unicode classname
try:
    unicode = unicode
except:
    unicode = str
