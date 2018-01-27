=======
 Usage
=======

The script requires a configuration file with default values. A
typical configuration file looks like the following:

Configuration file
==================

.. code-block:: console

   [DEFAULT]
   max_workers = 4

   [esoarchive]
   username = XXXXXXX
   password = XXXXXXX
   rows = 200
   output = /tmp/{nightobs}
   headless = true
   starttime = 16
   endtime = 16
   instrument = VIRCAM


Runing the script
=================

.. code-block:: console

   esoarchive --conf config.ini --night 20170609 --rows 1000

Data will be downloaded to the directory specified in the
configuration file (it will be created if it does not exist).
