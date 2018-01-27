# -*- coding: utf-8 -*-

"""Console script for esoarchive."""

from configparser import ConfigParser
from datetime import datetime

import click

from .esoarchive import ESOArchive


def validate_night(ctx, param, value):
    try:
        datetime.strptime(value, '%Y%m%d')
        return value
    except ValueError:
        raise click.BadParameter('night needs to be in format YYYYMMDD')


@click.command(help='Automatic ESO raw data archive requests and download')
@click.option('--conf', '-c',
              type=click.Path(exists=True),
              help='Configuration file')
@click.option('--instrument',
              help='Instrument or list of instruments')
@click.option('--night',
              default=datetime.utcnow().strftime('%Y%m%d'),
              callback=validate_night,
              help='Night of observation (YYYYMMDD)')
@click.option('--output', '-o',
              type=click.Path(),
              help='Output directory')
@click.option('--rows', default=200,
              help='Maximum number of rows to return')
def main(conf, instrument, night, output, rows):
    if conf is None:
        config = {'esoarchive': {}}
    else:
        config = ConfigParser()
        config.read(conf)

    options = dict(config['esoarchive'])
    if instrument:
        options['instrument'] = instrument
    if night:
        options['nightobs'] = night
    if rows:
        options['rows'] = rows
    if output:
        options['output'] = output

    archive = ESOArchive(options, debug=True)

    filelist = archive.request()
    if filelist is not None:
        archive.download(filelist)


if __name__ == "__main__":
    main()
