"""
pluckable - object lazy wrapper that supports chained soft get/slice of
items and/or attributes like::

    pluckable(obj).users[2:5, 10:15].name.first

    pluckable(obj)[::-1].meta["is-admin"][0]

    pluckable({"v": namedtuple("Vector", "x y z")(1, 2, 3)}).v.x

"""

# TODO?
# pluckable([{'a': {2: 1}}]).a.2 --> 1

from __future__ import absolute_import

import sys

from .compat import xrange, baseinteger, basestring, unicode


class AttrSelector(unicode):
    """String key with preferrence for attribute plucking (`getattr`)."""

class KeySelector(unicode):
    """String key with preferrence for item plucking (`__getitem__`)."""


class pluckable(object):
    def __init__(self, obj=None, default=None, skipmissing=True,
                 inplace=False, empty=False):
        """Creates a new pluckable object based on `obj`. Default value for the
        missing keys is given with `default`.

        A two modes of plucking are supported::

        (1) the default, document databases alike, where missing keys (and it's
            ancestors) will be silently dropped-out -- except for the leaf
            nodes -- which always default to the ``default`` when missing.

        (2) one-on-one extractor (explict mode), which will include all missing
            values as ``default``, ensuring the leaf values exist even when one
            (or more) intermediate nodes are missing.
        """
        self.obj = obj
        self.default = default
        self.skipmissing = skipmissing
        self.inplace = inplace
        self.empty = empty

    def rewrap(self, **kwargs):
        """Inplace constructor. Depending on `self.inplace`, rewrap `obj`, or
        just update internal vars, possibly including the `obj`.
        """
        if self.inplace:
            for key, val in kwargs.items():
                setattr(self, key, val)
            return self
        else:
            for key in ['obj', 'default', 'skipmissing', 'inplace', 'empty']:
                kwargs.setdefault(key, getattr(self, key))
            return pluckable(**kwargs)

    @property
    def value(self):
        if self.empty:
            return self.default
        else:
            return self.obj

    def _append(self, obj, key, res, skipmissing=None):
        if skipmissing is None:
            skipmissing = self.skipmissing

        # prefer attributes over items
        if isinstance(key, AttrSelector):
            try:
                res.append(getattr(obj, key))
            except:  #  AttributeError et al
                try:
                    res.append(obj[key])
                except:  # KeyError et al
                    if not skipmissing:
                        res.append(self.default)
            return res

        # by default, prefer itemgetter over attrgetter (key ~ KeySelector)
        try:
            res.append(obj[key])
        except:  # KeyError et al
            try:
                res.append(getattr(obj, key))
            except:  #  AttributeError et al
                if not skipmissing:
                    res.append(self.default)
        return res

    def _filtered_list(self, selector):
        """Iterate over `self.obj` list, extracting `selector` from each
        element. The `selector` can be a simple integer index, or any valid
        key (hashable object).
        """
        res = []
        for elem in self.obj:
            self._append(elem, selector, res)
        return res

    def _sliced_list(self, selector):
        """For slice selectors operating on lists, we need to handle them
        differently, depending on ``skipmissing``. In explicit mode, we may have
        to expand the list with ``default`` values.
        """
        if self.skipmissing:
            return self.obj[selector]

        # TODO: can be optimized by observing list bounds
        keys = xrange(selector.start or 0,
                      selector.stop or sys.maxint,
                      selector.step or 1)
        res = []
        for key in keys:
            self._append(self.obj, key, res, skipmissing=False)
        return res

    def _extract_from_list(self, selector):
        if isinstance(selector, baseinteger):
            return self._sliced_list(slice(selector, selector+1))
        elif isinstance(selector, slice):
            return self._sliced_list(selector)
        else:
            return self._filtered_list(selector)
    
    def _extract_from_object(self, selector):
        """Extracts all values from `self.obj` object addressed with a `selector`.
        Selector can be a ``slice``, or a singular value extractor in form of a
        valid dictionary key (hashable object).
        
        Object (operated on) can be anything with an itemgetter or attrgetter,
        including, but limited to `dict`, and `list`.
        Itemgetter is preferred over attrgetter, except when called as `.key`.
        
        If `selector` is a singular value extractor (like a string, integer,
        etc), a single value (for a given key) is returned if key exists, an
        empty list if not.
        
        If `selector` is a ``slice``, each key from that range is extracted;
        failing-back, again, to an empty list.
        """
        if isinstance(selector, slice):
            # we must expand the slice manually, in order to be able to apply to
            # for example, to mapping types, or general objects
            # (e.g. slice `4::2` will filter all even numerical keys/attrs >=4)
            start = selector.start or 0
            step = selector.step or 1
            if selector.stop is None:
                if hasattr(self.obj, "keys"):
                    # filter keys by slice
                    keys = \
                        [k for k in self.obj.keys() if isinstance(k, baseinteger) \
                            and k >= start and (k - start) % step == 0]
                elif hasattr(self.obj, "__len__"):
                    # object we slice should have a length (__len__ method),
                    keys = xrange(start, len(self.obj), step)
                else:
                    # otherwise, we don't know how to slice, so just skip it,
                    # instead of failing
                    keys = []
            else:
                keys = xrange(start, selector.stop, step)

        else:
            keys = [selector]
        
        res = []
        for key in keys:
            self._append(self.obj, key, res)
        return res
    
    def _get_all(self, *selectors):
        res = []
        for selector in selectors:
            if isinstance(self.obj, list):
                res.extend(self._extract_from_list(selector))
            else:
                res.extend(self._extract_from_object(selector))

        # Should we collapse the result list to a singular result?
        # We should, if we filter by only one simple selector (index or key),
        # except when we filter a list with the key selector.
        # (cases: anything[idx], dict["key"]/obj.attr)
        #
        # We are doing this here, and not in selector extractors above, to make
        # combining results from multiple selectors easier.
        singular_result = False
        if len(selectors) == 1:
            is_idx = isinstance(selectors[0], baseinteger)
            is_key = isinstance(selectors[0], basestring)
            not_list = not isinstance(self.obj, list)
            singular_result = is_idx or is_key and not_list

        if len(res) == 0:
            return self.rewrap(empty=True)
        elif len(res) == 1 and singular_result:
            return self.rewrap(obj=res[0])
        else:
            return self.rewrap(obj=res)
    
    def __getattr__(self, name):
        """Handle ``obj.name`` lookups.
        
            obj.key -> similar to obj["key"], but with preferrence on attributes vs items. 
                       If obj is a dict, and "key" is not a valid `dict` attribute, extract
                       dict value under key "key" (or default val). If obj is a list,
                       iterate over all elements, extracting "key" from each element
        """
        return self._get_all(AttrSelector(name))
    
    def __getitem__(self, key):
        """Handle various ``obj[key]`` lookups, including::
        
            obj[2]      -> if obj is list, extract elem with index 2;
                           if obj is dict, extract value under key 2
            obj[1, 2]   -> if obj is list, extract elems with indices 1 and 2;
                           if obj is dict, extract values under keys 1,2 into a new list
            obj[1:5]    -> the same as obj[1,2,3,4,5]
            obj["key"]  -> if obj is dict, extract value under key "key" (or default val),
                           if obj is list, iterate over all elements, extracting "key" from each element
            obj[2, 4:5] -> the same as obj[2,4,5]
            obj[1:, 0]  -> analog to the above, sugar syntax for: obj[1:] + [obj[0]]
            obj["x", "y"]  -> if obj is dict, extract keys "x" and "y" into a new list;
                              if obj is list, iterate over all elements, extracting "x" and "y"
                              from each element into a flat list
            obj["x", "y", 3, ::-1] -> similar to above, extracting "x", "y", 3 and all keys in reverse
        """
        try:
            # accept any iterable for indices
            keys = iter(key)
        except TypeError:
            keys = (key,)

        return self._get_all(*keys)

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return repr(self.value)

    def __iter__(self):
        """Iterate over values plucked so far.
        
        Example::

            for val in pluckable(obj).users.last:
                print(val)
        """
        if self.empty:
            return iter([])

        val = self.value
        try:
            return iter(val)
        except Exception as e:
            return iter([val])

    def items(self):
        """Behave like `dict.items` for mapping types (iterator over (key, value)
        pairs), and like `iter` for sequence types (iterator over values).
        """
        if self.empty:
            return iter([])

        val = self.value
        if hasattr(val, "iteritems"):
            return val.iteritems()
        elif hasattr(val, "items"):
            return val.items()
        else:
            return iter(self)
