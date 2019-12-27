"""
Plucking (deep) keys/paths safely from python collections has never been easier.
"""
from __future__ import absolute_import

import re
import operator
from copy import deepcopy
from itertools import chain

from .compat import basestring
from .structural import pluckable

__all__ = ["pluck", "plucks", "pluckable", "merge"]


def plucks(obj, selector, default=None):
    """Safe itemgetter for structured objects.
    Happily operates on all (nested) objects that implement the item getter, 
    i.e. the `[]` operator.

    The `selector` is ~
    ``(<key>|<index>|<slice>|\*)(\.(<key>|<index>|<slice>|\*))*``.
    Parts (keys) in the selector path are separated with a dot. If the key
    looks like a number it's interpreted as such, i.e. as an index (so beware
    of numeric string keys in `dict`s).
    Python slice syntax is supported with keys like: ``2:7``, ``:5``, ``::-1``.
    A special key is ``*``, equivalent to the slice-all op ``:``. Note its
    usage does not serve functional, but annotational purpose -- feel free to
    leave it out (check the last example below).

    Examples:
        obj = {
            'users': [{
                'uid': 1234,
                'name': {
                    'first': 'John',
                    'last': 'Smith',
                }
            }, {
                'uid': 2345,
                'name': {
                    'last': 'Bono'
                }
            }]
        }

        plucks(obj, 'users.1.name')
            -> {'last': 'Bono'}

        plucks(obj, 'users.*.name.last')
            -> ['Smith', 'Bono']

        plucks(obj, 'users.name.first')
            -> ['John']


    Note: since the dot `.` is used as a separator, keys can not contain dots.
    """
    
    def _filter(iterable, index):
        res = []
        for obj in iterable:
            try:
                res.append(obj[index])
            except:
                pass
        return res

    def _int(val):
        try:
            return int(val)
        except:
            return None

    def _parsekey(key):
        m = re.match(r"^(?P<index>-?\d+)$", key)
        if m:
            return int(m.group('index'))

        m = re.match(r"^(?P<start>-?\d+)?"\
                     r"(:(?P<stop>-?\d+)?(:(?P<step>-?\d+)?)?)?$", key)
        if m:
            return slice(_int(m.group('start')),
                         _int(m.group('stop')),
                         _int(m.group('step')))

        if key == '*':
            return slice(None)

        return key

    miss = False
    for key in selector.split('.'):
        index = _parsekey(key)
        
        if miss:
            if isinstance(index, basestring):
                obj = {}
            else:
                obj = []
        
        try:
            if isinstance(index, basestring):
                if isinstance(obj, list):
                    obj = _filter(obj, index)
                else:
                    obj = obj[index]
            else:
                obj = obj[index]
            miss = False
        except:
            miss = True
    
    if miss:
        return default
    else:
        return obj


def pluck(obj, selector, default=None, skipmissing=True):
    """Alternative implementation of `plucks` that accepts more complex
    selectors. It's a wrapper around `pluckable`, so a `selector` can be any
    valid Python expression comprising attribute getters (``.attr``) and item
    getters (``[1, 4:8, "key"]``).

    Example:

        pluck(obj, "users[2:5, 10:15].name.first")

    equal to:

        pluckable(obj).users[2:5, 10:15].name.first.value

    """
    if not selector:
        return obj
    if selector[0] != '[':
        selector = '.%s' % selector
    wrapped_obj = pluckable(obj, default=default, skipmissing=skipmissing, inplace=True)
    return eval("wrapped_obj%s.value" % selector)


def merge(a, b, op=None, recurse_list=False, max_depth=None):
    """Immutable merge ``a`` structure with ``b`` using binary operator ``op``
    on leaf nodes. All nodes at, or below, ``max_depth`` are considered to be
    leaf nodes.

    Merged structure is returned, input data structures are not modified.

    If ``recurse_list=True``, leaf lists of equal length will be merged on a
    list-element level. Lists are considered to be leaf nodes by default
    (``recurse_list=False``), and they are merged with user-provided ``op``.
    Note the difference::

        merge([1, 2], [3, 4]) ==> [1, 2, 3, 4]

        merge([1, 2], [3, 4], recurse_list=True) ==> [4, 6]

    """

    if op is None:
        op = operator.add

    if max_depth is not None:
        if max_depth < 1:
            return op(a, b)
        else:
            max_depth -= 1

    if isinstance(a, dict) and isinstance(b, dict):
        result = {}
        for key in set(chain(a.keys(), b.keys())):
            if key in a and key in b:
                result[key] = merge(a[key], b[key],
                                    op=op, recurse_list=recurse_list,
                                    max_depth=max_depth)
            elif key in a:
                result[key] = deepcopy(a[key])
            elif key in b:
                result[key] = deepcopy(b[key])
        return result

    elif isinstance(a, list) and isinstance(b, list):
        if recurse_list and len(a) == len(b):
            # merge subelements
            result = []
            for idx in range(len(a)):
                result.append(merge(a[idx], b[idx],
                                    op=op, recurse_list=recurse_list,
                                    max_depth=max_depth))
            return result
        else:
            # merge lists
            return op(a, b)

    # all other merge ops should be handled by ``op``.
    # default ``operator.add`` will handle addition of numeric types, but fail
    # with TypeError for incompatible types (eg. str + None, etc.)
    return op(a, b)
