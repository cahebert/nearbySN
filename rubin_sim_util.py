import numpy as np

def query_data_lab(ra_min, ra_max, dec_min, dec_max, N, expid, save=True):
    from dl import queryClient as qc

    """Fetch TRILEGAL positions and gmag for a given ra/dec region."""
    query = \
       """SELECT ra, dec, av, gmag, gc 
          FROM lsst_sim.simdr2
          WHERE (ra BETWEEN {} AND {} AND dec BETWEEN {} AND {})
          LIMIT {}
          """.format(ra_min, ra_max, dec_min, dec_max, N)

    print("Submitting request:\n")
    print(query)
    
    result = qc.query(sql=query,
                      fmt='pandas',
                      async_=True,
                      wait=True,
                      poll=15,
                      verbose=1)
    
    if save:
        np.savetxt(f'{args.catdir}/gc_values_{expid}.txt', np.array(result['gc']))
               
    return result


def save_summary(expid, df, header, args):
    # expid, ra, dec, gal l, gal b, n_stars, n_stars w g>24.5, p_thin, p_thick, p_halo, p_bulge
    summary = [
        expid,
        header['rightascension'],
        header['declination'],
        args.l,
        args.b,
        len(df),
        len(df[df['gmag']<24.5]),
        len(df[df['gc']==1]) / len(df),
        len(df[df['gc']==2]) / len(df),
        len(df[df['gc']==3]) / len(df),
        len(df[df['gc']==4]) / len(df),
    ]
    
    summary_f = f'{args.catdir}/pointing_summaries.txt'
    with open(summary_f, 'a') as f:
        f.write(' '.join([str(s) for s in summary]) + '\n')
        

def make_inst_cat(df, header, catdir,  dust=True, pair=None):
    """Make a instance catalog based on TRILEGAL dataframe.
    
    Dataframe columns must include ra, dec, av, and gmag."""
    print("Assembling catalog...\n")

    expid = "00"+str(int(header["obshistid"]))
    if pair is not None:
        pair = '_p' + str(pair)
    else:
        pair = ''

    # for now, same SED file for everyone
    sedpath = 'starSED/phoSimMLT/lte035-4.5-1.0a+0.4.BT-Settl.spec.gz'

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

    # now write objects
    for row in df.index:
        df_row = df.loc[row]
        to_write = f"object {row} {df_row['ra']} {df_row['dec']} {df_row['gmag']} {sedpath} " + \
                   f"0 0 0 0 0 0 point none CCM " + \
                   f"{df_row['av'] if dust else 0} 3.1\n"
        instCat.write(to_write)

    instCat.close()

    print(f"Successfully written catalog of length {len(df)} to file {fname}.\n")
    return fname

def main(args):
    import opsim_pointing
    ra, dec = opsim_pointing.get_celestial_coord(args.l, args.b)
    
    # window argument should be in degrees
    ra_min, ra_max = ra - args.window, ra + args.window
    dec_min, dec_max = dec - args.window, dec + args.window
    
    # OpSim query
    ops_visit = opsim_pointing.get_opsim_visit(ra, dec, args.db)
    ops_header = opsim_pointing.assemble_instcat_header(ops_visit,
                                                        seed=args.seed,
                                                        filter_=args.filter)
    expid = "00"+str(int(ops_header["obshistid"]))
    
    # TRILEGAL query
    out = query_data_lab(ra_min, ra_max, dec_min, dec_max, args.N, expid)    
    
    save_summary(expid, out, ops_header, args)
    if not args.noplot:
        import matplotlib.pyplot as plt
        import plotting
        plt.style.use(args.mplstyle)
        
        plotting.plot_stars(out, ops_header)
        
    make_inst_cat(out, header=ops_header, catdir=args.catdir, dust=args.dust)


def get_args():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--login', default=False, action='store_true')
    parser.add_argument('--l', default=0, type=float)
    parser.add_argument('--b', default=0, type=float)
    parser.add_argument('--seed', default=23526, type=int)
    parser.add_argument('--filter', default=2, type=int)
    parser.add_argument('--N', default=100000, type=int)
    parser.add_argument('--window', default=0.12, type=float)
    parser.add_argument('--dust', default=True, action='store_false')
    parser.add_argument('--noplot', default=False, action='store_true')
    parser.add_argument('--catdir', default='./instcats')
    parser.add_argument('--db', default='~/Documents/share/sim_basline/baseline_v3.3_10yrs.db')
    parser.add_argument('--mplstyle', default='~/Documents/clem.mplstyle')
    args = parser.parse_args()
    return args
    
if __name__ == '__main__':
    
    args = get_args()
    
    if args.login:
        from getpass import getpass
        from dl import authClient as ac
        token = ac.login(input("Enter user name: "),getpass("Enter password: "))
        ac.whoAmI()
        
    main(args)
