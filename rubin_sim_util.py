import numpy as np
import astropy.units as u
import astropy.constants as constants

def query_data_lab(index, N, indextype='nest4096',expid=None, magcut=None, save=False):
    """Fetch TRILEGAL positions and gmag for a given ra/dec region."""
    from dl import queryClient as qc

    magstring = f'AND imag<{magcut}' if magcut is not None else ''
    if indextype == 'nest4096':
        index = ' in ('+', '.join([str(i) for i in index])+')'
    else:
        index = f'={index}'
    query = \
       """SELECT ra, dec, av, imag, gc, logte, logg, logl, mu0, z
          FROM lsst_sim.simdr2
          WHERE ({}{} AND label!=9 {})
          LIMIT {}
          """.format(indextype, index, magstring, N)

    print("Submitting request:\n")
    print(query)

    result = qc.query(sql=query,
                      fmt='pandas',
                      async_=True,
                      wait=True,
                      poll=15,
                      verbose=1)

    print(f"Request complete: catalog length {len(result)}")

    if save:
        np.savetxt(f'{args.catdir}/gc_values_{expid}.txt', np.array(result['gc']))

    return result

def random_points_within_polygon(ra, dec, n_points, seed=None):
    """Function to generate random points within RA/Dec area"""
    from shapely.geometry import Polygon, Point

    points = []
    points.append((ra[np.argmin(ra)], dec[np.argmin(ra)]))
    points.append((ra[np.argmin(dec)], dec[np.argmin(dec)]))
    points.append((ra[np.argmax(ra)], dec[np.argmax(ra)]))
    points.append((ra[np.argmax(dec)], dec[np.argmax(dec)]))
    polygon = Polygon(points)

    min_x, min_y, max_x, max_y = polygon.bounds
    positions = []

    rng = np.rangom.default_rng(seed)
    while len(positions) < n_points:
        random_point = Point(rng.uniform(min_x, max_x), rng.uniform(min_y, max_y))
        if polygon.contains(random_point):
            positions.append(random_point)

    return np.array([[point.x, point.y] for point in positions])

def randomize_positions(df):
    """Randomize positions of stars in dataframe."""
    ra = df['ra'].to_numpy()
    dec = df['dec'].to_numpy()
    new_positions = random_points_within_polygon(ra, dec, len(ra))
    df['ra'] = new_positions[:,0]
    df['dec'] = new_positions[:,1]
    return df

def save_summary(expid, df, header, args):
    # expid, ra, dec, gal l, gal b, n_stars, n_stars w g>24.5, p_thin, p_thick, p_halo, p_bulge
    summary = [
        expid,
        header['rightascension'],
        header['declination'],
        args.l,
        args.b,
        len(df),
        # len(df[df['imag']<24.5]),
        len(df[df['gc']==1]) / len(df),
        len(df[df['gc']==2]) / len(df),
        len(df[df['gc']==3]) / len(df),
        len(df[df['gc']==4]) / len(df),
    ]

    summary_f = f'{args.catdir}/pointing_summaries.txt'
    with open(summary_f, 'a') as f:
        f.write(' '.join([str(s) for s in summary]) + '\n')

# def get_sed_info(star, etoiles, index, sed_path='/Users/clairealice/Documents/share/rubin_sim_data/sims_sed_library/'):
#     """Returns magnorm and path to file for SED of given star.

#     star is dict or row of dataframe."""
#     import galsim
#     import astropy.units as u
#     import astropy.constants

#     sed_cols = ['logte','logg','logl','z']
#     sed = etoiles.get_intrinsic_sed(**star[sed_cols].to_dict())
#     sed = etoiles.convert_to_observed(sed, star['mu0'])

#     lams = np.linspace(sed.blue_limit, 1500, 2000)
#     fname = f'lsstsim_sample/nsn_sed_index{index}.txt'
#     with open(sed_path + fname, 'w+') as f:
#         f.writelines(f'{l} {f}\n' for l,f in zip(lams, sed._spec(lams)))

#     wl = 500*u.nm
#     hnu0 = (astropy.constants.h*astropy.constants.c)/wl
#     flambda0 = hnu0 * sed(wl.value) * (1./u.nm/u.cm**2/u.s)
#     fnu0 = flambda0 * wl**2 / astropy.constants.c
#     magnorm = fnu0.to_value(u.ABmag)

#     return magnorm, fname

def get_magnorm(sed):
    wl = 500*u.nm
    hnu0 = (constants.h*constants.c)/wl
    flambda0 = hnu0 * sed(wl.value) * (1./u.nm/u.cm**2/u.s)
    fnu0 = flambda0 * wl**2 / constants.c
    return fnu0.to_value(u.ABmag)

def get_sed_info(star, etoiles, index, sed_path='/Users/clairealice/Documents/share/rubin_sim_data/sims_sed_library/'):
    """Returns magnorm and path to file for SED of given star.
    star is dict or row of dataframe."""
    sed_cols = ['logte','logg','logl','z']
    sed = etoiles.get_intrinsic_sed(**star[sed_cols].to_dict())
    sed = etoiles.convert_to_observed(sed, star['mu0'])

    lams = np.linspace(sed.blue_limit, 1500, 2000)
    fname = f'lsstsim_sample/nsn_sed_index{index}.txt'
    with open(sed_path + fname, 'w+') as f:
        f.writelines(f'{l} {f}\n' for l,f in zip(lams, sed._spec(lams)))

    return get_magnorm(sed), fname

def make_inst_cat(df, header, catdir,
                  magcut=True, randomize=True,
                  dust=True, pair=None, write_stars=True):
    """Make a instance catalog based on TRILEGAL dataframe.

    Dataframe columns must include ra, dec, av, and gmag."""
    import pylumiere
    print("Assembling catalog...\n")

    expid = "00"+str(int(header["obshistid"]))
    if pair is not None:
        pair = '_p' + str(pair)
    else:
        pair = ''

    fname = f'instcat_trilegal{pair}_{expid}{"" if dust else "_nodust"}.txt'
    fname = catdir + fname

    # open file in append mode
    try:
        _ = open(fname, 'r')

        # if we can open the instant catalog, then it exists -> need a new file.
        fname = f'instcat_trilegal{pair}_{expid}{"" if dust else "_nodust"}_{int(np.random.uniform(1000))}.txt'
        fname = catdir + fname
        print(f'file already exists, saving under: {fname}\n')
        instCat = open(fname, 'a')

    except FileNotFoundError:
        instCat = open(fname, 'a')

    # write header section
    for key, val in header.items():
        instCat.write(f'{key} {val}\n')

    if write_stars:
        if randomize:
            df = randomize_positions(df)
        etoiles = pylumiere.Stellib('BTSettl', rv=3.1, dustmodel='O94')
        # now write objects
        for row in df.index:
            df_row = df.loc[row]
            magnorm, sedpath = get_sed_info(df_row, etoiles, row)
            to_write = f"object {row} {df_row['ra']} {df_row['dec']} {magnorm} {sedpath} " + \
                    f"0 0 0 0 0 0 point none CCM " + \
                    f"{df_row['av'] if dust else 0} 3.1\n"
            instCat.write(to_write)

    instCat.close()

    print(f"Successfully written catalog of length {len(df)} to file {fname}.\n")
    return fname

# def main(args):
#     import opsim_util
#     ra, dec = opsim_util.get_celestial_coord(args.l, args.b)

#     import healpy
#     healpix = healpy.ang2pix(256, theta=args.l, phi=args.b, lonlat=True)

#     # OpSim query
#     ops_visit = opsim_util.get_opsim_visit(ra, dec, args.db)
#     ops_header = opsim_util.assemble_instcat_header(ops_visit,
#                                                         seed=args.seed,
#                                                         exptime_=args.exptime,
#                                                         filter_=args.filter)
#     expid = "00"+str(int(ops_header["obshistid"]))

#     # TRILEGAL query
#     out = query_data_lab(healpix, args.N)

#     save_summary(expid, out, ops_header, args)
#     if not args.noplot:
#         import matplotlib.pyplot as plt
#         import plotting
#         plt.style.use(args.mplstyle)

#         plotting.plot_stars(out, ops_header)

#     make_inst_cat(out, header=ops_header, catdir=args.catdir, dust=args.dust)


# def get_args():
#     from argparse import ArgumentParser
#     parser = ArgumentParser()
#     parser.add_argument('--login', default=False, action='store_true')
#     parser.add_argument('--l', default=0, type=float)
#     parser.add_argument('--b', default=0, type=float)
#     parser.add_argument('--seed', default=23526, type=int)
#     parser.add_argument('--exptime', default=15., type=float)
#     parser.add_argument('--filter', default=2, type=int)
#     parser.add_argument('--N', default=100000, type=int)
#     parser.add_argument('--window', default=0.12, type=float)
#     parser.add_argument('--dust', default=True, action='store_false')
#     parser.add_argument('--noplot', default=False, action='store_true')
#     parser.add_argument('--catdir', default='./instcats')
#     parser.add_argument('--db', default='~/Documents/share/sim_basline/baseline_v3.3_10yrs.db')
#     parser.add_argument('--mplstyle', default='~/Documents/clem.mplstyle')
#     args = parser.parse_args()
#     return args

# if __name__ == '__main__':

#     args = get_args()

#     if args.login:
#         from getpass import getpass
#         from dl import authClient as ac
#         token = ac.login(input("Enter user name: "),getpass("Enter password: "))
#         ac.whoAmI()

#     main(args)
