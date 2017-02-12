import numpy as np

class Ensemble(object):
    """An ensemble of particles.

    All ensembles have particle positions and velocities. In addition, an
    ensemble may define ensemble properties and per particle properties."""

    def __init__(self, num_ptcls=1):
        self.x = np.zeros([num_ptcls, 3], dtype=np.float64)
        self.v = np.zeros([num_ptcls, 3], dtype=np.float64)
        self.ensemble_properties = {}
        self.particle_properties = {}

    def get_num_ptcls(self):
        return self.x.shape[0]

    num_ptcls = property(get_num_ptcls,
                         'The number of particles in the ensemble')

    def set_particle_property(self, key, prop):
        """Set a particle property.

        key -- The name under which the property is stored.
        prop -- An array of the per particle properties. The array should have
        layout (num_ptcls, ...), i.e. the leading dimension should match the
        number of particles currently in the ensemble. We store a copy of
        prop."""

        if prop.shape[0] != self.num_ptcls:
            raise RuntimeError(
                'Size of property array does not match number of particles.')
        self.particle_properties[key] = np.copy(prop)

    def resize(self, new_size):
        shape = list(self.x.shape)
        shape[0] = new_size
        self.x.resize(shape)
        self.v.resize(shape)
        for particle_prop in self.particle_properties:
            shape = [self.particle_properties[particle_prop].shape]
            shape[0] = new_size
            self.particle_properties[particle_prop].resize(shape)



class Source(object):
    """A particle source."""

    def __init__(self):
        pass

    def num_ptcls_produced(self, dt):
        """The number of particles that will be produced.

        This gives the number of particles that will be generated by the next
        call to produce_ptcls. It is legal for a source to return different
        numbers of particles on consecutive calls to num_ptcls_produced. This
        is often the case for stochastic sources that produce a certain number
        of particles on average.

        dt -- The duration of the time interval for which to produce particles.
        """
        return 0

    def produce_ptcls(self, dt, start, end, ensemble):
        """Generate particles.

        The number of particles generated must match the result return by a
        call to num_ptcls_produced(). We can expect end - start ==
        num_ptcls_produced().

        dt -- The duration of the time interval for which to produce particles.
        To make start and end and dt consistent with one another this dt should
        be the same as the dt passed to num_ptcls_produced to obtain start and
        end.
        start -- First position in ensemble where particles will be inserted.
        end -- One past the last position in the ensemble where particles will
        be inserted.
        ensemble -- The ensemble into which to insert the particles."""
        pass


def produce_ptcls(dt, ensemble, sources=[]):
    """Insert particles produced by sources into the ensemble.

    dt -- Length of time interval for which to produce particles.
    ensemble -- The ensemble into which to insert the particles.
    sources -- The particle source. Should derive from Source.
    """

    num_new_ptcls = []
    tot_new_ptcls = 0
    for s in sources:
        num_new_ptcls.append(s.num_ptcls_produced(dt))
        tot_new_ptcls += num_new_ptcls[-1]

    start = ensemble.num_ptcls
    ensemble.resize(ensemble.num_ptcls + tot_new_ptcls)
    for i, s in enumerate(sources):
        s.produce_ptcls(dt, start, start + num_new_ptcls[i], ensemble)
        start += num_new_ptcls[i]


class Sink(object):
    """A particle sink.

    Conceptually, sinks are represented by surfaces that remove particles from
    an ensemble if they hit the surface."""

    def find_absorption_time(self, x, v, dt):
        """The time at which particles will be arbsorbed by the sink.

        This method returns the time interval after which particles starting at
        x and traveling with velocity vector v along a straight line will hit
        the sink surface. dt is the duration of the interval in which an
        absorption time is sought. If the particle will not hit the sink in
        interval dt the function should return an absorption time greater than
        dt.

        x -- Initial particle positions.
        v -- Particle velocities.
        dt -- Length of time interval.
        """
        return np.full(x.shape[0], 2.0 * dt)

    def absorb_particle(self, x, v, dt):
        """This function gets called when this sink absorbs a particle."""
        pass


class SinkPlane(Sink):

    def __init__(self, point, normal):
        """Generate a sink that absorbs particles hitting a plane.

        point -- A point in the plane.
        normal -- A normal to the plane.
        """
        self.point = point
        self.normal = normal

    def find_absorption_time(self, x, v, dt):
        taus = np.zeros(x.shape[0])

        for i in range(x.shape[0]):
            normal_velocity = self.normal.dot(v[i])
            if (normal_velocity == 0.0):
                taus[i] = 2.0 * dt
            else:
                taus[i] = self.normal.dot(self.point - x[i]) / normal_velocity

        return taus


def drift_kick(dt, ensemble, forces=[]):
    """Drift-Kick-Drift push of particles."""
    if len(forces) == 0:
        ensemble.x += dt * ensemble.v
    else:
        ensemble.x += 0.5 * dt * ensemble.v

        f = np.zeros_like(ensemble.v)
        for force in forces:
            f += force(ensemble)

        m = 0.0
        if 'mass' in ensemble.ensemble_properties:
            m = ensemble.ensemble_properties['mass']
        elif 'mass' in ensemble.particle_properties:
            m = ensemble.particle_properties['mass']
        else:
            raise RuntimeError('To accelerate particles we need a mass ensemble or particle property')
        ensemble.v += (dt / m) * f
        ensemble.x += 0.5 * dt * ensemble.v

