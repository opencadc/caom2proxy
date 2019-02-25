alma-proxy
==========

The Dockerfile for the image is located in the image directory. To build the image:

::

    cd image
    docker build -t alma-proxy .


To run the image:

::

    docker run --rm -p 5000:5000 -d  --name alma-proxy alma-proxy


This maps the Web service to the 5000 local port but it can be a different one.


Finally, to test the container:

::

   curl http://localhost:5000/obs23/alma/A001_X11a2_X11
   curl http://localhost:5000/obs23/alma?maxrec=1000

