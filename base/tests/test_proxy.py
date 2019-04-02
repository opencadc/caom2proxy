# -*- coding: utf-8 -*-
# ***********************************************************************
# ******************  CANADIAN ASTRONOMY DATA CENTRE  *******************
# *************  CENTRE CANADIEN DE DONNÉES ASTRONOMIQUES  **************
#
#  (c) 2018.                            (c) 2018.
#  Government of Canada                 Gouvernement du Canada
#  National Research Council            Conseil national de recherches
#  Ottawa, Canada, K1A 0R6              Ottawa, Canada, K1A 0R6
#  All rights reserved                  Tous droits réservés
#
#  NRC disclaims any warranties,        Le CNRC dénie toute garantie
#  expressed, implied, or               énoncée, implicite ou légale,
#  statutory, of any kind with          de quelque nature que ce
#  respect to the software,             soit, concernant le logiciel,
#  including without limitation         y compris sans restriction
#  any warranty of merchantability      toute garantie de valeur
#  or fitness for a particular          marchande ou de pertinence
#  purpose. NRC shall not be            pour un usage particulier.
#  liable in any event for any          Le CNRC ne pourra en aucun cas
#  damages, whether direct or           être tenu responsable de tout
#  indirect, special or general,        dommage, direct ou indirect,
#  consequential or incidental,         particulier ou général,
#  arising from the use of the          accessoire ou fortuit, résultant
#  software.  Neither the name          de l'utilisation du logiciel. Ni
#  of the National Research             le nom du Conseil National de
#  Council of Canada nor the            Recherches du Canada ni les noms
#  names of its contributors may        de ses  participants ne peuvent
#  be used to endorse or promote        être utilisés pour approuver ou
#  products derived from this           promouvoir les produits dérivés
#  software without specific prior      de ce logiciel sans autorisation
#  written permission.                  préalable et particulière
#                                       par écrit.
#
#  This file is part of the             Ce fichier fait partie du projet
#  OpenCADC project.                    OpenCADC.
#
#  OpenCADC is free software:           OpenCADC est un logiciel libre ;
#  you can redistribute it and/or       vous pouvez le redistribuer ou le
#  modify it under the terms of         modifier suivant les termes de
#  the GNU Affero General Public        la “GNU Affero General Public
#  License as published by the          License” telle que publiée
#  Free Software Foundation,            par la Free Software Foundation
#  either version 3 of the              : soit la version 3 de cette
#  License, or (at your option)         licence, soit (à votre gré)
#  any later version.                   toute version ultérieure.
#
#  OpenCADC is distributed in the       OpenCADC est distribué
#  hope that it will be useful,         dans l’espoir qu’il vous
#  but WITHOUT ANY WARRANTY;            sera utile, mais SANS AUCUNE
#  without even the implied             GARANTIE : sans même la garantie
#  warranty of MERCHANTABILITY          implicite de COMMERCIALISABILITÉ
#  or FITNESS FOR A PARTICULAR          ni d’ADÉQUATION À UN OBJECTIF
#  PURPOSE.  See the GNU Affero         PARTICULIER. Consultez la Licence
#  General Public License for           Générale Publique GNU Affero
#  more details.                        pour plus de détails.
#
#  You should have received             Vous devriez avoir reçu une
#  a copy of the GNU Affero             copie de la Licence Générale
#  General Public License along         Publique GNU Affero avec
#  with OpenCADC.  If not, see          OpenCADC ; si ce n’est
#  <http://www.gnu.org/licenses/>.      pas le cas, consultez :
#                                       <http://www.gnu.org/licenses/>.
#
#  $Revision: 4 $
#
# ***********************************************************************
#
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os
import docker
import pytest
import logging
import time
import requests

logger = logging.getLogger('test')

CONTAINER_NAME = 'caom2proxy'
BASE_IMAGE_NAME = 'bucket.canfar.net/cadc/base-caom2-proxy'
IMAGE_NAME = 'caom2proxy:latest'
LOCAL_PORT = 5000

PARENT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
BASE_IMAGE_DIR = os.path.join(os.path.dirname(PARENT_DIR), 'base', 'image')
IMAGE_DIR = os.path.join(PARENT_DIR, 'image')


@pytest.fixture
def docker_client():
    # builds and launches a container
    client = docker.from_env()
    for c in client.containers.list():
        if c.name == CONTAINER_NAME:
            c.kill()
    try:
        client.images.remove(BASE_IMAGE_NAME, force=True)
    except Exception as e:
        logger.warning('Cannot remove base image: {}'.format(str(e)))
    try:
        client.images.remove(IMAGE_NAME, force=True)
    except Exception as e:
        logger.warning('Cannot remove image: {}'.format(str(e)))

    # build base name
    client.images.build(path=BASE_IMAGE_DIR, tag=BASE_IMAGE_NAME)
    client.images.build(path=IMAGE_DIR, tag=IMAGE_NAME)

    return client.containers.run(IMAGE_NAME, auto_remove=True,
                                 ports={'5000/tcp': LOCAL_PORT},
                                 volumes={'/tmp': {'bind': '/logs',
                                                   'mode': 'rw'}},
                                 name=CONTAINER_NAME,
                                 detach=True)


def test_main(docker_client):
    assert docker_client.status == 'created'
    time.sleep(5)
    with open('/tmp/collection.log', 'r') as f:
        print(f.read())
    response = \
        requests.get(
            'http://localhost:{}/collection/obs23/collection?maxrec=1&'
            'start=2010-10-10T10:10:10.000&end=2011-10-10T10:10:10.0'.
            format(LOCAL_PORT))
    assert response.status_code == 500
    assert 'GET list observations' in response.text

    response = \
        requests.get(
            'http://localhost:{}/collection/obs23/collection/1234'.
            format(LOCAL_PORT))
    assert response.status_code == 500
    assert 'GET observation' in response.text

    response = \
        requests.get(
            'http://localhost:{}/collection/artresolve'.format(LOCAL_PORT))
    assert response.status_code == 500
    assert 'resolve artifact uri not implememnted' in response.text
