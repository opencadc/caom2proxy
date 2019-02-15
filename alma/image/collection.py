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
import requests
import mimetypes
from astroquery.alma import Alma
from caom2.shape import SubInterval
import caom2
from cadcutils.util import date2ivoa
from six import BytesIO
import logging
from astropy import units as u
from astropy.time import Time as AstropyTime
import re
from astropy.io.votable import parse_single_table


COLLECTION = 'alma'

ALMA_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
ALMA_QUERY_DATE_FORMAT = '%d-%m-%Y'
ALMA_RELEASE_DATE_FORMAT = '%Y-%m-%d'

ALMA_TAP_SYNC_URL = 'https://almascience.nrao.edu/tap/sync'


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

    where = ''
    if start or end:
        if start:
            where = 'WHERE t_min>{}'.format(AstropyTime(start).mjd)
            if end:
                where += ' AND t_min<={}'.format(AstropyTime(end).mjd)
        else:
            where = 'WHERE t_min<={}'.format(AstropyTime(end).mjd)
    top = ''

    if maxrec:
        if int(maxrec) < 1:
            raise AttributeError('maxrec must be positive integer')
        top = 'TOP {}'.format(maxrec)
    query = "SELECT {} obs_id AS observationID, min(t_min) AS obsTime " \
            "FROM alma.obscore {} GROUP BY obs_id ORDER by obsTime".\
        format(top, where)
    response = requests.get(ALMA_TAP_SYNC_URL,
                            params={'QUERY': query, 'LANG': 'ADQL'})
    response.raise_for_status()
    temp = BytesIO(response.content)
    obs_ids = parse_single_table(temp)

    result = []
    for r in obs_ids.array:
        obsID = _to_obs_id(r[0].decode('ascii'))
        timestamp = date2ivoa(AstropyTime(r[1], format='mjd').datetime)
        result.append('{}, {}\n'.format(obsID, timestamp))

    return result


def _to_obs_id(member_ouss_id):
    # transformation needed for use as path in URI
    return member_ouss_id.replace('uid://', '').replace('/', '_')


def _to_member_ouss_id(obs_id):
    # reverse transformation
    return 'uid://{}'.format(obs_id.replace('_', '/'))


def get_observation(id):
    """
    Return the observation corresponding to the id
    :param id: id of the observation
    :return: observation corresponding to the id or None if such
    such observation does not exist
    """
    member_ouss_id = _to_member_ouss_id(id)
    # TODO temporary disabled see ticket
    # https://help.almascience.org/index.php?/na/Tickets/Ticket/View/14715
    # Alma.archive_url = 'http://almascience.eso.org'
    results = Alma.query({'member_ous_id': member_ouss_id}, science=False)

    if not results:
        logger.debug('No observation found for ID : {}'.format(member_ouss_id))
        return None
    return member2observation(member_ouss_id, results)


a = Alma()
# alternative mirror when main site doesn't work
# a.archive_url = 'http://almascience.eso.org'


# Code for proxy caom2 service
def member2observation(member_ous, table):
    """ returns an observation object """
    observationID = (member_ous.replace('uid://', '')).replace('/', '_')
    observation = caom2.SimpleObservation('ALMA', observationID)
    for row in table:
        add_calib_plane(observation, row, table)

    # observation metadata is common amongst rows so get it from the first
    # row
    fr = table[0]
    observation.meta_release = \
        datetime.strptime(fr['Observation date'].decode('ascii'),
                          ALMA_DATE_FORMAT)
    add_raw_plane(observation, member_ous, observation.meta_release)
    proposal = caom2.Proposal(fr['ASA_PROJECT_CODE'])
    proposal.project = fr['Project code']
    proposal.pi_name = fr['PI name']
    proposal.title = fr['Project title']
    proposal.keywords = set(fr['Science keyword'].split(','))
    observation.proposal = proposal
    instrument = caom2.Instrument('BAND {}'.format(row['Band'][0]))
    observation.instrument = instrument
    observation.algorithm = caom2.Algorithm('Exposure')
    observation.intent = caom2.ObservationIntentType.SCIENCE
    observation.telescope = \
        caom2.Telescope('ALMA-{}'.format(row['Array'].decode('ascii')),
                        2225142.18, -5440307.37, -2481029.852)
    observation.target = caom2.Target(name='TBD',
                                      target_type=caom2.TargetType.OBJECT)
    return observation


def add_calib_plane(observation, row, table):
    """ Adds a calibrated plane to the observation """
    productID = \
        re.sub('-$', '',
               (re.sub('^-', '', ((re.sub('\W+', '-', row['Source name'])).
                                  replace('--', '-')))))
    plane = caom2.Plane(productID)
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
    # TODO bug in astroquery.alma
    # plane.data_release = datetime.strptime(tmp, ALMA_RELEASE_DATE_FORMAT)

    plane.position = _get_position(row, table)
    plane.energy = _get_energy(row)
    plane.time = _get_time(row, table)
    plane.polarization = _get_polarization(row)

    plane.data_product_type = caom2.DataProductType.VISIBILITY
    plane.calibration_level = caom2.CalibrationLevel.CALIBRATED
    observation.planes[productID] = plane


def add_raw_plane(observation, member_ous, meta_release):
    """ Adds raw plane to observation """
    productID = observation.observation_id + '-raw'
    plane = caom2.Plane(productID)
    plane.artifacts = caom2.TypedOrderedDict(caom2.Artifact)
    plane.meta_release = meta_release
    plane.calibration_level = caom2.CalibrationLevel.RAW_INSTRUMENTAL
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
    """ Adds a raw artifact to the plane """
    filename = file_url.split('/')[-1]
    file_uri = 'alma:ALMA/' + filename
    file_header = requests.head(file_url)
    content_type = file_header.headers['Content-Type']
    if content_type == '':
        content_type = mimetypes.guess_type(file_url)[0]
    if 'asdm' in filename:
        product_type = caom2.ProductType.SCIENCE
        content_length = int(file_header.headers['Content-Length'])
    else:
        product_type = caom2.ProductType.AUXILIARY
        content_length = None
    artifact = caom2.Artifact(file_uri, product_type, caom2.ReleaseType.META,
                              content_type=content_type,
                              content_length=content_length)
    plane.artifacts[file_uri] = artifact


def _get_position(row, table):
    # Extracts position from a returned row of the ALMA results table
    position = caom2.Position()
    position.resolution = row['Spatial resolution']
    # Shape is circle
    # make sure all units are degrees
    ra = row['RA'] * table['RA'].unit.to(u.deg)
    dec = row['Dec'] * table['Dec'].unit.to(u.deg)
    radius = row['Field of view'] * table['Field of view'].unit.to(u.deg) / 2.0
    circle = caom2.Circle(caom2.Point(ra, dec), radius)
    position.bounds = circle
    return position


def _get_energy(row):
    # Extracts the energy inform from a returned row
    min_bound = None
    max_bound = None
    si = []  # list of non-overlapping sub-intervals
    for b in re.findall(r'\[([^]]*)\]', row['Frequency support']):
        e_int = b.split(',')[0]
        vals = e_int.split('..')
        lower_freq = float(vals[0])
        # upper string of form: 123.45GHz
        upper_str = re.findall(r'\b\d+\.?\d+', vals[1])[0]
        upper_freq = float(upper_str)
        units = u.Unit(vals[1][len(upper_str):])
        # wavelengths in meters:
        upper = \
            (lower_freq*units).to(u.meter, equivalencies=u.spectral()).value
        lower = \
            (upper_freq*units).to(u.meter, equivalencies=u.spectral()).value
        si = _add_subinterval(si, (lower, upper))
        if min_bound is not None:
            min_bound = min(min_bound, lower)
        else:
            min_bound = lower
        if max_bound is not None:
            max_bound = max(max_bound, upper)
        else:
            max_bound = upper
    samples = []
    for s in si:
        samples.append(SubInterval(s[0], s[1]))
    bounds = caom2.Interval(min_bound, max_bound, samples=samples)
    return caom2.Energy(bounds=bounds)


def _add_subinterval(si_list, subinterval):
    # Adds and interval to a list of intervals eliminating (merging) any
    # overlaps

    if not si_list:
        return [subinterval]
    # check for overlaps
    # begining of the list?
    if subinterval[1] < si_list[0][0]:
        return [subinterval] + si_list
    if subinterval[0] > si_list[-1][1]:
        return si_list + [subinterval]
    result = []
    for si in si_list:
        if (si[0] >= subinterval[0] and si[0] <= subinterval[1]) or\
           (subinterval[0] >= si[0] and subinterval[0] <= si[1]):
            # overlap detected
            subinterval = (min(si[0], subinterval[0]),
                           max(si[1], subinterval[1]))
        else:
            if subinterval[0] < si[0]:
                result += [subinterval]
                result += si_list[si_list.index(si):]
                return result
            else:
                result += [si]
    return result + [subinterval]


def _get_time(row, table):
    # Extracts time information from a rrow fo returned ALMA table
    time = caom2.Time()
    time.exposure = \
        row['Integration'] * table['Integration'].unit.to(u.second)
    time_lb = AstropyTime(datetime.strptime(
        row['Observation date'].decode('ascii'), ALMA_DATE_FORMAT))
    time_ub = time_lb + time.exposure * u.second
    time_interval = caom2.Interval(time_lb.mjd, time_ub.mjd)
    samples = SubInterval(time_lb.mjd, time_ub.mjd)
    time_interval.samples = [samples]
    time.bounds = time_interval
    return time


def _get_polarization(row):
    # Extracts polarization information from a row
    polarization = caom2.Polarization()
    polarization.polarization_states = \
        [caom2.PolarizationState(i) for i in row['Pol products'].split()]
    return polarization
