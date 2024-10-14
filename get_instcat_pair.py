import numpy as np
import rubin_sim_util
import opsim_util
import plotting

def get_args():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--login', default=False, action='store_true', help='use if first time on new machine!')
    parser.add_argument('--l', default=40, type=float)
    parser.add_argument('--b', default=-15, type=float)
    parser.add_argument('--seed', default=23526, type=int)
    parser.add_argument('--exptime', default=15., type=float)
    parser.add_argument('--filter', default=3, type=int)
    parser.add_argument('--N', default=100000, type=int)
    parser.add_argument('--window', default=0.12, type=float)
    parser.add_argument('--dust', default=True, action='store_false')
    parser.add_argument('--noplot', default=False, action='store_true')
    parser.add_argument('--randomize', default=False, action='store_true')
    parser.add_argument('--magcut', default=None)
    parser.add_argument('--catdir', default='./instcats/')
    parser.add_argument('--pair', default=None)
    parser.add_argument('--db', default='/Users/clairealice/Documents/share/sim_baseline/baseline_v3.3_10yrs.db')
    parser.add_argument('--mplstyle', default='/Users/clairealice/Documents/clem.mplstyle')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = get_args()

    if args.login:
        from getpass import getpass
        from dl import authClient as ac
        token = ac.login(input("Enter user name: "),getpass("Enter password: "))
        ac.whoAmI()
    
    rng = np.random.default_rng(args.seed)

    if not args.noplot:
        import matplotlib.pyplot as plt
        import plotting
        plt.style.use(args.mplstyle)
        plotting.plot_galactic_coord(args.l, args.b)

    # convert to celestial coords
    ra, dec = opsim_util.get_celestial_coord(args.l, args.b)

    # query baseline for visits near that spot, choose pair close together and with few day lag
    visit_1, visit_2 = opsim_util.get_opsim_visit_pair(ra, dec, args.db)
    
    # make header for both cats
    header_1 = opsim_util.assemble_instcat_header(visit_1, seed=int(rng.uniform()*1000), exptime_=args.exptime)
    header_2 = opsim_util.assemble_instcat_header(visit_2, seed=int(rng.uniform()*1000), exptime_=args.exptime)
    
    # artificially tweak ra/dec to be separated by just 10 arcsec (=.00278 deg) dither
    new_ra = np.mean([header_1['rightascension'], header_2['rightascension']])
    new_dec = np.mean([header_1['declination'], header_2['declination']])

    header_1['rightascension'] = new_ra
    header_1['declination'] = new_dec
    header_2['rightascension'] = new_ra + (1/360) * np.sqrt(2)
    header_2['declination'] = new_dec + (1/360) * np.sqrt(2)

    # query rubin_sim for stars that fall within 1 + sqrt(2) * CCD area of the observation center
    ra_min, ra_max = new_ra - args.window * (1 + np.sqrt(2)), new_ra + args.window * (1 + np.sqrt(2))
    dec_min, dec_max = new_dec - args.window * (1 + np.sqrt(2)), new_dec + args.window * (1 + np.sqrt(2))
    
    out = rubin_sim_util.query_data_lab(ra_min, ra_max, dec_min, dec_max, args.N, expid=None, save=False)    

    # dump into .txt with the instcat headers above
    if args.pair is not None:
        pair = args.pair
    else:
        pair = str(int(np.random.uniform() * 1000))

    np.savetxt(args.catdir+f'imags_p{pair}.txt', out['imag'].to_numpy())
    

    # launch imsim for both
    # run alignment
    # check header for seeing
    # use seeing to run hotpants (det which is template vs img, and size of gauss)