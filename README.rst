caom2proxy
==========

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
        :return: Comma separated list, each row consisting of ObservationID,
        last mod date.

        NOTE: For stream the results use a generator, e.g:
            for i in range(3):
            yield "{}\n".format(datetime.datetime.now().isoformat())
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
   curl http://localhost:5000/obs23/collection/123
   curl http://localhost:5000/obs23/collection?maxrec=1000 

Note: This will result in an NotImplemented error since the framework needs
to be extended.
