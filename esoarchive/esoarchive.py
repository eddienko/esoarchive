# -*- coding: utf-8 -*-

"""Main module."""

import concurrent.futures
import logging
import os
import os.path
import re
import shutil
import time
from concurrent.futures import ThreadPoolExecutor

import requests
from splinter import Browser
from voluptuous import Invalid, Optional, Schema

logging.basicConfig(format='%(levelname)-9s: %(name)s : %(message)s')


class LoginUnsuccessful(Exception):
    pass


def Str2Int(value):
    try:
        return int(value)
    except Exception:
        raise Invalid('Not an integer')


def Str2Bool(value):
    if value in ['false', 'true']:
        return value == 'true'
    else:
        raise Invalid('Not a boolean')


class ESOArchive:
    """
    Query the ESO raw data archive.

    Parameters
    ----------
    config : dict
      Dictionary containing configuration values
    """

    url = 'http://archive.eso.org/eso/eso_archive_main.html'
    schema = Schema({
        Optional('max_workers'): Str2Int,
        Optional('rows'): Str2Int,
        Optional('starttime'): Str2Int,
        Optional('endtime'): Str2Int,
        Optional('headless'): Str2Bool
    }, extra=True)

    def __init__(self, config, debug=False):
        self.logger = logging.getLogger(__class__.__name__)
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)

        self._validate_config(config)

        self._setup()

        self._instrument = self._nightobs = self._target = None
        self._coords = None
        self._resolver = 'simbad'
        self._endtime = self._startime = 12
        self._rows = 200

        self.instrument = self._config.get('instrument', None)
        self.nightobs = self._config.get('nightobs', None)
        self.target = self._config.get('target', None)
        self.starttime = self._config.get('starttime', None)
        self.endtime = self._config.get('endtime', None)
        self.max_rows = self._config.get('rows', None)
        self.output = self._config.get('output', None)

    def _validate_config(self, config):
        try:
            self._config = self.schema(dict(config))
        except Exception as err:
            self.logger.error(err)
            raise

    def _setup(self):
        """Setup the connection.
        """
        self.logger.debug(f'Setting URL {self.url}')
        headless = self._config.get('headless', True)
        self.browser = Browser('chrome', headless=headless)
        self.browser.visit(self.url)

    @property
    def output(self):
        return self._output.format(nightobs=self.nightobs,
                                   instrument=self.instrument)

    @output.setter
    def output(self, out: str):
        self._output = out

    @property
    def nightobs(self):
        """Night of observation to request (YYYYMMDD)
        """
        try:
            n = self._nightobs.replace(' ', '')
        except Exception:
            n = ''
        return n

    @nightobs.setter
    def nightobs(self, nightobs: str):
        """Set the night to request.

        Parameters
        ----------
        nightobs : str
          Night of observation to request, YYYYMMDD.
        """
        if nightobs is None:
            return
        night = ' '.join([*map(lambda x: nightobs[slice(*x)], [(0, 4), (4, 6), (6, 8)])])
        self.logger.debug(f'Selecting night {nightobs}')
        self.browser.find_by_name('night').fill(night)
        self._nightobs = night

    @property
    def target(self):
        """Name of the astronomical object you want to search for.
        """
        return self._target

    @target.setter
    def target(self, target: str):
        if target is None:
            return
        self.logger.debug(f'Selecting target {target}')
        self.browser.find_by_name('target').fill(target)
        self._target = target

    @property
    def resolver(self):
        """Resolver to use for target (simbad | ned | none).
        """
        return self._resolver

    @resolver.setter
    def resolver(self, resolver: str='simbad'):
        if resolver is None:
            return
        self.logger.debug(f'Selecting target {resolver}')
        self.browser.find_by_name('resolver').select(resolver)
        self._resolver = resolver

    @property
    def coords(self):
        """Coordinates of position to look for.
        """
        return self._coords

    @coords.setter
    def coords(self, ra: str, dec: str):
        if ra is None or dec is None:
            return
        self.browser.find_by_name('ra').fill(ra)
        self.browser.find_by_name('dec').fill(dec)
        self._coords = [ra, dec]

    def _getlog(self):
        self.browser.find_by_name('wdbo').first.select('ascii/display')
        self.browser.find_by_id('search').click()
        res = self.browser.html
        self.browser.back()
        self.browser.find_by_name('wdbo').first.select('html/display')
        return res

    @property
    def instrument(self):
        """Instrument to query for data (e.g. VIRCAM)
        """
        return self._instrument

    @instrument.setter
    def instrument(self, instrument: str=None):
        """Select instrument.

        Parameters
        ----------
        instrument : str
          Instrument or list separated by commas
        """
        if instrument is None:
            return
        self.logger.debug(f'Selecting instrument {instrument}')
        for ins in instrument.split(','):
            self.browser.find_by_value(ins).first.click()
        self._instrument = instrument

    @property
    def starttime(self):
        """Start time of observations.
        """
        return self._starttime

    @starttime.setter
    def starttime(self, hour: int=12):
        """Set the start time.

        Parameters
        ----------
        hour : int, default: 12
          Start time (0, 23)
        """
        if hour is None:
            return
        self.browser.find_by_name('starttime').first.select(hour)
        self._starttime = hour

    @property
    def endtime(self):
        """End time of observations.
        """
        return self._endtime

    @endtime.setter
    def endtime(self, hour: int=12):
        """Set the end time.

        Parameters
        ----------
        hour : int, default: 12
          End time (0, 23)
        """
        if hour is None:
            return
        self.browser.find_by_name('endtime').first.select(hour)
        self._endtime = hour

    @property
    def max_rows(self):
        """Maximum number of records to retrieve.
        """
        return self._rows

    @max_rows.setter
    def max_rows(self, rows: int=200):
        """Set maximum number of rows to return.

        Parameters
        ----------
        rows : int, default: 200
          Maximum number of rows to return
        """
        if rows is None:
            return
        self.logger.debug(f'Selecting max rows {rows}')
        self.browser.find_by_name('max_rows_returned').first.fill(rows)
        self._rows = rows

    def _login(self):
        """Login to the archive.
        """
        if self.browser.is_element_not_present_by_text('Login'):
            self.logger.warn('No login form found')
            return
        credentials = {k: v for k, v in self._config.items() if k in ['username', 'password']}
        self.browser.fill_form(credentials)
        self.browser.find_by_text('Login')[1].click()
        if self.browser.html.find('Login failed') > 0:
            raise LoginUnsuccessful(f'Login unsuccessfull for {credentials["username"]}')
        else:
            self.logger.debug(f'Login successfull for {credentials["username"]}')

    def _make_outdir(self):
        if not os.access(self.output, os.X_OK):
            os.makedirs(self.output)

    def request(self):
        """Perform a request to the archive.
        """
        self.logger.debug('Searching and requesting data')
        # First page - fill in extras
        for tab in ['tab_origfile', 'tab_obs_name', 'tab_ob_id', 'tab_rel_date']:
            self.browser.find_by_name(tab).first.click()
        # Request ASCII table
        self.logdata = self._getlog()
        # First page - click on search
        self.browser.find_by_id('search').click()
        # Second page - check that there are some data returned
        if self.browser.html.find('No data returned') > 0:
            self.logger.error('No data returned')
            return
        # Second page - mark all rows
        self.browser.find_by_id('ibmarkall').click()
        # Second page - request datasets
        self.browser.find_by_value('Request marked datasets').first.click()
        # Third page - fill login credentials
        try:
            self._login()
        except LoginUnsuccessful as err:
            self.logger.error(err)
            return
        # Fourth page - submit
        self.browser.find_by_name('submit').first.click()

        # Fifth page - wait for completed
        while self.browser.html.find('Completed') < 0:
            time.sleep(2)

        href = self.browser.find_link_by_partial_text('downloadRequest').first
        url = re.compile('(https://.*)"').search(href.outer_html).group(1)

        result = requests.get(url, cookies=self.browser.cookies.all())
        script = result.content.decode('utf-8')

        self._make_outdir()

        with open(os.path.join(self.output, href.value), 'w') as fh:
            fh.write(script)
            self.logger.debug(f'{href.value} written')

        with open(os.path.join(self.output, f'ESOLOG.{self.nightobs}'), 'w') as fh:
            fh.write(self.logdata)
            self.logger.debug(f'ESOLOG.{self.nightobs} written')

        filelist = re.compile('https://.*[fz|txt]').findall(script)

        allfiles = re.compile('VCAM.\S+').findall(self.logdata)
        for f in allfiles:
            if not any(map(lambda x: f in x, filelist)):
                with open(os.path.join(self.output, f'{f}.dummy'), 'w') as fh:
                    fh.write('')

        return filelist

    def download(self, filelist: list):
        """Download a list of files.

        Parameters
        ----------
        filelist : list of str
          URLs to download.
        """
        max_workers = self._config.get('max_workers', 1)
        self.logger.debug(f'Downloading using {max_workers} workers')
        with ThreadPoolExecutor(max_workers=int(max_workers)) as executor:
            future_to_url = {executor.submit(self._downloadfile, url): url for url in filelist}
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                self.logger.info('Saved %s', os.path.basename(url))

    def _downloadfile(self, f):
        r = requests.get(f, stream=True, auth=(self._config['username'],
                                               self._config['password']))
        filename = os.path.basename(f)
        fullname = os.path.join(self.output, filename)
        if os.access(fullname, os.F_OK):
            oldsize = os.stat(fullname).st_size
            newsize = int(r.headers['Content-Length'])
            if oldsize == newsize:
                return

        with open(fullname, 'wb') as fh:
            shutil.copyfileobj(r.raw, fh)

    def close(self):
        self.browser.quit()
