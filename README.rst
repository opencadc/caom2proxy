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
such as the http://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/caom2ops service. It
is used primarily to support metadata harvesting into a CAOM2 repository.


Subprojects
-----------

+ base: implements the base image that is inherited by all the others
+ alma: implements the image for proxying the ALMA


Development
-----------

Here are the steps to create a new image:

1 Create the subproject:

::

    mkdir myproxy
    cd myproxy
    mkdir tests
    mkdir image


2. Create the development python envirnoment requirements. At the minimum,
this consists of the pytest package

::

    echo 'pytest' > dev_requirements.txt


3. In the image subdirectory, create the image including the Dockerfile with
specific environment, requirements.txt file for the Python environment and
collection.py with the specific code (see `base <base>` for details)

::

    cd image
    touch Dockerfile
    # edit Dockerfile
    touch requirements.txt
    # edit requirements.txt
    touch collection.py
    # edit collection.py
    cd ..


4. Create the unit tests in the tests directory. Data files required in the
tests are located in tests/data

5. Run tests

::

    pytest tests


6. Build and check container (see `base <base>` for details)

5. Check the style of the code

::

    flake8 image
    flake8 tests


Details on how to implement an image can be found in the `base subproject<base>`.

To test a project, the environment needs to be set up first, followed by test
invocation:

::

    cd <subproject>
    pip install -r dev_requirements.txt
    pip install -r image/requirements.txt
    pytest --cov tests

