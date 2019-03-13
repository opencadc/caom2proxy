alma-proxy
==========

The Dockerfile for the image is located in the image directory. To build the image:

::

    cd image
    docker build -t alma-proxy .


To run the image:

::

    docker run --rm -p 5000:5000 -d -v /<tmp>:/logs --name alma-proxy alma-proxy


This maps the Web service to the 5000 local port but it can be a different one.
Also replace <tmp> with the logs location of your choice on the host.


Finally, to test the container:

::

   curl http://localhost:5000/alma/obs23/ALMA/A001_X11a2_X11
   curl http://localhost:5000/alma/obs23/ALMA?maxrec=1000
   curl http://localhost:5000/alma/artresolve?uri=alma:ALMA/A001_X131c_X12f/2017.A.00054.S_uid___A001_X131c_X12f_001_of_001.tar

