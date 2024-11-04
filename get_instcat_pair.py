import numpy as np
import rubin_sim_util
import opsim_util
import plotting

def get_healpix_info(ra, dec, neighbors=True, nside=4096, nest=True):
    import healpy
    # get ra/dec central to that healpix, will be what we query opsim for
    healpix = healpy.ang2pix(nside, theta=ra, phi=dec, lonlat=True, nest=nest)
    ra, dec = healpy.pix2ang(nside, healpix, lonlat=True, nest=nest)

    if neighbors:
        healpix = [healpix]
        healpix += list(healpy.get_all_neighbours(nside, healpix[0], nest=True))

    return ra, dec, healpix


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
    parser.add_argument('--keeppos', default=False, action='store_true')
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
    ra, dec, healpix = get_healpix_info(ra, dec)

    # query baseline for visits near that spot, choose pair close together and with few day lag
    visit_1, visit_2 = opsim_util.get_opsim_visit_pair(ra, dec, args.db)

    # make header for both cats
    header_1 = opsim_util.assemble_instcat_header(visit_1, seed=int(rng.uniform()*1000), exptime_=args.exptime)
    header_2 = opsim_util.assemble_instcat_header(visit_2, seed=int(rng.uniform()*1000), exptime_=args.exptime)

    # artificially tweak ra/dec to be separated by just 10 arcsec (=.00278 deg) dither
    delta_ra = 0.00278

    header_1['rightascension'] = ra
    header_1['declination'] = dec
    header_2['rightascension'] = ra + delta_ra
    header_2['declination'] = dec + delta_ra

    out = rubin_sim_util.query_data_lab(healpix, args.N, indextype='nest4096', magcut=args.magcut, save=False)

    # dump into .txt with the instcat headers above
    if args.pair is not None:
        pair = args.pair
    else:
        pair = str(int(np.random.uniform() * 1000))

    np.savetxt(args.catdir+f'imags_p{pair}.txt', out['imag'].to_numpy())

    rubin_sim_util.make_inst_cat(out,
                                 header=header_1,
                                 catdir=args.catdir,
                                 dust=args.dust,
                                 pair=pair,
                                 randomize=~args.keeppos)

    rubin_sim_util.make_inst_cat(out,
                                 header=header_2,
                                 catdir=args.catdir,
                                 dust=args.dust,
                                 pair=pair,
                                 randomize=~args.keeppos,
                                 write_stars=False)
