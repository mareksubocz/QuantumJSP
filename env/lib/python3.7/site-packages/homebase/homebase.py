# -*- coding: utf-8 -*-
"""
This module provides an API for determining application specific directories for data, config, logs, etc.

public module members:

.. autosummary::

    user_data_dir
    user_config_dir
    user_cache_dir
    user_state_dir
    user_logs_dir
    site_data_dir
    site_config_dir
    site_data_dir_list
    site_config_dir_list

This code is inspired by and builds on top of code from http://github.com/ActiveState/appdirs

"""
# Dev Notes:
# - MSDN on where to store app data files:
#   http://support.microsoft.com/default.aspx?scid=kb;en-us;310294#XSLTH3194121123120121120120
# - Mac OS X: http://developer.apple.com/documentation/MacOSX/Conceptual/BPFileSystem/index.html
# - XDG spec for Un*x: http://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html

import sys
import os
from enum import Enum


class _FolderTypes(Enum):
    data = 1
    config = 2
    cache = 3
    state = 4
    logs = 5


class Platform(Enum):
    WINDOWS = 1
    MACOS = 2
    POSIX = 3


# only calculate this once, at import.
if sys.platform == 'win32':
    platform = Platform.WINDOWS
elif sys.platform == 'darwin':
    platform = Platform.MACOS
else:
    platform = Platform.POSIX


def user_data_dir(app_name, app_author, version=None, roaming=False, use_virtualenv=True, create=True):
    """
    Return the full path to the user data dir for this application, using a virtualenv location as a base, if it is
    exists, and falling back to the host OS's convention if it doesn't.

    If using a virtualenv, the path returned is :bash:`/path/to/virtualenv/data/app_name`

    Typical user data directories are:

        * Mac OS X:               :bash:`~/Library/Application Support/<app_name>`
        * Unix:                   :bash:`~/.local/share/<app_name>    # or $XDG_DATA_HOME/<app_name>, if defined.`
        * Win XP (not roaming):   :bash:`C:\\Documents and Settings\\<username>\\Application Data\\<app_author>\\<app_name>`
        * Win XP (roaming):       :bash:`C:\\Documents and Settings\\<username>\\Local Settings\\Application Data\\<app_author>\\<app_name>`
        * Win 7  (not roaming):   :bash:`C:\\Users\\<username>\\AppData\\Local\\<app_author>\\<app_name>`
        * Win 7  (roaming):       :bash:`C:\\Users\\<username>\\AppData\\Roaming\\<app_author>\\<app_name>`

    For Unix, we follow the XDG spec and support :bash:`$XDG_DATA_HOME`.
    That means, by default :bash:`~/.local/share/<AppName>`.


    Args:
        str app_name: Name of the application. Will be appended to the base user data path.
        str app_author: Only used in Windows when not in a virtualenv, name of the application author.
        str version: If given, the application version identifier will be appended to the app_name.
        bool roaming: roaming appdata directory. That means that for users on a Windows
                      network setup for roaming profiles, this user data will be synchronized on login. See
                      <http://technet.microsoft.com/en-us/library/cc766489(WS.10).aspx> for a discussion of issues.
        bool use_virtualenv: If True and we're running inside of a virtualenv, return a path relative to that
            environment.
        bool create: If True, the folder is created if it does not exist before the path is returned.

    Returns:
        str: the full path to the user data dir for this application.
    """
    return _get_folder(True, _FolderTypes.data, app_name, app_author, version, roaming, use_virtualenv, create)[0]


def user_config_dir(app_name, app_author, version=None, roaming=False, use_virtualenv=True, create=True):
    """
    Return the full path to the user config dir for this application, using a virtualenv location as a base, if it is
    exists, and falling back to the host OS's convention if it doesn't.

    If using a virtualenv, the path returned is :bash:`/path/to/virtualenv/config/app_name`

    Typical user config directories are:
        * Mac OS X:               same as user_data_dir
        * Unix:                   :bash:`~/.config/<AppName> # or in $XDG_CONFIG_HOME, if defined`
        * Win \\*:                  same as user_data_dir

    For Unix, we follow the XDG spec and support $XDG_CONFIG_HOME.
    That means, by default :bash:`~/.config/<AppName>`.

    Args:
        str app_name: Name of the application. Will be appended to the base user config path.
        str app_author: Only used in Windows, name of the application author.
        str version: If given, the application version identifier will be appended to the app_name.
        bool roaming: roaming appdata directory. That means that for users on a Windows
                      network setup for roaming profiles, this user data will be synchronized on login. See
                      <http://technet.microsoft.com/en-us/library/cc766489(WS.10).aspx> for a discussion of issues.
        bool use_virtualenv: If True and we're running inside of a virtualenv, return a path relative to that
            environment.
        bool create: If True, the folder is created if it does not exist before the path is returned.

    Returns:
        str: the full path to the user config dir for this application.
    """
    return _get_folder(True, _FolderTypes.config, app_name, app_author, version, roaming, use_virtualenv, create)[0]


def user_cache_dir(app_name, app_author, version=None, use_virtualenv=True, create=True):
    """
    Return the full path to the user cache dir for this application, using a virtualenv location as a base, if it is
    exists, and falling back to the host OS's convention if it doesn't.

    If using a virtualenv, the path returned is :bash:`/path/to/virtualenv/cache/app_name`

    Typical user cache directories are:
        * Mac OS X:   :bash:`~/Library/Caches/<AppName>`
        * Unix:       :bash:`~/.cache/<AppName> (XDG default)`
        * Win XP:     :bash:`C:\\Documents and Settings\\<username>\\Local Settings\\Application Data\\<AppAuthor>\\<AppName>\\Cache`
        * Vista:      :bash:`C:\\Users\\<username>\\AppData\\Local\\<AppAuthor>\\<AppName>\\Cache`

    Args:
        str app_name: Name of the application. Will be appended to the base user config path.
        str app_author: Only used in Windows, name of the application author.
        str version: If given, the application version identifier will be appended to the app_name.
        bool use_virtualenv: If True and we're running inside of a virtualenv, return a path relative to that
            environment.
        bool create: If True, the folder is created if it does not exist before the path is returned.

    Returns:
        str: the full path to the user cache dir for this application.

    """
    return _get_folder(True, _FolderTypes.cache, app_name, app_author, version, False, use_virtualenv, create)[0]


def user_state_dir(app_name, app_author, version=None, roaming=False, use_virtualenv=True, create=True):
    """
    Return the full path to the user state dir for this application, using a virtualenv location as a base, if it is
    exists, and falling back to the host OS's convention if it doesn't.

    If using a virtualenv, the path returned is :bash:`/path/to/virtualenv/state/app_name`

    Typical user state directories are:
        * Mac OS X:  same as user_data_dir
        * Unix:      :bash:`~/.local/state/<AppName>   # or in $XDG_STATE_HOME, if defined`
        * Win \\*:     same as user_data_dir

    For Unix, we follow this Debian proposal https://wiki.debian.org/XDGBaseDirectorySpecification#state
    to extend the XDG spec and support $XDG_STATE_HOME. That means, by default :bash:`~/.local/state/<AppName>`.

    Args:
        str app_name: Name of the application. Will be appended to the base user config path.
        str app_author: Only used in Windows, name of the application author.
        str version: If given, the application version identifier will be appended to the app_name.
        bool roaming: roaming appdata directory. That means that for users on a Windows
                      network setup for roaming profiles, this user data will be synchronized on login. See
                      <http://technet.microsoft.com/en-us/library/cc766489(WS.10).aspx> for a discussion of issues.
        bool use_virtualenv: If True and we're running inside of a virtualenv, return a path relative to that
            environment.
        bool create: If True, the folder is created if it does not exist before the path is returned.

    Returns:
        str: the full path to the user state dir for this application.
    """
    return _get_folder(True, _FolderTypes.state, app_name, app_author, version, roaming, use_virtualenv, create)[0]


def user_logs_dir(app_name, app_author, version=None, use_virtualenv=True, create=True):
    """
    Return the full path to the user log dir for this application, using a virtualenv location as a base, if it is
    exists, and falling back to the host OS's convention if it doesn't.

    If using a virtualenv, the path returned is :bash:`:bash:`/path/to/virtualenv/log/app_name``

    Typical user log directories are:
        * Mac OS X:   :bash:`~/Library/Logs/<AppName>`
        * Unix:       :bash:`~/.cache/<AppName>/log  # or under $XDG_CACHE_HOME if defined`
        * Win XP:     :bash:`C:\\Documents and Settings\\<username>\\Local Settings\\Application Data\\<AppAuthor>\\<AppName>\\Logs`
        * Vista:      :bash:`C:\\Users\\<username>\\AppData\\Local\\<AppAuthor>\\<AppName>\\Logs`

    Args:
        str app_name: Name of the application. Will be appended to the base user config path.
        str app_author: Only used in Windows, name of the application author.
        str version: If given, the application version identifier will be appended to the app_name.
        bool use_virtualenv: If True and we're running inside of a virtualenv, return a path relative to that
            environment.
        bool create: If True, the folder is created if it does not exist before the path is returned.

    Returns:
        str: the full path to the user log dir for this application.
    """
    return _get_folder(True, _FolderTypes.logs, app_name, app_author, version, False, use_virtualenv, create)[0]


def site_data_dir(app_name, app_author, version=None, use_virtualenv=True, create=False):
    """
    Return the full path to the OS wide data dir for this application.

    Typical site data directories are:
        * Mac OS X:   :bash:`/Library/Application Support/<AppName>`
        * Unix:       :bash:`/usr/local/share/<AppName> or /usr/share/<AppName>`
        * Win XP:     :bash:`C:\\Documents and Settings\\All Users\\Application Data\\<AppAuthor>\\<AppName>`
        * Vista:      :bash:`(Fail! "C:\\ProgramData" is a hidden *system* directory on Vista.)`
        * Win 7:      :bash:`C:\\ProgramData\\<AppAuthor>\\<AppName>   # Hidden, but writeable on Win 7.`

    For \*nix, this is using the :bash:`$XDG_DATA_DIRS` default.

    .. Note::
        On linux, the $XDG_DATA_DIRS environment variable may contain a list. `site_data_dir` returns the first
        element of this list. If you want access to the whole list, use :func:`site_data_dir_list`

    .. WARNING::
        Do not use this on Windows Vista. See the Vista-Fail note above for why.

    Args:
        str app_name: Name of the application. Will be appended to the base user config path.
        str app_author: Only used in Windows, name of the application author.
        str version: If given, the application version identifier will be appended to the app_name.
        bool use_virtualenv: If True and we're running inside of a virtualenv, return a path relative to that
            environment.
        bool create: If True, the folder is created if it does not exist before the path is returned.

    Returns:
        str: the full path to the site data dir for this application.
    """
    return _get_folder(False, _FolderTypes.data, app_name, app_author, version, False, use_virtualenv, create)[0]


def site_data_dir_list(app_name, app_author, version=None, use_virtualenv=True, create=False):
    """
    Return the list of full path to the OS wide data directories for this application.

    Typical site data directories are:
        * Mac OS X:   :bash:`/Library/Application Support/<AppName>`
        * Unix:       :bash:`/usr/local/share/<AppName> or /usr/share/<AppName>`
        * Win XP:     :bash:`C:\\Documents and Settings\\All Users\\Application Data\\<AppAuthor>\\<AppName>`
        * Vista:      :bash:`(Fail! "C:\\ProgramData" is a hidden *system* directory on Vista.)`
        * Win 7:      :bash:`C:\\ProgramData\\<AppAuthor>\\<AppName>   # Hidden, but writeable on Win 7.`

    For \*nix, this is using the :bash:`$XDG_DATA_DIRS` default.

    .. WARNING::
        Do not use this on Windows Vista. See the Vista-Fail note above for why.

    Args:
        str app_name: Name of the application. Will be appended to the base user config path.
        str app_author: Only used in Windows, name of the application author.
        str version: If given, the application version identifier will be appended to the app_name.
        bool use_virtualenv: If True and we're running inside of a virtualenv, return a path relative to that
            environment.
        bool create: If True, the folder is created if it does not exist before the path is returned.

    Returns:
        list: A list to the full paths for site data directories for this application.
    """
    return _get_folder(False, _FolderTypes.data, app_name, app_author, version, False, use_virtualenv, create)


def site_config_dir(app_name, app_author, version=None, use_virtualenv=True, create=False):
    """
    Return the full path to the OS wide config dir for this application.

    Typical site data directories are:
        * Mac OS X:   :bash:`/Library/Application Support/<AppName>`
        * Unix:       :bash:`/usr/local/share/<AppName> or /usr/share/<AppName>`
        * Win XP:     :bash:`C:\\Documents and Settings\\All Users\\Application Data\\<AppAuthor>\\<AppName>`
        * Vista:      :bash:`(Fail! "C:\\ProgramData" is a hidden *system* directory on Vista.)`
        * Win 7:      :bash:`C:\\ProgramData\\<AppAuthor>\\<AppName>   # Hidden, but writeable on Win 7.`

    For \*nix, this is using the :bash:`$XDG_DATA_DIRS` default.

    .. Note::
        On linux, the $XDG_CONFIG_DIRS environment variable may contain a list. `site_config_dir` returns the first
        element of this list. If you want access to the whole list, use :func:`site_config_dir_list`

    .. WARNING::
        Do not use this on Windows Vista. See the Vista-Fail note above for why.

    Args:
        str app_name: Name of the application. Will be appended to the base user config path.
        str app_author: Only used in Windows, name of the application author.
        str version: If given, the application version identifier will be appended to the app_name.
        bool use_virtualenv: If True and we're running inside of a virtualenv, return a path relative to that
            environment.
        bool create: If True, the folder is created if it does not exist before the path is returned.

    Returns:
        str: the full path to the site config dir for this application.
    """
    return _get_folder(False, _FolderTypes.config, app_name, app_author, version, False, use_virtualenv, create)[0]


def site_config_dir_list(app_name, app_author, version=None, use_virtualenv=True, create=False):
    """
    Return the list of full path to the OS wide data directories for this application.

    Typical site data directories are:
        * Mac OS X:   :bash:`/Library/Application Support/<AppName>`
        * Unix:       :bash:`/usr/local/share/<AppName> or /usr/share/<AppName>`
        * Win XP:     :bash:`C:\\Documents and Settings\\All Users\\Application Data\\<AppAuthor>\\<AppName>`
        * Vista:      :bash:`(Fail! "C:\\ProgramData" is a hidden *system* directory on Vista.)`
        * Win 7:      :bash:`C:\\ProgramData\\<AppAuthor>\\<AppName>   # Hidden, but writeable on Win 7.`

    For \*nix, this is using the :bash:`$XDG_DATA_DIRS` default.

    .. WARNING::
        Do not use this on Windows Vista. See the Vista-Fail note above for why.

    Args:
        str app_name: Name of the application. Will be appended to the base user config path.
        str app_author: Only used in Windows, name of the application author.
        str version: If given, the application version identifier will be appended to the app_name.
        bool use_virtualenv: If True and we're running inside of a virtualenv, return a path relative to that
            environment.
        bool create: If True, the folder is created if it does not exist before the path is returned.

    Returns:
        list: A list to the full paths for site data directories for this application.
    """
    return _get_folder(False, _FolderTypes.config, app_name, app_author, version, False, use_virtualenv, create)


def _get_folder(user, folder_type, app_name, app_author, version, roaming, use_virtualenv, create):
    """
    Get the directory corresponding to the appropriate folder type and operating system.
    The folder is returned, with the app_name, and in the case of windows app_author appended to it.
    If version is not None, it is appended to app_name to allow for multiple versions to run in the same place.

    Since some operating systems have more than one appropriate folder of a given time (e.g. site_data on linux),
    A list is returned. It is up to calling functions to handle the contents of this list.

    Args:
        _FolderTypes folder_type: Folder type value.
        str app_name: Name of the app, the returned dir has os.path.basename == app_name
        str app_author: Name of app author, only used in Windows.
        str version: App version, appended to app_name
        bool roaming: Whether or not the Windows user is roaming.
        bool use_virtualenv: If True and a virtualenv is activated, use the virtualenv path instead of the OS
            convention. Note: This is ignored for site directories, for obvious reasons.
        bool create: If True, create the directory if it doesn't exist. In the case of lists of directories, all folders
            are created.

    Returns:
        list: A list of paths.

    """
    if user and use_virtualenv and _in_virtualenv():
        sub_folder = folder_type.name  # data | config | state | log | cache
        paths = [os.path.join(sys.prefix, sub_folder)]

    elif platform == Platform.WINDOWS:
        if user:
            if folder_type in [_FolderTypes.data, _FolderTypes.config, _FolderTypes.state]:
                paths = [os.path.normpath(_get_win_folder(site=False, roaming=roaming, app_author=app_author))]
            elif folder_type == _FolderTypes.cache:
                # we'll follow the MSDN recommendation on local data, but since they're mum on caches,
                # we'll put them in LOCAL_APPDATA/app_author/Caches.
                path = os.path.normpath(_get_win_folder(site=False, roaming=False, app_author=app_author))
                paths = [os.path.join(path, 'Caches')]
            else:  # folder_type == _FolderTypes.logs:
                # Similar issue as with user caches. MSDN is no help.
                path = os.path.normpath(_get_win_folder(site=False, roaming=False, app_author=app_author))
                paths = [os.path.join(path, 'Logs')]
        elif folder_type in [_FolderTypes.data, _FolderTypes.config]:
            paths = [os.path.normpath(_get_win_folder(site=True, roaming=roaming, app_author=app_author))]
        else:
            raise RuntimeError('Unknown folder type: {}, user: {}'.format(folder_type.name, user))

    elif platform == Platform.MACOS:
        if user:
            if folder_type in [_FolderTypes.data, _FolderTypes.config, _FolderTypes.state]:
                paths = [os.path.expanduser('~/Library/Application Support')]
            elif folder_type == _FolderTypes.cache:
                paths = [os.path.expanduser('~/Library/Caches')]
            else:  # folder_type == _FolderTypes.logs:
                paths = [os.path.expanduser('~/Library/Logs')]
        elif folder_type in [_FolderTypes.data, _FolderTypes.config]:
            paths = [os.path.expanduser('/Library/Application Support')]
        else:
            raise RuntimeError('Unknown folder type: {}, user: {}'.format(folder_type.name, user))

    elif platform == Platform.POSIX:
        if user:
            if folder_type == _FolderTypes.data:
                paths = [os.getenv('XDG_DATA_HOME', os.path.expanduser("~/.local/share"))]
            elif folder_type == _FolderTypes.config:
                paths = [os.getenv('XDG_CONFIG_HOME', os.path.expanduser("~/.config"))]
            elif folder_type == _FolderTypes.state:
                paths = [os.getenv('XDG_STATE_HOME', os.path.expanduser("~/.local/state"))]
            elif folder_type == _FolderTypes.cache:
                paths = [os.getenv('XDG_CACHE_HOME', os.path.expanduser('~/.cache'))]
            else:  # folder_type == _FolderTypes.logs:
                paths = [os.path.expanduser('~/.log')]
        elif folder_type == _FolderTypes.data:
            path = os.getenv('XDG_DATA_DIRS', os.pathsep.join(['/usr/local/share', '/usr/share']))
            paths = [os.path.expanduser(x.rstrip(os.sep)) for x in path.split(os.pathsep)]
        elif folder_type == _FolderTypes.config:
            path = os.getenv('XDG_CONFIG_DIRS', '/etc/xdg')
            paths = [os.path.expanduser(x.rstrip(os.sep)) for x in path.split(os.pathsep)]
        else:
            raise RuntimeError('Unknown folder type: {}, user: {}'.format(folder_type.name, user))

    else:
        raise RuntimeError('Unsupported operating system: {}'.format(sys.platform))

    final_paths = []
    for path in paths:
        final_path = os.path.join(path, app_name)
        if version is not None:
            final_path = '{}_{}'.format(final_path, version)

        if create and not os.path.exists(final_path):
            os.makedirs(final_path)

        final_paths.append(final_path)

    return final_paths


def _in_virtualenv():
    """
    Determine if we're in a virtual env.

    If sys.real_prefix exists, we are in a virtualenv, and sys.prefix is the virtualenv path, while
    sys.real_prefix is the 'system' python.
    if sys.real_prefix does not exist, it could be because we're in python 3 and the user is using
    the built in venv module instead of virtualenv. In this case a sys.base_prefix attribute always exists, and is
    is different from sys.prefix.

    In either case, the path we want in case we are in a virtualenv is sys.prefix.

    Returns:
        bool: True if we are running in a virtual environment, and False otherwise.
    """
    return hasattr(sys, 'real_prefix') or hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix


def _get_win_folder(site, roaming, app_author):
    import ctypes

    if not isinstance(app_author, str) or app_author == '':
        raise RuntimeError('On Windows, app_author must be a non-empty string.')

    # As of Windows Vista, these values have been replaced by KNOWNFOLDERID values.
    # The CSIDL system is supported under Windows Vista, 8 and 10 for compatibility reasons,
    # And the function SHGetFolderPath maps these values to SHGetKnownFolderID. A future version of this
    # library will need to updated if support for CSIDL is ever dropped.
    csidl_consts = {
        "CSIDL_APPDATA": 26,
        "CSIDL_COMMON_APPDATA": 35,
        "CSIDL_LOCAL_APPDATA": 28,
    }

    if site:
        csidl_const = csidl_consts['CSIDL_COMMON_APPDATA']
    elif roaming:
        csidl_const = csidl_consts['CSIDL_APPDATA']
    else:
        csidl_const = csidl_consts['CSIDL_LOCAL_APPDATA']

    buf = ctypes.create_unicode_buffer(1024)
    ctypes.windll.shell32.SHGetFolderPathW(None, csidl_const, None, 0, buf)

    # Downgrade to short path name if have highbit chars. See
    # http://bugs.activestate.com/show_bug.cgi?id=85099.
    # Oren: This bug is not publicly available!
    has_high_char = False
    for c in buf:
        if ord(c) > 255:
            has_high_char = True
            break
    if has_high_char:
        buf2 = ctypes.create_unicode_buffer(1024)
        if ctypes.windll.kernel32.GetShortPathNameW(buf.value, buf2, 1024):
            buf = buf2

    return os.path.join(buf.value, app_author)
