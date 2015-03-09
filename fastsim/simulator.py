from heppy_fcc.fastsim.propagator import StraightLinePropagator, HelixPropagator 
from heppy_fcc.fastsim.pfobjects import Cluster, SmearedCluster
import random

class Simulator(object):

    def __init__(self, detector):
        self.detector = detector
        self.prop_helix = HelixPropagator()
        self.prop_straight = StraightLinePropagator()
        
    def reset(self):
        self.particles = None
        Cluster.max_energy = 0.

    def propagator(self, ptc):
        is_neutral = abs(ptc.charge)<0.5
        return self.prop_straight if is_neutral else self.prop_helix
        
    def propagate(self, ptc):
        '''propagate the particle to all dector cylinders'''
        self.propagator(ptc).propagate([ptc], self.detector.cylinders(),
                                       self.detector.elements['field'].magnitude)

    def make_cluster(self, ptc, detname, fraction=1., size=None):
        '''adds a cluster in a given detector, with a given fraction of 
        the particle energy.'''
        detector = self.detector.elements[detname]
        self.propagator(ptc).propagate_one(ptc,
                                           detector.volume.inner,
                                           self.detector.elements['field'].magnitude )
        if size is None:
            size = detector.cluster_size(ptc)
        cylname = detector.volume.inner.name
        cluster =  Cluster(ptc.p4.E()*fraction,
                           ptc.points[cylname],
                           size,
                           cylname, ptc)
        ptc.clusters[cylname] = cluster
        return cluster
         
<<<<<<< HEAD
=======
    # def smear_cluster(self, cluster, detector):
    #     '''detector is only used to get the resolution and acceptance.
    #     returns a smeared cluster that is basically a copy of cluster, 
    #     with smeared position and energy. 
    #     if the smeared cluster does not pass the acceptance cuts, 
    #     returns None.
    #     '''
    #     eres = detector.energy_resolution(cluster)
    #     energy = cluster.energy * random.gauss(1, eres)
    #     smeared_cluster = SmearedCluster( cluster,
    #                                       energy,
    #                                       cluster.position,
    #                                       cluster.size,
    #                                       cluster.layer,
    #                                       cluster.particle )
    #     smeared_cluster.set_energy(energy)
    #     return smeared_cluster
        #TODO make the interface look like make_cluster?
        
>>>>>>> origin/master
    def simulate_photon(self, ptc):
        detname = 'ecal'
        ecal = self.detector.elements[detname]
        self.prop_straight.propagate_one(ptc,
                                         ecal.volume.inner)
        
        cluster = self.make_cluster(ptc, detname)
        smeared = cluster.smear(ecal)
<<<<<<< HEAD
        if smeared: 
            ptc.clusters_smeared[smeared.layer] = smeared
=======
        ptc.clusters_smeared[smeared.layer] = smeared
>>>>>>> origin/master


    def simulate_electron(self, ptc):
        ecal = self.detector.elements['ecal']
        self.prop_helix.propagate_one(ptc,
                                      ecal.volume.inner,
                                      self.detector.elements['field'].magnitude )
<<<<<<< HEAD
        cluster = self.make_cluster(ptc, 'ecal')
        smeared_cluster = cluster.smear(ecal)
        if smeared_cluster: 
            ptc.clusters_smeared[smeared_cluster.layer] = smeared_cluster
        smeared_track = ptc.track.smear(self.detector.elements['tracker'])
        if smeared_track:
            ptc.track_smeared = smeared_track
=======
        self.make_cluster(ptc, 'ecal')
        smeared = cluster.smear(ecal)
        ptc.clusters_smeared[smeared.layer] = smeared
>>>>>>> origin/master


    def simulate_neutrino(self, ptc):
        self.propagate(ptc)
        
    def simulate_hadron(self, ptc):
        ecal = self.detector.elements['ecal']
        hcal = self.detector.elements['hcal']        
        path_length = ecal.material.path_length(ptc)
        self.propagator(ptc).propagate_one(ptc,
                                           ecal.volume.inner,
                                           self.detector.elements['field'].magnitude)
        time_ecal_inner = ptc.path.time_at_z(ptc.points['ecal_in'].Z())
        deltat = ptc.path.deltat(path_length)
        time_decay = time_ecal_inner + deltat
        point_decay = ptc.path.point_at_time(time_decay)
        ptc.points['ecal_decay'] = point_decay
        frac_ecal = 0.
        if ecal.volume.contains(point_decay):
            frac_ecal = random.uniform(0., 0.7)
            cluster = self.make_cluster(ptc, 'ecal', frac_ecal)
            # For now, using the hcal resolution and acceptance
            # for hadronic cluster
            # in the ECAL. That's not a bug! 
            smeared = cluster.smear(hcal)
            if smeared:
                ptc.clusters_smeared[smeared.layer] = smeared
        cluster = self.make_cluster(ptc, 'hcal', 1-frac_ecal)
        smeared = cluster.smear(hcal)
        if smeared:
            ptc.clusters_smeared[smeared.layer] = smeared
        smeared_track = ptc.track.smear(self.detector.elements['tracker'])
        if smeared_track:
            ptc.track_smeared = smeared_track

    def simulate_muon(self, ptc):
        self.propagate(ptc)
        smeared_track = ptc.track.smear(self.detector.elements['tracker'])
        if smeared_track:
            ptc.track_smeared = smeared_track
            
    def simulate(self, ptcs):
        self.reset()
        self.ptcs = ptcs
        for ptc in ptcs:
            if ptc.pdgid == 22:
                self.simulate_photon(ptc)
            elif abs(ptc.pdgid) == 11:
                self.simulate_electron(ptc)
            elif abs(ptc.pdgid) == 13:
                self.simulate_muon(ptc)
            elif abs(ptc.pdgid) in [12,14,16]:
                self.simulate_neutrino(ptc)
            elif abs(ptc.pdgid) > 100: #TODO make sure this is ok
                self.simulate_hadron(ptc)
            
                
if __name__ == '__main__':

    import math
    from heppy_fcc.fastsim.vectors import Point
    from heppy_fcc.fastsim.detectors.CMS import CMS
    from heppy_fcc.fastsim.toyevents import particles
    from heppy_fcc.display.core import Display
    from heppy_fcc.display.geometry import GDetector
    from heppy_fcc.display.pfobjects import GTrajectories

    cms = CMS()
    simulator = Simulator(cms)
    particles = list(particles(1, 11, 1, 2,
                               5., 5.) )
    simulator.simulate(particles)

    display = Display(['xy', 'ECAL_thetaphi', 'HCAL_thetaphi'])
    gcms = GDetector(cms)
    display.register(gcms, 0)
    gtrajectories = GTrajectories(particles)
    display.register(gtrajectories,1)
    display.draw()
