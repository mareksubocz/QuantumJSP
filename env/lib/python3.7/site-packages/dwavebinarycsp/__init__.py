# Copyright 2018 D-Wave Systems Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
# ================================================================================================

from dwavebinarycsp.compilers import *
import dwavebinarycsp.compilers

from dwavebinarycsp.core import *
import dwavebinarycsp.core

from dwavebinarycsp.reduction import *
import dwavebinarycsp.reduction

import dwavebinarycsp.exceptions

import dwavebinarycsp.factories

from dwavebinarycsp.io import *
import dwavebinarycsp.io

from dwavebinarycsp.package_info import __version__, __author__, __authoremail__, __description__

import dwavebinarycsp.testing

# import dimod.Vartype, dimod.SPIN and dimod.BINARY into dwavebinarycsp namespace for convenience
from dimod import Vartype, SPIN, BINARY


def assert_penaltymodel_factory_available():
    """For `dwavebinarycsp` to be functional, at least one penalty model factory
    has to be installed. See discussion in setup.py for details.
    """

    from pkg_resources import iter_entry_points
    from penaltymodel.core import FACTORY_ENTRYPOINT
    from itertools import chain

    supported = ('maxgap', 'mip')
    factories = chain(*(iter_entry_points(FACTORY_ENTRYPOINT, name) for name in supported))

    try:
        next(factories)
    except StopIteration:
        raise AssertionError(
            "To use 'dwavebinarycsp', at least one penaltymodel factory must be installed. "
            "Try {}.".format(
                " or ".join("'pip install dwavebinarycsp[{}]'".format(name) for name in supported)
            ))

# Check that at least one of penaltymodel-{mip,maxgap} is installed.
# Raise warning on import, error on first use (stitch).
try:
    assert_penaltymodel_factory_available()
except AssertionError as e:
    import warnings
    warnings.warn(str(e), RuntimeWarning)
