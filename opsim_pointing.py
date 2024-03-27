def get_celestial_coord(l, b):
    from astropy import units as u
    from astropy.coordinates import SkyCoord
    
    gc_galactic = SkyCoord(frame='galactic', l=l*u.degree, b=b*u.degree)
    gc_celestial = gc_galactic.icrs
    
    return gc_celestial.ra.degree, gc_celestial.dec.wrap_at('180d').degree
    
def get_opsim_visit(GC_RA, GC_DEC, db_path):
    import sqlite3
    import pandas as pd
    import numpy as np

    # baseline_db = '/gpfs02/astro/workarea/esheldon/rubin_sim_data/opsim-databases/baseline_v3.3_10yrs.db'
    con = sqlite3.connect(db_path)

    # Some of the columns you might be interested in
    cols = ['observationStartMJD', 'observationId', 'seeingFwhm500']
    cols += ['fieldRA', 'fieldDec']
    cols += ['rotSkyPos', 'rotTelPos']
    cols += ['altitude', 'azimuth']
    cols += ['sunAlt', 'moonAlt', 'moonRA', 'moonDec', 'moonDistance', 'moonPhase']

    query = \
        """SELECT {:s} 
           FROM observations 
           WHERE (fieldRA BETWEEN {} AND {} AND fieldDec BETWEEN {} AND {})
           """.format(', '.join(cols), GC_RA-0.15, GC_RA+0.15, GC_DEC-0.15, GC_DEC+0.15)

    # Read these columns in from the "Summary" table, convert into a Pandas df
    db = pd.read_sql_query(query, con)

    i_min = np.hypot(GC_RA-db['fieldRA'], GC_DEC-db['fieldDec']).argmin()
    return db.iloc[i_min]

def assemble_instcat_header(visit, filter_=None, seed=None):
    
    column_conversion = {
                         'fieldRA' : 'rightascension',
                         'fieldDec' : 'declination',
                         'observationStartMJD' : 'mjd',
                         'observationId' : 'obshistid',
                         'rotSkyPos' : 'rotskypos',
                         'rotTelPos' : 'rottelpos',
                         'altitude' : 'altitude',
                         'azimuth' : 'azimuth',
                         'sunAlt' : 'sunalt',
                         'moonAlt' : 'moonalt',
                         'moonRA' : 'moonra',
                         'moonDec' : 'moondec',
                         'moonDistance' : 'dist2moon',
                         'moonPhase' : 'moonphase',
                         'seeingFwhm500' : 'seeing',
                        }
    visit.rename(index=column_conversion, inplace=True)
    visit = visit.to_dict()
    
    fixed_rows = {
                  'nsnap': 1,
                  'vistime': 30.0,
                  'seqnum': 0,
                  'filter': filter_ if filter_ is not None else 2,
                  'seed': seed if seed is not None else 398414,
                  }
    
    visit.update(fixed_rows)

    return visit
    