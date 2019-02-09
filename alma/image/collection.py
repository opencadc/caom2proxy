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

# collection specific code to return a list of observation IDs or a
# specific CAOM2 observation

from datetime import datetime
import re
import requests
import mimetypes
from astroquery.alma import Alma
from caom2.shape import SubInterval #TODO
from caom2 import SimpleObservation, TypedOrderedDict, Plane, Artifact,\
                  Part, Chunk, ObservationWriter, ProductType, Position, Circle, Point, Interval,\
                  ReleaseType, TypedList, DataProductType, Proposal, CalibrationLevel, Target, TargetType, \
    Instrument, Time, Energy, Polarization, PolarizationState, Algorithm, ObservationIntentType, Telescope
from cadcutils.util import date2ivoa
import numpy as np
from six import BytesIO
import logging
from astropy import units as u
from astropy.time import Time as AstropyTime


COLLECTION = 'alma'

ALMA_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
ALMA_QUERY_DATE_FORMAT = '%d-%m-%Y'
ALMA_RELEASE_DATE_FORMAT = '%Y-%m-%d'


logger = logging.getLogger('caom2proxy')
logger.setLevel(logging.DEBUG)

def list_observations(start=None, end=None, maxrec=None):
    """
    List observations
    :param start: start date (UTC)
    :param end: end date (UTC)
    :param maxrec: maximum number of rows to return
    :return: Comma separated list, each row consisting of ObservationID,
    last mod date.
    """
    obs_date = {}
    if start and end:
        obs_date = '{} .. {}'.format(start.strftime(ALMA_QUERY_DATE_FORMAT),
                                     end.strftime(ALMA_QUERY_DATE_FORMAT))
    elif start:
        obs_date = '>= {}'.format(start.strftime(ALMA_QUERY_DATE_FORMAT))
    elif end:
        obs_date = '<= {}'.format(end.strftime(ALMA_QUERY_DATE_FORMAT))

    if obs_date:
        obs_date = {'start_date': obs_date}
    alma = Alma.query(obs_date)['Member ous id', 'Observation date']
    np.unique(alma['Member ous id'])
    tmp = {}
    for row in alma:
        d = datetime.strptime(row[1].decode('ascii'), ALMA_DATE_FORMAT)
        if row['Member ous id'] not in tmp or d>tmp[row['Member ous id']]:
            tmp[row['Member ous id']] = d
    result = ['{}, {}\n'.format(_to_obs_id(w), date2ivoa(tmp[w]))
              for w in sorted(tmp, key=tmp.get)]
    if maxrec:
        return result[:maxrec]
    else:
        return result


def _to_obs_id(member_ouss_id):
    return member_ouss_id.replace('uid://', '').replace('/', '_')

def _to_member_ouss_id(obs_id):
    return 'uid://{}'.format(obs_id.replace('_', '/'))

def get_observation(id):
    """
    Return the observation corresponding to the id
    :param id: id of the observation
    :return: observation corresponding to the id or None if such
    such observation does not exist
    """
    member_ouss_id = _to_member_ouss_id(id)
    #TODO temporary
    #Alma.archive_url = 'http://almascience.eso.org'
    results = Alma.query({'member_ous_id': member_ouss_id}, science=False)

    if not results:
        logger.debug('No observation found for ID : {}'.format(member_ouss_id))
        return None
    return member2observation(member_ouss_id, results)


a = Alma()
# alternative mirror when main site doesn't work
#a.archive_url = 'http://almascience.eso.org'

# Code for proxy caom2 service

def member2observation(member_ous, table):
    """ returns an observation object """
    observationID = (member_ous.replace('uid://', '')).replace('/', '_')
    observation = SimpleObservation('ALMA', observationID)
    for row in table:
        add_calib_plane(observation, row, table)

    # observation metadata is common amongst rows so get it from the first
    # row
    fr = table[0]
    observation.meta_release = \
        datetime.strptime(fr['Observation date'].decode('ascii'),
                          ALMA_DATE_FORMAT)
    add_raw_plane(observation, member_ous, observation.meta_release)
    proposal = Proposal(fr['ASA_PROJECT_CODE'])
    proposal.project = fr['Project code']
    proposal.pi_name = fr['PI name']
    proposal.title = fr['Project title']
    proposal.keywords = set(fr['Science keyword'].split(','))
    observation.proposal = proposal
    instrument = Instrument('BAND {}'.format(row['Band'][0]))
    observation.instrument = instrument
    observation.algorithm = Algorithm('Exposure')
    observation.intent = ObservationIntentType.SCIENCE
    observation.telescope = \
        Telescope('ALMA-{}'.format(row['Array'].decode('ascii')),
                  2225142.18, -5440307.37, -2481029.852)
    observation.target = Target(name='TBD', target_type=TargetType.OBJECT)
    return observation


def add_calib_plane(observation, row, table):
    """ Adds a calibrated plane to the observation """
    productID = re.sub('-$', '', (
    re.sub('^-', '', ((re.sub('\W+', '-', row['Source name'])).
                      replace('--', '-')))))
    plane = Plane(productID)
    meta_release = \
        datetime.strptime(row['Observation date'].decode('ascii'),
                          ALMA_DATE_FORMAT)
    if 'Observation date' in row:
        meta_release = datetime.strptime(
            row['Observation date'].decode('ascii'), ALMA_DATE_FORMAT)
    plane.meta_release = meta_release
    tmp = row['Release date']
    if isinstance(tmp, bytes):
        tmp = tmp.decode('ascii')
    #TODO bug in astroquery.alma
    # plane.data_release = datetime.strptime(tmp, ALMA_RELEASE_DATE_FORMAT)
    position = Position()
    position.resolution = row['Spatial resolution']
    # Shape is circle
    # make sure all units are degrees
    ra = row['RA']*table['RA'].unit.to(u.deg)
    dec = row['Dec'] * table['Dec'].unit.to(u.deg)
    radius = row['Field of view'] * table['Field of view'].unit.to(u.deg)/2.0
    circle = Circle(Point(ra, dec), radius)
    position.bounds = circle
    plane.position = position
    #TODO energy = Energy()
    time = Time()
    time.exposure = row['Integration']*table['Integration'].unit.to(u.second)
    time_lb = AstropyTime(datetime.strptime(
        row['Observation date'].decode('ascii'), ALMA_DATE_FORMAT))
    time_ub = time_lb + time.exposure*u.second
    time_interval = Interval(time_lb.mjd, time_ub.mjd)
    samples = SubInterval(time_lb.mjd, time_ub.mjd)
    time_interval.samples = [samples]
    time.bounds = time_interval
    plane.time = time
    polarization = Polarization()
    polarization.polarization_states = \
        [PolarizationState(i) for i in row['Pol products'].split()]
    plane.polarization = polarization
    plane.data_product_type = DataProductType.VISIBILITY
    plane.calibration_level = CalibrationLevel.CALIBRATED
    observation.planes[productID] = plane


def add_raw_plane(observation, member_ous, meta_release):
    """ adds raw plane to observation """
    productID = observation.observation_id + '-raw'
    plane = Plane(productID)
    plane.artifacts = TypedOrderedDict(Artifact)
    plane.meta_release = meta_release
    plane.calibration_level = CalibrationLevel.RAW_INSTRUMENTAL
    observation.planes[productID] = plane
    add_raw_artifacts(plane, member_ous)


def add_raw_artifacts(plane, member_ous):
    """ Adds all the raw artifacts to the plane """
    files = a.stage_data(member_ous)
    file_urls = list(set(files['URL']))
    print('\n'.join(file_urls))
    for file_url in file_urls:
        add_raw_artifact(plane, file_url)


def add_raw_artifact(plane, file_url):
    """ adds a raw artifact to the plane """
    filename = file_url.split('/')[-1]
    #    print(filename)
    file_uri = 'alma:ALMA/' + filename
    #    print(file_file_uri)
    file_header = requests.head(file_url)
    content_type = file_header.headers['Content-Type']
    if content_type == '':
        content_type = mimetypes.guess_type(file_url)[0]
    if 'asdm' in filename:
        product_type = ProductType.SCIENCE
        content_length = file_header.headers['Content-Length']
    else:
        product_type = ProductType.AUXILIARY
        content_length = ''
    artifact = Artifact(file_uri, product_type, ReleaseType.META)
    plane.artifacts[file_uri] = artifact

