from vectors import Point
import math
from ROOT import TVector2, TVector3
from scipy import constants

class Helix(object):
    def __init__(self, field, charge, p4, origin):
        self.charge = charge
        self.p4 = p4
        self.udir = p4.Vect().Unit()
        self.origin = origin
        self.rho = p4.Perp() / (abs(charge)*field) * 1e9/constants.c
        self.v_over_omega = p4.Vect()
        self.v_over_omega *= 1./(abs(charge)*field)*1e9/constants.c
        self.omega = charge*field*constants.c**2 / (p4.M()*p4.Gamma()*1e9)
        # self.omega = charge*field*constants.c / (p4.M()*p4.Gamma())
        momperp_xy = TVector3(-p4.Y(), p4.X(), 0.).Unit()
        origin_xy = TVector3(origin.X(), origin.Y(), 0.)
        self.center_xy = origin_xy - charge * momperp_xy * self.rho
        self.extreme_point_xy = TVector3(self.rho, 0, 0) 
        if self.center_xy.X()!=0 or self.center_xy.Y()!=0:
            self.extreme_point_xy = self.center_xy + self.center_xy.Unit() * self.rho
        # calculate phi range with the origin at the center,
        # for display purposes
        center_to_origin = origin_xy - self.center_xy
        self.phi0 = center_to_origin.Phi()
        self.phi_min = self.phi0 * 180 / math.pi
        self.phi_max = self.phi_min + 360.

    def point_at_time(self, time):
        z = constants.c * self.udir.Z() * time + self.origin.Z()
        x = self.origin.X() + self.v_over_omega.Y() * (1-math.cos(self.omega*time)) \
            + self.v_over_omega.X() * math.sin(self.omega*time)
        y = self.origin.Y() - self.v_over_omega.X() * (1-math.cos(self.omega*time)) \
            + self.v_over_omega.Y() * math.sin(self.omega*time)
        # if time == 1e-8:
        #    import pdb; pdb.set_trace()
        return TVector3(x, y, z)

    def time_at_z(self, z):
        dest_time = (z - self.origin.Z())/(self.udir.Z()*constants.c)
        return dest_time
        
class Info(object):
    pass

class Propagator(object):

    def propagate(self, particles, cylinders):
        for ptc in particles:
            for cyl in cylinders:
                self.propagate_one(ptc, cyl)
                
                
class StraightLinePropagator(Propagator):        

    def propagate_one(self, particle, cylinder):
        udir = particle.p4.Vect().Unit()
        theta = udir.Theta()
        origin = particle.vertex
        if udir.Z():
            destz = cylinder.z if udir.Z() > 0. else -cylinder.z
            length = (destz - origin.Z())/math.cos(theta)
            assert(length>=0)
            destination = origin + udir * length
            rdest = destination.Perp()
            if rdest > cylinder.rad:
                udirxy = TVector3(udir.X(), udir.Y(), 0.)
                originxy = TVector3(origin.X(), origin.Y(), 0.)
                # solve 2nd degree equation for intersection
                # between the straight line and the cylinder
                # in the xy plane to get k,
                # the propagation length
                a = udirxy.Mag2()
                b= 2*udirxy.Dot(originxy)
                c= originxy.Mag2()-cylinder.rad**2
                delta = b**2 - 4*a*c
                km = (-b - math.sqrt(delta))/(2*a)
                # positive propagation -> correct solution.
                kp = (-b + math.sqrt(delta))/(2*a)
                # print delta, km, kp
                destination = origin + udir * kp  
        #TODO deal with Z == 0 
        #TODO deal with overlapping cylinders
        particle.points[cylinder.name] = destination

        
class HelixPropagator(Propagator):
    
    def propagate_one(self, particle, cylinder, debug_info=None):
        field = 4. 
        helix = Helix(field, particle.charge, particle.p4,
                      particle.vertex)
        particle.set_helix(helix)
        is_looper = helix.extreme_point_xy.Mag() < cylinder.rad
        is_positive = particle.p4.Z() > 0.
        if is_looper:
            # extrapolating to endcap
            destz = cylinder.z if helix.udir.Z() > 0. else -cylinder.z
            dest_time = helix.time_at_z(destz)
            destination = helix.point_at_time(dest_time)
            # destz = cylinder.z if positive else -cylinder.z
            particle.points[cylinder.name] = destination
        info = Info()
        info.is_positive = is_positive
        info.is_looper = is_looper
        return info
        
straight_line = StraightLinePropagator()

helix = HelixPropagator() 
