__author__ = 'hwb'
from mpmath import ellipk, j, taufrom, jtheta, qfrom, ellipf, asin, mfrom
from numpy import roots, complex64, conj, pi, sqrt, sum
import mpmath
import time
import matrices
import os
from laplace import five_point_laplace
import math



def quartic_roots(k, x1, x2, x3):
    K = complex64(ellipk(k**2))

    e0 = complex64((x1*j - x2)**2 + .25 * K**2)
    e1 = complex64(4*(x1*j-x2)*x3)
    e2 = complex64(4*(x3**2) - 2 * (x1**2) - 2 * (x2**2) + (K**2) * (k**2 - 0.5))
    e3 = complex64(4*x3*(x2 + j*x1))
    e4 = complex64(x2**2 - x1**2 + 2*j*x1*x2 + 0.25*K**2)

    return roots([e4, e3, e2, e1, e0])


def order_roots(roots):
    if len(roots) != 4:
        raise ValueError

    if abs( roots[0]+1/conj(roots[1]) ) <10**(-4):
        return [roots[0], roots[2], roots[1], roots[3]]
    elif abs(roots[0]+1/conj(roots[2])) <10**(-4):
        return [roots[0],roots[1],roots[2],roots[3]]
    elif abs(roots[0]+1/conj(roots[3])) <10**(-4):
        return[roots[0],roots[1],roots[3],roots[2]]
    raise ValueError

def calc_zeta(k, x1, x2, x3):
    return order_roots(quartic_roots(k, x1, x2, x3))

def calc_eta(k, x1, x2, x3):
    zeta = calc_zeta(k, x1, x2, x3)
    return map(lambda zetai : -(x2 + j*x1) * zetai**2 - 2*x3 * zetai + x2 - j*x1, zeta)

def calc_abel(k, zeta, eta):
    k1 = sqrt(1-k**2)

    a=k1+complex(0, 1)*k

    b=k1-complex(0, 1)*k

    abel_tmp = map(lambda zetai : \
                       complex(0, 1) * 1/(complex64(ellipk(k**2))*2*b) \
                                     * complex64(ellipf( asin( (zetai )/a), mfrom(k=a/b))) \
                       - taufrom(k=k)/2,
               zeta)

    abel = []
    for i in range(0, 4, 1):
        abel.append(abel_select(k, abel_tmp[i], eta[i]))

    return abel

def abel_select(k, abeli, etai):
    tol = 0.001

    if (abs(complex64(calc_eta_by_theta(k, abeli)) - etai) > tol):
        return - abeli - 0.5 * (1 + taufrom(k=k))
    else :
        return abeli


def calc_eta_by_theta(k, z):
    return 0.25 * complex(0, 1) * pi * ((jtheta(2, 0,  qfrom(k=k), 0)) ** 2) \
        * ((jtheta(4, 0,  qfrom(k=k), 0)) ** 2) \
        * (jtheta(3, 0,  qfrom(k=k), 0)) \
        * (jtheta(3, 2*z*pi,  qfrom(k=k), 0)) \
            / ( ((jtheta(1, z*pi,  qfrom(k=k), 0)) ** 2) * ((jtheta(3, z*pi,  qfrom(k=k), 0)) ** 2) )

def calc_mu(k, x1, x2, x3, zeta, abel):
    mu = []
    for i in range(0, 4, 1):
        mu.append(complex(
               0.25 *pi* ((jtheta(1, abel[i]*pi,  qfrom(k=k), 1) / (jtheta(1, abel[i]*pi,  qfrom(k=k), 0)) )
                    + (jtheta(3, abel[i]*pi,  qfrom(k=k), 1) / (jtheta(3, abel[i]*pi,  qfrom(k=k), 0)) )) \
            - x3 - (x2 + complex(0,1) *x1) * zeta[i]))
    return mu


def calc_phi_squared(k, x1, x2, x3):
    # t0= time.time()
    zeta = calc_zeta(k ,x1, x2, x3)
    # t1 = time.time()
    # print "zeta: " + str(t1-t0)
    eta = calc_eta(k, x1, x2, x3)
    # t2 = time.time()
    # print "eta: " + str(t2-t1)
    abel = calc_abel(k, zeta, eta)
    # t3 = time.time()
    # print "abel: " + str(t3-t2)
    mu = calc_mu(k, x1, x2, x3, zeta, abel)
    # t4 = time.time()
    # print "mu: " + str(t4-t3)

    result =  matrices.HIGGSTRACE(map(lambda z:complex(z), zeta), mu, [x1, x2, x3], k)
    # t5 = time.time()
    # print "Higgs: " + str(t5-t4)
    # print "Total: " + str(t5-t0)
    return result.real



def energy_density(k, x1, x2, x3):
    step_size = 0.02

    points = []
    for a in range(-2, 3, 1):
        points_y = []
        for b in range(-2, 3, 1):
            points_z = []
            for c in range(-2, 3, 1):
                points_z.append(calc_phi_squared(k, float(x1 + a * step_size), float(x2 + b * step_size), float(x3 + c * step_size)))
            points_y.append(points_z)
        points.append(points_y)

    return five_point_laplace(points, step_size)

# print energy_density(0.8, 1, 1, 1)

def energy_density_on_line(k, x0, y0, z0, axis, end):
    if (axis not in ['x','y','z']):
        raise ValueError("Invalid axis given. Must be one of 'x', 'y', or 'z'")

    step_size = 0.02
    if (axis == 'x'):
        start = x0
    elif (axis == 'y'):
        start = y0
    elif (axis == 'z'):
        start = z0
    intervals = int(math.ceil((end - start)/step_size))


    points = []
    for a in range(0, intervals, 1):
        points_y = []
        for b in range(-2, 3, 1):
            points_z = []
            for c in range(-2, 3, 1):
                if(b == 0 or c == 0):
                    if (axis == 'x'):
                        points_z.append(calc_phi_squared(k, float(x0 + a * step_size), float(y0 + b * step_size), float(z0 + c * step_size)))
                    elif (axis == 'y'):
                        points_z.append(calc_phi_squared(k, float(x0 + b * step_size), float(y0 + a * step_size), float(z0 + c * step_size)))
                    elif (axis == 'z'):
                        points_z.append(calc_phi_squared(k, float(x0 + c * step_size), float(y0 + b * step_size), float(z0 + a * step_size)))
                else:
                    points_z.append(0) # Value is not used in laplace calculation
            points_y.append(points_z)
        points.append(points_y)

    return five_point_laplace(points, step_size)



# print energy_density_on_line(0.8, 0.5, 0, 0, 'x', 2.5)
# print energy_density_on_line(0.8, 0, 0.5, 0, 'y', 2.5)
# print energy_density_on_line(0.8, 0, 0, 0.5, 'z', 2.5)

print energy_density_on_line(0.8, 4, 0, 0, 'x', 5)