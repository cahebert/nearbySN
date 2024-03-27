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


def get_opsim_visit_pair(GC_RA, GC_DEC, db_path):
    import sqlite3
    import pandas as pd
    import numpy as np

    con = sqlite3.connect(db_path)

    cols = ['observationStartMJD', 'observationId', 'seeingFwhm500']
    cols += ['fieldRA', 'fieldDec']
    cols += ['rotSkyPos', 'rotTelPos']
    cols += ['altitude', 'azimuth']
    cols += ['sunAlt', 'moonAlt', 'moonRA', 'moonDec', 'moonDistance', 'moonPhase']

    query = \
        """SELECT {:s} 
           FROM observations 
           WHERE (fieldRA BETWEEN {} AND {} AND fieldDec BETWEEN {} AND {})
           """.format(', '.join(cols), GC_RA-1, GC_RA+1, GC_DEC-1, GC_DEC+1)

    # Read these columns in from the "Summary" table, convert into a Pandas df
    db = pd.read_sql_query(query, con)
    
    # entries ordered by MJD, so first narrow options with that
    diffdb = db - db.shift(periods=1)
    
    diffdb = diffdb[diffdb['observationStartMJD']>2]
    diffdb = diffdb[diffdb['observationStartMJD']<8]

    diffdb['fieldDelta'] = np.hypot(diffdb['fieldDec'], diffdb['fieldRA'])
    i_min = diffdb.index[diffdb['fieldDelta']==diffdb['fieldDelta'].min()]

    if diffdb['fieldDelta'].min() > 1:
        print('check the field choices, position difference is large!')

    return db.loc[i_min].iloc[0], db.loc[i_min-1].iloc[0] #iloc to convert to series


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
    