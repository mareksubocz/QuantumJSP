"""
Test homebase.

Since some of the homebase functionality is OS specific, this module can only get 100% coverage if it is run on
all three operating systems: Windows, Linux, and macOS. Thus, coverage tools will need to merge reports from different
runs.

From a functional perspective, the only thing that changes across operating systems are expected results.
As such, the strategy for testing is as follows:

1. A base class TestHomebase defines basic expectations and all of the unit tests common to all three operating
   systems.
2. A class for handling virtualenv tests, TestHomebaseVirtualEnv that modifies the expected path for each
   OS to expect the appropriate virtualenv base dir, and runs all tests of TestHomebase by inheriting from it.
3. The base class TestHomebase tests linux in the case where the XDG variables are not set. Another class
   TestHomebaseLinuxXDG sets these variables and the expected paths and reruns the tests by inheriting from
   TestHomebase.
4.A class for Windows TestHomebaseWindows adds tests for roaming and app_author values.

To run the tests against linux, you can use the accompanying Dockerfile.

"""
import os
import sys
import shutil
import unittest

import virtualenv
import homebase

_PY2 = sys.version_info[0] == 2
if _PY2:
    def itervalues(d):
        return d.itervalues()
else:
    def itervalues(d):
        return iter(d.values())


class TestHomebase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.app_name = "test_app"
        self.app_author = 'for_windows_only'

        # we can't just use sys.platform because on linux it could be either linux2 or just linux
        # (https://docs.python.org/2/library/sys.html#sys.platform)
        # If we're masking linux, might as well mask darwin with mac os.
        if sys.platform.startswith('linux'):
            self.platform = 'linux'
        elif sys.platform == 'darwin':
            self.platform = 'mac_os'
        else:
            self.platform = 'windows'

        self.base_paths = self._expected_base_paths()

    def _expected_base_paths(self):
        mac_os_app_support = os.path.expanduser('~/Library/Application Support/')
        mac_os_site_app_support = '/Library/Application Support'
        base_paths = {
            'mac_os': {
                'user_data': mac_os_app_support,
                'user_config': mac_os_app_support,
                'user_state': mac_os_app_support,
                'user_cache': os.path.expanduser('~/Library/Caches'),
                'user_log': os.path.expanduser('~/Library/Logs'),
                'site_data': [mac_os_site_app_support],
                'site_config': [mac_os_site_app_support]
            },
            'linux': {
                'user_data': os.path.expanduser("~/.local/share"),
                'user_config': os.path.expanduser('~/.config'),
                'user_state': os.path.expanduser('~/.local/state'),
                'user_cache': os.path.expanduser('~/.cache'),
                'user_log': os.path.expanduser('~/.log'),
                'site_data': ['/usr/local/share', '/usr/share'],
                'site_config': ['/etc/xdg']
            },
            'windows': self._windows_base_paths()
        }

        # add virtualenv expectations. When there is no actual virtualenv, we expect the use_virtualenv parameter
        # to do nothing.
        for paths in itervalues(base_paths):
            paths['user_data_venv'] = paths['user_data']
            paths['user_config_venv'] = paths['user_config']
            paths['user_state_venv'] = paths['user_state']
            paths['user_cache_venv'] = paths['user_cache']
            paths['user_log_venv'] = paths['user_log']

        return base_paths

    def _windows_base_paths(self):
        windows_username = os.getenv('username')
        base_paths = {
            'user_data': '',
            'user_config': '',
            'user_state': '',
            'user_cache': '',
            'user_log': '',
            'site_data': '',
            'site_config': ''

        }
        if windows_username is not None:
            windows_absolute_path = os.path.join('C:', os.sep)
            windows_base_path = os.path.join(windows_absolute_path, 'Users', windows_username, 'AppData', 'Local')

            # add windows expectations.
            base_paths['user_data'] = os.path.join(windows_base_path, self.app_author)
            base_paths['user_config'] = os.path.join(windows_base_path, self.app_author)
            base_paths['user_state'] = os.path.join(windows_base_path, self.app_author)
            base_paths['user_cache'] = os.path.join(windows_base_path, self.app_author, 'Caches')
            base_paths['user_log'] = os.path.join(windows_base_path, self.app_author, 'Logs')
            base_paths['site_data'] = [os.path.join(windows_absolute_path, 'ProgramData', self.app_author)]
            base_paths['site_config'] = [os.path.join(windows_absolute_path, 'ProgramData', self.app_author)]

        return base_paths

    @staticmethod
    def _setup_linux_xdg_vars():
        test_dir = os.path.abspath(os.path.dirname(__file__))
        os.environ['XDG_DATA_HOME'] = os.path.join(test_dir, '.local/share')
        os.environ['XDG_CONFIG_HOME'] = os.path.join(test_dir, '.config')
        os.environ['XDG_STATE_HOME'] = os.path.join(test_dir, '.local/state')
        os.environ['XDG_CACHE_HOME'] = os.path.join(test_dir, '.cache')
        os.environ['XDG_DATA_DIRS'] = os.pathsep.join([os.path.join(test_dir, '.site/data'),
                                                       os.path.join(test_dir, '.site/data2')])
        os.environ['XDG_CONFIG_DIRS'] = os.pathsep.join([os.path.join(test_dir, '.site/config'),
                                                         os.path.join(test_dir, '.site/config2')])

    @staticmethod
    def _clear_linux_xdg_vars():
        var_names = ['XDG_DATA_HOME', 'XDG_CONFIG_HOME', 'XDG_STATE_HOME', 'XDG_CACHE_HOME', 'XDG_DATA_DIRS',
                     'XDG_CONFIG_DIRS']
        for var in var_names:
            if var in os.environ:
                del os.environ[var]

    @classmethod
    def setUpClass(cls):
        cls._clear_linux_xdg_vars()

    #####################################################
    # user_data_dir.
    #####################################################
    def test_user_data_no_version_no_venv_no_create(self):
        expected = os.path.join(self.base_paths[self.platform]['user_data'], self.app_name)
        self.assertEqual(expected,
                         homebase.user_data_dir(self.app_name, app_author=self.app_author, version=None,
                                                use_virtualenv=False, create=False))

    def test_user_data_no_version_no_venv_create(self):
        expected = os.path.join(self.base_paths[self.platform]['user_data'], self.app_name)
        if os.path.exists(expected):
            shutil.rmtree(expected)
        self.assertEqual(expected, homebase.user_data_dir(self.app_name, app_author=self.app_author, version=None,
                                                          use_virtualenv=False, create=True))
        self.assertTrue(os.path.exists(expected))
        shutil.rmtree(expected)

    def test_user_data_no_version_venv_no_create(self):
        expected = os.path.join(self.base_paths[self.platform]['user_data_venv'], self.app_name)
        self.assertEqual(expected, homebase.user_data_dir(self.app_name, app_author=self.app_author, version=None,
                                                          use_virtualenv=True, create=False))

    def test_user_data_no_version_venv_create(self):
        expected = os.path.join(self.base_paths[self.platform]['user_data_venv'], self.app_name)
        if os.path.exists(expected):
            shutil.rmtree(expected)
        self.assertEqual(expected, homebase.user_data_dir(self.app_name, app_author=self.app_author, version=None,
                                                          use_virtualenv=True, create=True))
        self.assertTrue(os.path.exists(expected))
        shutil.rmtree(expected)

    def test_user_data_version_no_venv_no_create(self):
        version = "1.0"
        expected = os.path.join(self.base_paths[self.platform]['user_data'], '{}_{}'.format(self.app_name, version))
        self.assertEqual(expected,
                         homebase.user_data_dir(self.app_name, app_author=self.app_author, version=version,
                                                use_virtualenv=False, create=False))

    def test_user_data_version_no_venv_create(self):
        version = "1.0"
        expected = os.path.join(self.base_paths[self.platform]['user_data'], '{}_{}'.format(self.app_name, version))
        if os.path.exists(expected):
            shutil.rmtree(expected)
        result = homebase.user_data_dir(self.app_name, app_author=self.app_author, version=version, use_virtualenv=False,
                                        create=True)
        self.assertEqual(expected, result)
        self.assertTrue(os.path.exists(expected))
        shutil.rmtree(expected)

    def test_user_data_version_venv_no_create(self):
        version = '1.0'
        expected = os.path.join(self.base_paths[self.platform]['user_data_venv'],
                                '{}_{}'.format(self.app_name, version))
        result = homebase.user_data_dir(self.app_name, app_author=self.app_author, version=version, use_virtualenv=True,
                                        create=False)
        self.assertEqual(expected, result)

    def test_user_data_version_venv_create(self):
        version = '1.0'
        expected = os.path.join(self.base_paths[self.platform]['user_data_venv'],
                                '{}_{}'.format(self.app_name, version))
        if os.path.exists(expected):
            shutil.rmtree(expected)
        self.assertFalse(os.path.exists(expected))
        result = homebase.user_data_dir(self.app_name, app_author=self.app_author, version=version, use_virtualenv=True,
                                        create=True)
        self.assertEqual(expected, result)
        self.assertTrue(os.path.exists(expected))
        shutil.rmtree(expected)

    #####################################################
    # user_cache_dir.
    #####################################################
    def test_user_cache_no_version_no_venv_no_create(self):
        expected = os.path.join(self.base_paths[self.platform]['user_cache'], self.app_name)
        self.assertEqual(expected,
                         homebase.user_cache_dir(self.app_name, app_author=self.app_author, version=None,
                                                 use_virtualenv=False, create=False))

    def test_user_cache_no_version_no_venv_create(self):
        expected = os.path.join(self.base_paths[self.platform]['user_cache'], self.app_name)
        if os.path.exists(expected):
            shutil.rmtree(expected)
        self.assertEqual(expected,
                         homebase.user_cache_dir(self.app_name, app_author=self.app_author, version=None,
                                                 use_virtualenv=False, create=True))
        self.assertTrue(os.path.exists(expected))
        shutil.rmtree(expected)

    def test_user_cache_no_version_venv_no_create(self):
        expected = os.path.join(self.base_paths[self.platform]['user_cache_venv'], self.app_name)
        self.assertEqual(expected,
                         homebase.user_cache_dir(self.app_name, app_author=self.app_author, version=None,
                                                 use_virtualenv=True, create=False))

    def test_user_cache_no_version_venv_create(self):
        expected = os.path.join(self.base_paths[self.platform]['user_cache_venv'], self.app_name)
        if os.path.exists(expected):
            shutil.rmtree(expected)
        self.assertEqual(expected, homebase.user_cache_dir(self.app_name, app_author=self.app_author, version=None,
                                                           use_virtualenv=True, create=True))
        self.assertTrue(os.path.exists(expected))
        shutil.rmtree(expected)

    def test_user_cache_version_no_venv_no_create(self):
        version = "1.0"
        expected = os.path.join(self.base_paths[self.platform]['user_cache'], '{}_{}'.format(self.app_name, version))
        self.assertEqual(expected,
                         homebase.user_cache_dir(self.app_name, app_author=self.app_author, version=version,
                                                 use_virtualenv=False, create=False))

    def test_user_cache_version_no_venv_create(self):
        version = "1.0"
        expected = os.path.join(self.base_paths[self.platform]['user_cache'], '{}_{}'.format(self.app_name, version))
        if os.path.exists(expected):
            shutil.rmtree(expected)
        result = homebase.user_cache_dir(self.app_name, app_author=self.app_author, version=version, use_virtualenv=False,
                                         create=True)
        self.assertEqual(expected, result)
        self.assertTrue(os.path.exists(expected))
        shutil.rmtree(expected)

    def test_user_cache_version_venv_no_create(self):
        version = '1.0'
        expected = os.path.join(self.base_paths[self.platform]['user_cache_venv'],
                                '{}_{}'.format(self.app_name, version))
        result = homebase.user_cache_dir(self.app_name, app_author=self.app_author, version=version, use_virtualenv=True,
                                         create=False)
        self.assertEqual(expected, result)

    def test_user_cache_version_venv_create(self):
        version = '1.0'
        expected = os.path.join(self.base_paths[self.platform]['user_cache_venv'],
                                '{}_{}'.format(self.app_name, version))
        if os.path.exists(expected):
            shutil.rmtree(expected)
        self.assertFalse(os.path.exists(expected))
        result = homebase.user_cache_dir(self.app_name, app_author=self.app_author, version=version, use_virtualenv=True,
                                         create=True)
        self.assertEqual(expected, result)
        self.assertTrue(os.path.exists(expected))
        shutil.rmtree(expected)

    #####################################################
    # user_config_dir
    #####################################################
    def test_user_config_no_version_no_venv_no_create(self):
        expected = os.path.join(self.base_paths[self.platform]['user_config'], self.app_name)
        self.assertEqual(expected,
                         homebase.user_config_dir(self.app_name, app_author=self.app_author, version=None,
                                                  use_virtualenv=False, create=False))

    def test_user_config_no_version_no_venv_create(self):
        expected = os.path.join(self.base_paths[self.platform]['user_config'], self.app_name)
        if os.path.exists(expected):
            shutil.rmtree(expected)
        self.assertEqual(expected,
                         homebase.user_config_dir(self.app_name, app_author=self.app_author, version=None,
                                                  use_virtualenv=False, create=True))
        self.assertTrue(os.path.exists(expected))
        shutil.rmtree(expected)

    def test_user_config_no_version_venv_no_create(self):
        expected = os.path.join(self.base_paths[self.platform]['user_config_venv'], self.app_name)
        self.assertEqual(expected,
                         homebase.user_config_dir(self.app_name, app_author=self.app_author, version=None,
                                                  use_virtualenv=True, create=False))

    def test_user_config_no_version_venv_create(self):
        expected = os.path.join(self.base_paths[self.platform]['user_config_venv'], self.app_name)
        if os.path.exists(expected):
            shutil.rmtree(expected)
        self.assertEqual(expected,
                         homebase.user_config_dir(self.app_name, app_author=self.app_author, version=None,
                                                  use_virtualenv=True, create=True))
        self.assertTrue(os.path.exists(expected))
        shutil.rmtree(expected)

    def test_user_config_version_no_venv_no_create(self):
        version = "1.0"
        expected = os.path.join(self.base_paths[self.platform]['user_config'], '{}_{}'.format(self.app_name, version))
        self.assertEqual(expected,
                         homebase.user_config_dir(self.app_name, app_author=self.app_author, version=version,
                                                  use_virtualenv=False, create=False))

    def test_user_config_version_no_venv_create(self):
        version = "1.0"
        expected = os.path.join(self.base_paths[self.platform]['user_config'], '{}_{}'.format(self.app_name, version))
        if os.path.exists(expected):
            shutil.rmtree(expected)
        result = homebase.user_config_dir(self.app_name, app_author=self.app_author, version=version,
                                          use_virtualenv=False, create=True)
        self.assertEqual(expected, result)
        self.assertTrue(os.path.exists(expected))
        shutil.rmtree(expected)

    def test_user_config_version_venv_no_create(self):
        version = '1.0'
        expected = os.path.join(self.base_paths[self.platform]['user_config_venv'],
                                '{}_{}'.format(self.app_name, version))
        result = homebase.user_config_dir(self.app_name, app_author=self.app_author, version=version, use_virtualenv=True,
                                          create=False)
        self.assertEqual(expected, result)

    def test_user_config_version_venv_create(self):
        version = '1.0'
        expected = os.path.join(self.base_paths[self.platform]['user_config_venv'],
                                '{}_{}'.format(self.app_name, version))
        if os.path.exists(expected):
            shutil.rmtree(expected)
        self.assertFalse(os.path.exists(expected))
        result = homebase.user_config_dir(self.app_name, app_author=self.app_author, version=version, use_virtualenv=True,
                                          create=True)
        self.assertEqual(expected, result)
        self.assertTrue(os.path.exists(expected))
        shutil.rmtree(expected)

    #####################################################
    # user_state_dir
    #####################################################
    def test_user_state_no_version_no_venv_no_create(self):
        expected = os.path.join(self.base_paths[self.platform]['user_state'], self.app_name)
        self.assertEqual(expected,
                         homebase.user_state_dir(self.app_name, app_author=self.app_author, version=None,
                                                 use_virtualenv=False, create=False))

    def test_user_state_no_version_no_venv_create(self):
        expected = os.path.join(self.base_paths[self.platform]['user_state'], self.app_name)
        if os.path.exists(expected):
            shutil.rmtree(expected)
        self.assertEqual(expected,
                         homebase.user_state_dir(self.app_name, app_author=self.app_author, version=None,
                                                 use_virtualenv=False, create=True))
        self.assertTrue(os.path.exists(expected))
        shutil.rmtree(expected)

    def test_user_state_no_version_venv_no_create(self):
        expected = os.path.join(self.base_paths[self.platform]['user_state_venv'], self.app_name)
        self.assertEqual(expected,
                         homebase.user_state_dir(self.app_name, app_author=self.app_author, version=None,
                                                 use_virtualenv=True, create=False))

    def test_user_state_no_version_venv_create(self):
        expected = os.path.join(self.base_paths[self.platform]['user_state_venv'], self.app_name)
        if os.path.exists(expected):
            shutil.rmtree(expected)
        self.assertEqual(expected, homebase.user_state_dir(self.app_name, app_author=self.app_author, version=None,
                                                           use_virtualenv=True, create=True))
        self.assertTrue(os.path.exists(expected))
        shutil.rmtree(expected)

    def test_user_state_version_no_venv_no_create(self):
        version = "1.0"
        expected = os.path.join(self.base_paths[self.platform]['user_state'], '{}_{}'.format(self.app_name, version))
        self.assertEqual(expected,
                         homebase.user_state_dir(self.app_name, app_author=self.app_author, version=version,
                                                 use_virtualenv=False, create=False))

    def test_user_state_version_no_venv_create(self):
        version = "1.0"
        expected = os.path.join(self.base_paths[self.platform]['user_state'], '{}_{}'.format(self.app_name, version))
        if os.path.exists(expected):
            shutil.rmtree(expected)
        result = homebase.user_state_dir(self.app_name, app_author=self.app_author, version=version, use_virtualenv=False,
                                         create=True)
        self.assertEqual(expected, result)
        self.assertTrue(os.path.exists(expected))
        shutil.rmtree(expected)

    def test_user_state_version_venv_no_create(self):
        version = '1.0'
        expected = os.path.join(self.base_paths[self.platform]['user_state_venv'],
                                '{}_{}'.format(self.app_name, version))
        result = homebase.user_state_dir(self.app_name, app_author=self.app_author, version=version, use_virtualenv=True,
                                         create=False)
        self.assertEqual(expected, result)

    def test_user_state_version_venv_create(self):
        version = '1.0'
        expected = os.path.join(self.base_paths[self.platform]['user_state_venv'],
                                '{}_{}'.format(self.app_name, version))
        if os.path.exists(expected):
            shutil.rmtree(expected)
        self.assertFalse(os.path.exists(expected))
        result = homebase.user_state_dir(self.app_name, app_author=self.app_author, version=version, use_virtualenv=True,
                                         create=True)
        self.assertEqual(expected, result)
        self.assertTrue(os.path.exists(expected))
        shutil.rmtree(expected)

    #####################################################
    # user_logs_dir
    #####################################################
    def test_user_log_no_version_no_venv_no_create(self):
        expected = os.path.join(self.base_paths[self.platform]['user_log'], self.app_name)
        self.assertEqual(expected, homebase.user_logs_dir(self.app_name, app_author=self.app_author, version=None,
                                                          use_virtualenv=False, create=False))

    def test_user_log_no_version_no_venv_create(self):
        expected = os.path.join(self.base_paths[self.platform]['user_log'], self.app_name)
        if os.path.exists(expected):
            shutil.rmtree(expected)
        self.assertEqual(expected, homebase.user_logs_dir(self.app_name, app_author=self.app_author, version=None,
                                                          use_virtualenv=False, create=True))
        self.assertTrue(os.path.exists(expected))
        shutil.rmtree(expected)

    def test_user_log_no_version_venv_no_create(self):
        expected = os.path.join(self.base_paths[self.platform]['user_log_venv'], self.app_name)
        self.assertEqual(expected, homebase.user_logs_dir(self.app_name, app_author=self.app_author, version=None,
                                                          use_virtualenv=True, create=False))

    def test_user_log_no_version_venv_create(self):
        expected = os.path.join(self.base_paths[self.platform]['user_log_venv'], self.app_name)
        if os.path.exists(expected):
            shutil.rmtree(expected)
        self.assertEqual(expected, homebase.user_logs_dir(self.app_name, app_author=self.app_author, version=None,
                                                          use_virtualenv=True, create=True))
        self.assertTrue(os.path.exists(expected))
        shutil.rmtree(expected)

    def test_user_log_version_no_venv_no_create(self):
        version = "1.0"
        expected = os.path.join(self.base_paths[self.platform]['user_log'], '{}_{}'.format(self.app_name, version))
        self.assertEqual(expected,
                         homebase.user_logs_dir(self.app_name, app_author=self.app_author, version=version,
                                                use_virtualenv=False, create=False))

    def test_user_log_version_no_venv_create(self):
        version = "1.0"
        expected = os.path.join(self.base_paths[self.platform]['user_log'], '{}_{}'.format(self.app_name, version))
        if os.path.exists(expected):
            shutil.rmtree(expected)
        result = homebase.user_logs_dir(self.app_name, app_author=self.app_author, version=version, use_virtualenv=False,
                                        create=True)
        self.assertEqual(expected, result)
        self.assertTrue(os.path.exists(expected))
        shutil.rmtree(expected)

    def test_user_log_version_venv_no_create(self):
        version = '1.0'
        expected = os.path.join(self.base_paths[self.platform]['user_log_venv'],
                                '{}_{}'.format(self.app_name, version))
        result = homebase.user_logs_dir(self.app_name, app_author=self.app_author, version=version, use_virtualenv=True,
                                        create=False)
        self.assertEqual(expected, result)

    def test_user_log_version_venv_create(self):
        version = '1.0'
        expected = os.path.join(self.base_paths[self.platform]['user_log_venv'],
                                '{}_{}'.format(self.app_name, version))
        if os.path.exists(expected):
            shutil.rmtree(expected)
        self.assertFalse(os.path.exists(expected))
        result = homebase.user_logs_dir(self.app_name, app_author=self.app_author, version=version, use_virtualenv=True,
                                        create=True)
        self.assertEqual(expected, result)
        self.assertTrue(os.path.exists(expected))
        shutil.rmtree(expected)

    #####################################################
    # site_data_homebase. Not testing create=True since we don't know if we have permissions.
    #####################################################
    def test_site_data_no_version_no_venv_no_create(self):
        expected = os.path.join(self.base_paths[self.platform]['site_data'][0], self.app_name)
        self.assertEqual(expected,
                         homebase.site_data_dir(self.app_name, app_author=self.app_author, version=None,
                                                use_virtualenv=False, create=False))

    def test_site_data_no_version_venv_no_create(self):
        expected = os.path.join(self.base_paths[self.platform]['site_data'][0], self.app_name)
        self.assertEqual(expected,
                         homebase.site_data_dir(self.app_name, app_author=self.app_author, version=None,
                                                use_virtualenv=True, create=False))

    def test_site_data_version_no_venv_no_create(self):
        version = '1.0'
        expected = os.path.join(self.base_paths[self.platform]['site_data'][0], '{}_{}'.format(self.app_name, version))
        self.assertEqual(expected,
                         homebase.site_data_dir(self.app_name, app_author=self.app_author, version=version,
                                                use_virtualenv=False, create=False))

    def test_site_data_version_venv_no_create(self):
        version = '1.0'
        expected = os.path.join(self.base_paths[self.platform]['site_data'][0], '{}_{}'.format(self.app_name, version))
        self.assertEqual(expected,
                         homebase.site_data_dir(self.app_name, app_author=self.app_author, version=version,
                                                use_virtualenv=True, create=False))

    def test_site_data_list_no_version_no_venv_no_create(self):
        expected = [os.path.join(d, self.app_name) for d in self.base_paths[self.platform]['site_data']]
        self.assertEqual(expected,
                         homebase.site_data_dir_list(self.app_name, app_author=self.app_author, version=None,
                                                     use_virtualenv=False, create=False))

    def test_site_data_list_no_version_venv_no_create(self):
        expected = [os.path.join(d, self.app_name) for d in self.base_paths[self.platform]['site_data']]
        self.assertEqual(expected,
                         homebase.site_data_dir_list(self.app_name, app_author=self.app_author, version=None,
                                                     use_virtualenv=True, create=False))

    def test_site_data_list_version_no_venv_no_create(self):
        version = "1.0"
        expected = [os.path.join(d, '{}_{}'.format(self.app_name, version))
                    for d in self.base_paths[self.platform]['site_data']]
        self.assertEqual(expected,
                         homebase.site_data_dir_list(self.app_name, app_author=self.app_author, version=version,
                                                     use_virtualenv=False, create=False))

    def test_site_data_list_version_venv_no_create(self):
        version = '1.0'
        expected = [os.path.join(d, '{}_{}'.format(self.app_name, version))
                    for d in self.base_paths[self.platform]['site_data']]
        result = homebase.site_data_dir_list(self.app_name, app_author=self.app_author, version=version,
                                             use_virtualenv=True, create=False)
        self.assertEqual(expected, result)

    #####################################################
    # site_config_homebase. Not testing create=True since we don't know if we have permissions.
    #####################################################
    def test_site_config_no_version_no_venv_no_create(self):
        expected = os.path.join(self.base_paths[self.platform]['site_config'][0], self.app_name)
        self.assertEqual(expected,
                         homebase.site_config_dir(self.app_name, app_author=self.app_author, version=None,
                                                  use_virtualenv=False, create=False))

    def test_site_config_no_version_venv_no_create(self):
        expected = os.path.join(self.base_paths[self.platform]['site_config'][0], self.app_name)
        self.assertEqual(expected,
                         homebase.site_config_dir(self.app_name, app_author=self.app_author, version=None,
                                                  use_virtualenv=True, create=False))

    def test_site_config_version_no_venv_no_create(self):
        version = '1.0'
        expected = os.path.join(self.base_paths[self.platform]['site_config'][0],
                                '{}_{}'.format(self.app_name, version))
        self.assertEqual(expected,
                         homebase.site_config_dir(self.app_name, app_author=self.app_author, version=version,
                                                  use_virtualenv=False, create=False))

    def test_site_config_version_venv_no_create(self):
        version = '1.0'
        expected = os.path.join(self.base_paths[self.platform]['site_config'][0],
                                '{}_{}'.format(self.app_name, version))
        self.assertEqual(expected,
                         homebase.site_config_dir(self.app_name, app_author=self.app_author, version=version,
                                                  use_virtualenv=True, create=False))

    def test_site_config_list_no_version_no_venv_no_create(self):
        expected = [os.path.join(d, self.app_name) for d in self.base_paths[self.platform]['site_config']]
        self.assertEqual(expected,
                         homebase.site_config_dir_list(self.app_name, app_author=self.app_author, version=None,
                                                       use_virtualenv=False, create=False))

    def test_site_config_list_no_version_venv_no_create(self):
        expected = [os.path.join(d, self.app_name) for d in self.base_paths[self.platform]['site_config']]
        self.assertEqual(expected,
                         homebase.site_config_dir_list(self.app_name, app_author=self.app_author, version=None,
                                                       use_virtualenv=True, create=False))

    def test_site_config_list_version_no_venv_no_create(self):
        version = "1.0"
        expected = [os.path.join(d, '{}_{}'.format(self.app_name, version))
                    for d in self.base_paths[self.platform]['site_config']]
        self.assertEqual(expected,
                         homebase.site_config_dir_list(self.app_name, app_author=self.app_author, version=version,
                                                       use_virtualenv=False, create=False))

    def test_site_config_list_version_venv_no_create(self):
        version = '1.0'
        expected = [os.path.join(d, '{}_{}'.format(self.app_name, version))
                    for d in self.base_paths[self.platform]['site_config']]
        result = homebase.site_config_dir_list(self.app_name, app_author=self.app_author, version=version,
                                               use_virtualenv=True, create=False)
        self.assertEqual(expected, result)


@unittest.skipIf('travis' in os.path.expanduser('~'), 'Skipping travis virtualenv tests for now.')
class TestHomebaseVirtualEnv(TestHomebase):

    virtualenv_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'test_venv')
    real_prefix = sys.prefix

    def __init__(self, *args, **kwargs):
        TestHomebase.__init__(self, *args, **kwargs)

    def _expected_base_paths(self):
        base_paths = TestHomebase._expected_base_paths(self)

        # add virtualenv expectations.
        for paths in itervalues(base_paths):
            paths['user_data_venv'] = os.path.join(self.virtualenv_dir, 'data')
            paths['user_config_venv'] = os.path.join(self.virtualenv_dir, 'config')
            paths['user_state_venv'] = os.path.join(self.virtualenv_dir, 'state')
            paths['user_cache_venv'] = os.path.join(self.virtualenv_dir, 'cache')
            paths['user_log_venv'] = os.path.join(self.virtualenv_dir, 'logs')

        return base_paths

    @classmethod
    def setUpClass(cls):
        virtualenv.create_environment(cls.virtualenv_dir)
        if sys.platform == 'win32':
            activate_script = os.path.join(cls.virtualenv_dir, 'Scripts', 'activate_this.py')
        else:
            activate_script = os.path.join(cls.virtualenv_dir, 'bin', 'activate_this.py')

        if sys.version_info.major == '2':
            execfile(activate_script, dict(__file__=activate_script))
        else:
            with open(activate_script) as activate:
                exec(activate.read(), dict(__file__=activate_script))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.virtualenv_dir)
        if hasattr(sys, 'real_prefix'):
            sys.prefix = sys.real_prefix
            delattr(sys, 'real_prefix')
        else:
            sys.prefix = sys.base_prefix


@unittest.skipUnless(sys.platform.startswith('linux'), 'TestHomebaseLinuxXDG: Not Linux')
@unittest.skipIf('travis' in os.path.expanduser('~'), 'Skipping travis virtualenv tests for now.')
class TestHomebaseLinuxXDG(TestHomebase):

    def setUp(self):
        self._setup_linux_xdg_vars()

    def tearDown(self):
        self._clear_linux_xdg_vars()

    def _expected_base_paths(self):
        """
        Note: This class will always run regardless of OS, but unless self.platform is linux the values below are
        ignored and the test will be meaningless. You can either run it on linux (e.g. using the Dockerfile at the root
        of this project),or on mac by hard coding self.platform to 'linux' e.g. by overriding __init__.
        """
        base_paths = TestHomebase._expected_base_paths(self)

        self._setup_linux_xdg_vars()

        base_paths['linux']['user_data'] = os.environ['XDG_DATA_HOME']
        base_paths['linux']['user_data_venv'] = os.environ['XDG_DATA_HOME']
        base_paths['linux']['user_config'] = os.environ['XDG_CONFIG_HOME']
        base_paths['linux']['user_config_venv'] = os.environ['XDG_CONFIG_HOME']
        base_paths['linux']['user_state'] = os.environ['XDG_STATE_HOME']
        base_paths['linux']['user_state_venv'] = os.environ['XDG_STATE_HOME']
        base_paths['linux']['user_cache'] = os.environ['XDG_CACHE_HOME']
        base_paths['linux']['user_cache_venv'] = os.environ['XDG_CACHE_HOME']
        base_paths['linux']['site_data'] = os.environ['XDG_DATA_DIRS'].split(os.pathsep)
        base_paths['linux']['site_config'] = os.environ['XDG_CONFIG_DIRS'].split(os.pathsep)

        return base_paths


@unittest.skipUnless(sys.platform == 'win32', 'TestHomebaseWindowsExtra: Not Windows')
class TestHomebaseWindowsExtra(TestHomebase):

    def setUp(self):
        windows_username = os.getenv('username')
        windows_absolute_path = os.path.join('C:', os.sep)
        self.roaming_base_path = os.path.join(windows_absolute_path, 'Users', windows_username, 'AppData', 'Roaming')

        # # add windows expectations.
        # base_paths['user_data'] = os.path.join(windows_base_path, self.app_author)

    def test_user_data_no_app_author(self):
        with self.assertRaises(RuntimeError):
            homebase.user_data_dir(self.app_name, app_author=None)

    def test_user_config_no_app_author(self):
        with self.assertRaises(RuntimeError):
            homebase.user_config_dir(self.app_name, app_author=None)

    def test_user_cache_no_app_author(self):
        with self.assertRaises(RuntimeError):
            homebase.user_cache_dir(self.app_name, app_author=None)

    def test_user_logs_no_app_author(self):
        with self.assertRaises(RuntimeError):
            homebase.user_logs_dir(self.app_name, app_author=None)

    def test_user_state_no_app_author(self):
        with self.assertRaises(RuntimeError):
            homebase.user_state_dir(self.app_name, app_author=None)

    def test_site_data_no_app_author(self):
        with self.assertRaises(RuntimeError):
            homebase.site_data_dir(self.app_name, app_author=None)

    def test_site_config_no_app_author(self):
        with self.assertRaises(RuntimeError):
            homebase.site_config_dir(self.app_name, app_author=None)

    def test_user_data_roaming(self):
        expected = os.path.join(self.roaming_base_path, self.app_author, self.app_name)
        self.assertEqual(expected, homebase.user_data_dir(self.app_name, self.app_author, roaming=True))

    def test_user_config_roaming(self):
        expected = os.path.join(self.roaming_base_path, self.app_author, self.app_name)
        self.assertEqual(expected, homebase.user_config_dir(self.app_name, self.app_author, roaming=True))

    def test_user_state_roaming(self):
        expected = os.path.join(self.roaming_base_path, self.app_author, self.app_name)
        self.assertEqual(expected, homebase.user_state_dir(self.app_name, self.app_author, roaming=True))


if __name__ == '__main__':
    unittest.main()
