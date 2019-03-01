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

from flask import Flask, Response, make_response, stream_with_context, request
from flask_restful import Resource, Api, reqparse
from cadcutils.util import str2ivoa
from caom2 import ObservationWriter
from io import BytesIO
from collection import COLLECTION, list_observations, get_observation
import logging

app = Flask(__name__)
api = Api(app, default_mediatype=None)


logger = logging.getLogger('caom2proxy')
logger.setLevel(logging.DEBUG)

CAOM_VERSION = '23'


@api.representation('text/csv')
def output_csv(data, code, headers=None):
    logger.debug("CSV representation")
    t = Response(stream_with_context(data))
    resp = make_response(t, code)
    resp.headers.extend(headers or {})
    return resp


@api.representation('application/xml')
def output_xml(data, code, headers=None):
    """Makes a Flask response with a XML encoded body"""
    logger.debug("XML representation")
    resp = make_response(data, code)
    resp.headers.extend(headers or {})
    return resp


class Caom23ObsList(Resource):

    def __init__(self, representations=None):
        self.representations = representations
        super(Caom23ObsList, self).__init__()

    def get(self):
        logger.debug("list observations")
        parser = reqparse.RequestParser()
        parser.add_argument('maxrec', type=int, help='Maximum records')
        parser.add_argument('start', type=str2ivoa, help='Start date')
        parser.add_argument('end', type=str2ivoa, help='End date')
        args = parser.parse_args()
        return list_observations(args['start'], args['end'],
                                 args['maxrec'])


class Caom23Obs(Resource):
    def __init__(self, representations=None):
        self.representations = representations
        super(Caom23Obs, self).__init__()

    def get(self, id):
        logger.debug("get observation")
        obs = get_observation(id)
        if not obs:
            return 'Observation {}/{} not found'.format(COLLECTION, id), 404
        writer = ObservationWriter(True)
        output = BytesIO()
        writer.write(obs, output)
        return output.getvalue().decode('utf-8')


class Capabilities23(Resource):
    def __init__(self, representations=None):
        self.representations = representations
        super(Capabilities23, self).__init__()

    def get(self):
        logger.debug("get capabilities")
        base_url = request.base_url[:-12]  # drops /capabilities from url
        capabilities_doc = \
            """
            <vosi:capabilities
            xmlns:vosi="http://www.ivoa.net/xml/VOSICapabilities/v1.0"
            xmlns:vs="http://www.ivoa.net/xml/VODataService/v1.1"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                <capability standardID="ivo://ivoa.net/std/VOSI#capabilities">
                    <interface xsi:type="vs:ParamHTTP" role="std">
                        <accessURL use="full">
                            {0}capabilities
                        </accessURL>
                    </interface>
                </capability>
                <capability standardID="ivo://ivoa.net/std/VOSI#availability">
                    <interface xsi:type="vs:ParamHTTP" role="std">
                        <accessURL use="full">
                            {0}availability
                        </accessURL>
                    </interface>
                </capability>
                <capability
                standardID="vos://cadc.nrc.ca~vospace/CADC/std/CAOM2Repository#obs-1.1">
                    <interface xsi:type="vs:ParamHTTP" role="std">
                        <accessURL use="base">
                            {0}obs{1}
                        </accessURL>
                    </interface>
                </capability>
            </vosi:capabilities>
            """.format(base_url, CAOM_VERSION)
        return capabilities_doc


class Availability(Resource):

    def __init__(self, representations=None):
        self.representations = representations
        super(Availability, self).__init__()

    def get(self):
        logger.debug("Check availability")
        available = False
        avail_text = 'service is down'
        try:
            if list_observations(maxrec=1):
                available = True
                avail_text = 'service is accepting queries'
        except Exception:
            pass

        doc = \
            """
            <vosi:availability
            xmlns:vosi="http://www.ivoa.net/xml/VOSIAvailability/v1.0">
                <vosi:available>{}</vosi:available>
                <vosi:note>{}</vosi:note>
            </vosi:availability>
            """.format(available, avail_text)
        return doc


api.add_resource(Caom23ObsList, '/{}/obs{}/{}'.format(
    COLLECTION.lower(), CAOM_VERSION, COLLECTION),
                 resource_class_kwargs={
                     'representations': {'text/csv': output_csv}})
api.add_resource(Caom23Obs, '/{}/obs{}/{}/<string:id>'.format(
    COLLECTION.lower(), CAOM_VERSION, COLLECTION),
                 resource_class_kwargs={
                     'representations': {'application/xml': output_xml}})
api.add_resource(Capabilities23, '/{}/capabilities'.format(COLLECTION.lower()),
                 resource_class_kwargs={
                     'representations': {'application/xml': output_xml}})
api.add_resource(Availability, '/{}/availability'.format(COLLECTION.lower()),
                 resource_class_kwargs={
                     'representations': {'application/xml': output_xml}})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
