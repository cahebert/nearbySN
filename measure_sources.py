import numpy as np
import atm_psf

def get_args():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--images', nargs=2, required=True, default=[])
    parser.add_argument('--seed', default=123)
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = get_args()

    rng = np.random.RandomState(args.seed)

    sizes = []
    expids = []
    for img in args.images:
        truth = '/'.join(img.split('/')[:-1]) +'/truth_' + '_'.join(img.split('_')[1:])
        
        # loads the image, subtractes the sky using sky_level in truth catalog, loads
        # WCS from the header, and adds a fake PSF with fwhm=0.8 for detection
        exp, hdr = atm_psf.exposures.fits_to_exposure(
                                                      fname=img,
                                                      truth=truth,
                                                      rng=rng,
                                                      fwhm=0.8,
        )

        detmeas = atm_psf.measure.DetectMeasurer(exposure=exp, rng=rng)
        detmeas.detect()
        detmeas.measure()
        sources = detmeas.sources

        # print(len(sources))
        
        xx = sources['ext_shapeHSM_HsmSourceMoments_xx']
        yy = sources['ext_shapeHSM_HsmSourceMoments_yy']
        T = xx + yy
        sigma = np.sqrt(T/2) * 0.2 #* 2.3548200450309493 sigma, NOT fwhm
        sizes.append(np.nanmean(sigma))
        exp = img.split('_')[1].split('-')[0]
        expids.append(exp)

        savef = '/'.join(img.split('/')[:-1]) + f'/sources_{exp}.pkl'
        atm_psf.io.save_source_data(fname=savef, data=sources)

    if len(sizes)==2: ## ie doing pair differencing     
        ## sigma_match = sqrt(sig_img**2 - sig_tmp**2)
        ## and want (sigma6=1/2, sigma4=1, sigma2=2) * sigma_match

        if sizes[0] > sizes[1]:
            match = np.sqrt(sizes[0]**2 - sizes[1]**2)
            print(0.5*match, match, 2*match, expids[0], expids[1])
        else:
            match = np.sqrt(sizes[1]**2 - sizes[0]**2)
            print(0.5*match, match, 2*match, expids[1], expids[0])

