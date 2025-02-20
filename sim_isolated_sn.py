import galsim
import numpy as np
import astropy.units as u
import astropy.constants as constants
import rubin_sim_util as utils

bandpasses = {
    f: galsim.Bandpass(f"LSST_{f}.dat", wave_type="nm").withZeropoint("AB")
    for f in ["r", "i"]
}

def blackbody_luminosity(
    wl,
    temperature=None,
):
    import math
    return (
        2 * math.pi * constants.h * constants.c**2
        / (wl * u.nm)**5
        / (np.exp(constants.h * constants.c / (wl * u.nm * constants.k_B * temperature * u.K)) - 1)
    ).to(galsim.SED._flambda).value

def get_blackbody_spectrum(
    temperature,
    imag_goal,
):
    import functools
    sed = galsim.SED(
        functools.partial(
            blackbody_luminosity,
            temperature=temperature,
        ),
        wave_type="nm",
        flux_type="flambda"
    )

    imag = sed.calculateMagnitude(bandpass=bandpasses['i'])

    return utils.get_magnorm(sed), sed * 10**((imag_goal-imag) / -2.5)

def get_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--expid", type=str)
    parser.add_argument("--pair", type=int)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--sedpath", default='/Users/clairealice/Documents/share/rubin_sim_data/sims_sed_library/')
    parser.add_argument("--icpath", default='/Users/clairealice/Documents/git/nearbySN/instcats/')
    return parser.parse_args()

if __name__ == "__main__":
    args = get_args()
    rng = np.random.default_rng(args.seed)

    ## need realistic input values for av and temp; FOR NOW use one of these values
    import pickle
    with open('/Users/clairealice/Documents/git/pystellibs/trilegal_examples_randid.p', 'rb') as f:
        stars = pickle.load(f)
    # choose a random star
    star = stars.sample(1)
    temp = star['logte'].values[0]
    # FOR NOW set a target magnitude
    imag = 19

    magnorm, spec = get_blackbody_spectrum(10**temp, imag_goal=imag)
    lams = np.linspace(spec.blue_limit, 1500, 2000)
    sedfile = f'lsstsim_sample/blackbody-t{temp}-imag{imag}.txt'
    with open(args.sedpath + sedfile, 'w+') as f:
        f.writelines(f'{l} {f}\n' for l,f in zip(lams, spec._spec(lams)))

    icfile = args.icpath + f'instcat_trilegal_p{args.pair}_{args.expid}.txt'
    header = np.loadtxt(icfile, max_rows=20, dtype='str')
    header = {l[0]: l[1] for l in header}

    fname = args.icpath + f'instcat_sn_{args.expid}-t{temp}-imag{imag}.txt'
    # open file in append mode
    instCat = open(fname, 'a')

    for key, val in header.items():
        instCat.write(f'{key} {val}\n')

    # move SN to a few arcmin away from center
    ra = float(header['rightascension']) - 2/60
    dec = float(header['declination']) + 2/60
    to_write = f"object 0 {ra} {dec} {magnorm} {sedfile} " + \
                    f"0 0 0 0 0 0 point none CCM " + \
                    f"{star['av'].values[0]} 3.1\n"

    instCat.write(to_write)
    instCat.close()