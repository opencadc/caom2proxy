
base
====

This package implements the base Web Service functionality of the proxy caom2
repo. It creates a base Docker image that presents the REST API that the
caom2Harvester application expects.

Collection specific packages extend the base image by:

    1. providing their own python runtime environment in the requirements.txt
    file
    2. extending the interface in the collection.py with collection specific
    code that return observations in that collection.

The format of the collection.py file, and consequently the API that is to be
used by a proxy, is:

::

    COLLECTION = 'collection'  # name of CAOM2 collection


    def list_observations(start=None, end=None, maxrec=None):
        """
        List observations
        :param start: start date (UTC)
        :param end: end date (UTC)
        :param maxrec: maximum number of rows to return
        :return: Tab separated list of strings, each row of the form
        '{}\t{}\t{}\n'.format(<collection>, <obsid>, <timestamp>).
        Note that the list must be sorted based on the timestamp and that
        the timestamp is in IVOA dateformat(from a datetime object use the
        cadcutils.util.date2ivoa(timestamp) to get the right format)
        :raises: All exceptions raised by this function are mapped to
        HTTP Bad Request (400) error unless the exception has the status_code
        attribute with a specific HTTP error in which case that error is
        returned.

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
        :raises: All exceptions raised by this function are mapped to
        HTTP Bad Request (400) error unless the exception has the status_code
        attribute with a specific HTTP error in which case that error is
        returned.
        """
        raise NotImplementedError('GET observation')


    def resolve_artifact_uri(uri):
        """
        Return the URL corresponding to an artifact URI
        Note: This is optional and does not need to be implemented
        :param uri: URI for the artifact
        :return: URL corresponding the artifact URI
        """
        raise NotImplementedError('resolve artifact uri not implememnted')


Collection proxies override the file in their image with their own
implementation.

To build at Docker image:

::

    cd image
    docker build -t caom2proxy .


To run the image:

::

    docker run --rm -p 5000:5000 -d -v /tmp:/logs --name caom2proxy caom2proxy


This maps the Web service to the 5000 local port. Also, generated logs are
stored on the local machine in /tmp/<collection>.log since the /tmp on local
machine is mounted as /logs in the container.


Finally, to test the container (artresolve is optional):

::

   curl http://localhost:5000/collection/obs23/<collection>/123
   curl http://localhost:5000/collection/obs23/<collection>?maxrec=1000
   curl http://localhost:5000/collection/artresolve?uri=foo


Replace <collection> with the name of the collection you set in the
collection.py file


Note: This will result in an NotImplemented error since the framework needs
to be extended.
