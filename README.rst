caom2proxy
==========

.. image:: https://img.shields.io/travis/opencadc/caom2proxy/master.svg
    :target: https://travis-ci.org/opencadc/caom2proxy?branch=master

.. image:: https://img.shields.io/coveralls/opencadc/caom2proxy/master.svg
    :target: https://coveralls.io/github/opencadc/caom2proxy?branch=master

.. image:: https://img.shields.io/github/contributors/opencadc/caom2proxy.svg
    :target: https://github.com/opencadc/caom2proxy/graphs/contributors


Collection of Docker images that proxy data from different data providers
mimicking the GET endpoints of a caom2repo service
such as the http://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/caom2repo service. It
is used primarily to support metadata harvesting into a CAOM2 repository.


caom2_proxy_base
----------------

This implements the base Web Service functionality of the proxy caom2 repo.
To implement a data provider specific container using the image created
in this project and overriding the collection.py file in the /app directory
of the image.

The format of the collection.py file is:

::

    COLLECTION = 'collection'  # name of CAOM2 collection


    def list_observations(start=None, end=None, maxrec=None):
        """
        List observations
        :param start: start date (UTC)
        :param end: end date (UTC)
        :param maxrec: maximum number of rows to return
        :return: Comma separated list of strings, each row of the form
          '{}, {}\n'.format(<obsid>, <timestamp>). Note that the list must be
          sorted based on the timestamp and that the timestamp is in IVOA
          dateformat(from a datetime object use the
          cadcutils.util.date2ivoa(timestamp) to get the right format)

    NOTE: For stream the results use a generator, e.g:
        for obs in sorted(observations):
        yield "{},{}\n".format(obs, <timestamp>)
        time.sleep(1)
    """
    raise NotImplementedError('GET list observations')


    def get_observation(id):
        """
        Return the observation corresponding to the id
        :param id: id of the observation
        :return: observation corresponding to the id or None if such
        such observation does not exist
        """
        raise NotImplementedError('GET observation')


The Dockerfile for the image is located in the image directory. To build the image:

::

    cd image
    docker build -t caom2proxy .


To run the image:

::

    docker run --rm -p 5000:5000 -d  --name caom2proxy caom2proxy


This maps the Web service to the 5000 local port.


Finally, to test the container:

::

   curl http://localhost:5000/obs23/<collection>/123
   curl http://localhost:5000/obs23/<collection>?maxrec=1000


Replace <collection> with the name of the collection you set in the
collection.py file


Note: This will result in an NotImplemented error since the framework needs
to be extended.
