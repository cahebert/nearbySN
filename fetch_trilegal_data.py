# import matplotlib.pyplot as plt
# plt.style.use('./clem.mplstyle')
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
        np.savetxt(f'gc_instcats/gc_values_{expid}.txt', np.array(result['gc']))
               
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
    
    summary_f = './gc_instcats/pointing_summaries.txt'
    with open(summary_f, 'a') as f:
        f.write(' '.join([str(s) for s in summary]) + '\n')
        

def make_inst_cat(df, header, dust=True):
    """Make a instance catalog based on TRILEGAL dataframe.
    
    Dataframe columns must include ra, dec, av, and gmag."""
    print("Assembling catalog...\n")

    expid = "00"+str(int(header["obshistid"]))
    # for now, same SED file for everyone
    sedpath = 'starSED/phoSimMLT/lte035-4.5-1.0a+0.4.BT-Settl.spec.gz'
    fname = f'instcat_trilegal_{expid}{"" if dust else "_nodust"}.txt'
    fname = 'gc_instcats/' + fname

    # open file in append mode
    try:
        _ = open(fname, 'r')

        # if we can open the instant catalog, then it exists -> need a new file.
        fname = f'instcat_trilegal_{expid}{"" if dust else "_nodust"}_{int(np.random.uniform(1000))}.txt'
        fname = 'gc_instcats/' + fname
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

    print(f"Successfully written catalog of length {len(df)} to file {'gc_instcats/' + fname}.\n")
    return fname


def plot_stars(df, header):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    plt.style.use('./clem.mplstyle')
    import seaborn as sns

    f, a = plt.subplots(1,2, figsize=(8,4), gridspec_kw={'width_ratios':[1,0.6]})
    # thin disk=1, thick disk=2, halo=3, bulge=4

    # List of RGB triplets
    rgb_values = sns.color_palette("husl", 4)[::-1]
    # Map label to RGB
    color_map = sns.color_palette("husl", 4, as_cmap=True)

    handles = [Line2D([0], [0], color=rgb_values[0], marker='o', linestyle='', label='thin disk'),
               Line2D([0], [0], color=rgb_values[1], marker='o', linestyle='', label='thick disk'),
               Line2D([0], [0], color=rgb_values[2], marker='o', linestyle='', label='halo'),
               Line2D([0], [0], color=rgb_values[3], marker='o', linestyle='', label='bulge')]

    a[0].scatter(df['ra'], df['dec'], s=1, c=df['gc'], cmap=color_map, vmin=df['gc'].min()-.5, vmax=df['gc'].max()+.5)
    a[0].plot(header['rightascension'], header['declination'], 'kx', ms=10, markeredgewidth=1)
    a[0].set_xlabel('RA')
    a[0].set_ylabel('Dec')

    a[0].legend(handles=handles, loc='upper left', bbox_to_anchor=(0.95,1))

    a[1].hist(df['magnorm'], histtype='step', label=f'N={len(df)}')
    a[1].set_yscale('log')
    a[1].set_xlabel('$g$ mag')
    a[1].set_ylabel('N')
    a[1].legend(loc='upper left')

    plt.savefig(f'plots/trilegal_stars_{expid}.png', dpi=200, facecolor='w', transparent=False)


def main(args):
    import opsim_pointing
    ra, dec = opsim_pointing.get_celestial_coord(args.l, args.b)
    
    # window argument should be in degrees
    ra_min, ra_max = ra - args.window, ra + args.window
    dec_min, dec_max = dec - args.window, dec + args.window
    
    # OpSim query
    ops_visit = opsim_pointing.get_opsim_visit(ra, dec)
    ops_header = opsim_pointing.assemble_instcat_header(ops_visit,
                                                        seed=args.seed,
                                                        filter_=args.filter)
    expid = "00"+str(int(ops_header["obshistid"]))
    
    # TRILEGAL query
    out = query_data_lab(ra_min, ra_max, dec_min, dec_max, args.N, expid)    
    
    save_summary(expid, out, ops_header, args)
    if not args.noplot:
        plot_stars(out, ops_header)
        
    make_inst_cat(out, header=ops_header, dust=args.dust)


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
