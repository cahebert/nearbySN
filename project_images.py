from astropy.io import fits
from reproject import reproject_interp
    
def get_args():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--images', nargs=2, required=True, default=[])
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = get_args()

    hdu1 = fits.open(args.images[0])[0]
    hdu2 = fits.open(args.images[1])[0]

    array, footprint = reproject_interp(hdu2, hdu1.header)

    savef = args.images[1].split('.')[0] + '_projected.fits'
    fits.writeto(savef, array, hdu1.header, overwrite=True)