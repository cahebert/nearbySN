import numpy as np
import atm_psf

date='20240213'
expid='00398414'

seed = 10
rng = np.random.RandomState(seed)

# loads the image, subtractes the sky using sky_level in truth catalog, loads
# WCS from the header, and adds a fake PSF with fwhm=0.8 for detection
exp, hdr = atm_psf.exposures.fits_to_exposure(
    fname=f'{date}/eimage_{expid}-0-r-R22_S11-det094.fits',
    truth=f'{date}/truth_{expid}-0-r-R22_S11-det094.fits',
    rng=rng,
    fwhm=0.8,
)

detmeas = atm_psf.measure.DetectMeasurer(exposure=exp, rng=rng)
detmeas.detect()
detmeas.measure()
sources = detmeas.sources

print(len(sources))

atm_psf.io.save_source_data(fname=f'{date}/sources_{expid}.pkl', data=sources)

