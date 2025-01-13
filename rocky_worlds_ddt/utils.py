#! /usr/bin/env python
"""
Utilities module for the Rocky Worlds DDT project.

Authors
-------
- Mees Fix
"""
import warnings

from astroquery.ipac.nexsci.nasa_exoplanet_archive import NasaExoplanetArchive
from astropy.coordinates import SkyCoord
from astropy.time import Time
import astropy.units as u
from astroquery.mast import MastMissions
import numpy as np

warnings.filterwarnings("ignore")

def check_jwst_observations(ra, dec, radius=0.1):
    """Check MAST to see if target ra and dec has JWST observations.

    Parameters
    ----------
    ra : float
        Target Right Ascension (units: deg)
    dec : float
        Target Declination (units: deg)
    radius : float
        Search radius around ra and dec [default: 0.1]

    Returns
    -------
    results : astropy.Table.table
        Astropy table of query results
    """
    regionCoords = SkyCoord(float(ra), float(dec), unit=("deg", "deg"))
    missions = MastMissions(mission="jwst")
    results = missions.query_region(
        regionCoords,
        radius=radius,
        select_cols=[
            "targprop",
            "targ_ra",
            "targ_dec",
            "instrume",
            "exp_type",
            "opticalElements",
            "date_obs",
            "duration",
            "program",
            "observtn",
            "visit",
            "pi_name",
            "proposal_type",
            "proposal_cycle",
            "targtype",
            "access",
        ],
    )

    return results


def check_jwst_observation_type(planet_name, period, planet_ephemeris, jwst_observations):
    """
    This fough code tries to figure out, given some target information and
    an observation start and end time,what exoplanet event is being
    observed: transit, eclipse, phase curve, or nothing.

    This code may be buggy and has not been well-tested.

    WARNING: This only makes any sense if you already know what host star
    is being observing for the observation start/end, and then test the
    planets in that system. Otherwise, you can put in any time range,
    and for a large enough sample of planets, you will probably randomly
    hit on a transit/eclispe/phase curve event. This may be obvious but
    there you are.

    Parameters
    ----------
    planet_name : str
        Name of your target
    period : float
        Period of exoplanet
    planet_ephemeris : float
        The reference time for a transit mid-point.
    jwst_observations : astropy.Table.table
        Astropy table of results from astroquery.mast.MastMissions('jwst') query.
        See `query_mast_jwst_archive` function.
    """

    # Create time objects for API data to get them in same units as Exoplanet Archive data.
    obs_start = (
        Time(jwst_observations["date_obs"], format="isot", scale="utc").jd * u.day
    )
    obs_end = obs_start + (jwst_observations["duration"] * u.second).to(u.day)

    table_data = []
    for row, (start, end) in enumerate(zip(obs_start, obs_end)):
        n_start = (start - planet_ephemeris) / period
        n_end = (end - planet_ephemeris) / period
        n = int(n_start)

        phase_start = n_start - n
        phase_end = n_end - n

        if phase_end - phase_start > 1:
            observation_type = "PHASE CURVE"
        elif phase_start < 0.5 < phase_end:
            observation_type = "SECONDARY ECLIPSE"
        elif phase_start < 1.0 < phase_end:
            observation_type = "TRANSIT"
        else:
            observation_type = "NO EVENT"

        phase_data = {
            "planet_name": planet_name,
            "obs_type": observation_type,
            "phase_start": phase_start,
            "phase_end": phase_end,
            "orbit_start": n_start,
            "orbit_end": n_end,
        }
        table_data.append(phase_data)

    for key in phase_data:
        jwst_observations.add_column(
            [x[key] for x in table_data], name=key
        )

    return jwst_observations


def query_mast_jwst_archive(ra, dec, jwst_query_radius=0.1):
    """Query the MAST Archive for JWST observations at a given ra and dec.

    Parameters
    ----------
    ra : float
        Right ascension of target
    dec : float
        Declination of target

    Returns
    -------
    jwst_observations : astropy.Table.table
        An astropy table of targets that meet criteria provided.
    """
    jwst_observations = check_jwst_observations(ra, dec, jwst_query_radius)
    return jwst_observations


def query_nexsci_archive(target_name):
    """Query NASA NexSci Exoplanet Archive for planetary parameters.

    Parameters
    ----------
    target_name : str
        Name of exoplanet to query database on. The string is case sensitive.
    """
    all_planet_data = NasaExoplanetArchive.query_criteria(
        table="ps",
        select="pl_name, ra, dec, pl_orbper, pl_tranmid, pl_refname, default_flag",
        where=f"pl_name='{target_name}'",
    )

    # See if the preferred data set from NEA
    preferred_data_index = np.where(all_planet_data["default_flag"] == 1)[0]

    return all_planet_data, preferred_data_index
