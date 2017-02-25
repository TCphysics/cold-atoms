from .context import coldatoms
import numpy as np

speed_of_light = 3.0e8
wavelength = 1.0e-6
hbar_k = 1.0e-34 * np.array([2.0 * np.pi / wavelength, 0.0, 0.0])


class ConstantIntensity(object):
    def __init__(self, intensity):
        self.intensity = intensity

    def intensities(self, x):
        return np.full(x.shape[0], self.intensity)


class ConstantDetuning(object):
    def __init__(self, detuning):
        self.detuning = detuning

    def detunings(self, x, v):
        return np.full(x.shape[0], self.detuning)


intensity = ConstantIntensity(0.1)
detuning = ConstantDetuning(0.0)


def test_can_create_resonance_fluorescence():
    fluorescence = coldatoms.RadiationPressure(1.0e8, hbar_k, intensity, detuning)


def test_force_is_non_zero():
    fluorescence = coldatoms.RadiationPressure(1.0e8, hbar_k, intensity, detuning)
    ensemble = coldatoms.Ensemble()
    # In one millisecond we expect to scatter more than one photon
    f = fluorescence.force(1.0e-3, ensemble)
    assert(np.linalg.norm(f) > np.linalg.norm(hbar_k))
