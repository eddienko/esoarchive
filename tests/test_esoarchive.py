#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `esoarchive` package."""

from unittest.mock import Mock, call, patch

import pytest
from click.testing import CliRunner

from esoarchive import cli, esoarchive


@pytest.fixture
def response():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    # import requests
    # return requests.get('https://github.com/audreyr/cookiecutter-pypackage')


def test_content(response):
    """Sample pytest test function with the pytest fixture as an argument."""
    # from bs4 import BeautifulSoup
    # assert 'GitHub' in BeautifulSoup(response.content).title.string


@patch('esoarchive.esoarchive.Browser')
def test_esoarchive(Browser):
    browser = Browser.return_value
    browser.html = ' -- No data returned'
    config = {'nightobs': '20170101', 'rows': 10, 'headless': 'false'}
    archive = esoarchive.ESOArchive(config)
    assert archive.nightobs == config['nightobs']
    assert archive.max_rows == config['rows']
    archive.request()

    #browser.html = ' -- Completed'
    # archive.request()

    config = {'nightobs': '20170101', 'rows': 'error', 'headless': 'true'}
    with pytest.raises(Exception) as err:
        archive = esoarchive.ESOArchive(config)
        assert err.value == 'Not an integer'

    config = {'nightobs': '20170101', 'rows': '10', 'headless': 'error'}
    with pytest.raises(Exception) as err:
        archive = esoarchive.ESOArchive(config)
        assert err.value == 'Not a boolean'


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert 'Show this message and exit.' in help_result.output
