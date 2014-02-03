''' 
Copyright (C) 2011-2014 German Aerospace Center DLR
(Deutsches Zentrum fuer Luft- und Raumfahrt e.V.), 
Institute of System Dynamics and Control
All rights reserved.

This file is part of PySimulator.

PySimulator is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

PySimulator is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with PySimulator. If not, see www.gnu.org/licenses.
'''

'''
Created on 09.04.2012

@author: otter
'''

import matplotlib.pyplot as plt
import numpy
from Plugins.Algorithms.Control import Misc
from Plugins.Algorithms.Control import lti


def plotBode(lti, n=200, f_range=None, f_logspace=True, u_indices=None, y_indices=None):
    """
    Bode plot of LTI object using matplotlib

    Input arguments:
       n        : Number of result intervals (default = 200)
                  The result will have n+1 frequency points per transfer function
       f_range  : Frequency range as tuple (f_min, f_max) in [Hz]
                  If f_range=None, the range is automatically selected (default).
                  Otherwise, the provided range is used.
       f_logspace: = True , if frequency values are logarithmically spaced (default)
                   = False, if frequency values are linearly spaced
        u_indices: If none, the frequency response is computed from all inputs.
                   Otherwise, u_indices are the indices of the inputs for which
                   the frequency response shall be computed. For example indices_u=(0,3,4)
                   means to compute the frequency responses from u[0], u[3], u[4] to the select outputs.
        y_indices: If none, the frequency response is computed to all outputs.
                   Otherwise, y_indices are the indices of the outputs for which
                   the frequency response shall be computed. For example indices_y=(0,3,4)
                   means to compute the frequency responses from selected inputs to
                   the outputs y[0], y[3], y[4].
    """
    # Normalize indices
    (ui,yi) = Misc.normalizeIndices(lti.nu, lti.ny, u_indices=u_indices, y_indices=y_indices)

    # Compute frequency response
    (f,Y) = lti.frequencyResponse(n=n, f_range=f_range, f_logspace=f_logspace, u_indices=ui, y_indices=yi)

    # Get labels
    (u_names, u_units, y_names, y_units) = lti.getLabels(u_indices=ui, y_indices=yi)

    # Bode plot of every ui->yi path
    plt.figure()
    nu = len(ui)
    ny = len(yi)
    k = 0
    for (ii,i) in enumerate(yi):
        for (jj,j) in enumerate(ui):
            # Compute amplitude and phase
            y     = Y[i][j]
            y_A   = numpy.abs(y)
            y_phi = Misc.to_deg( Misc.continuousAngle(y) )

            # Plot Amplitude
            k = k+1
            plt.subplot(2*ny,nu,k)
            if f_logspace:
                plt.loglog(f, y_A)
            else:
                plt.plot(f, y_A)
            plt.grid(True, which="both")

            if jj == 0:
                if y_units == None:
                    plt.ylabel("|" + y_names[i] + "|")
                else:
                    plt.ylabel("|" + y_names[i] + "|" + " [" + y_units[i] + "]")

            if ii == 0:
                if u_units == None:
                    plt.title("from " + u_names[j])
                else:
                    plt.title("from " + u_names[j] + " [" + u_units[j] + "]")

        for (jj,j) in enumerate(ui):
            # Plot phase
            k = k + 1
            plt.subplot(2*ny,nu,k)
            if f_logspace:
                plt.semilogx(f, y_phi)
            else:
                plt.plot(f, y_A)
            plt.grid(True, which="both")
            if ii == ny-1: plt.xlabel("frequency [Hz]")
            if jj ==    0: plt.ylabel("phase(" + y_names[i] + ") [deg]")
    plt.show()


def plotBode2(zpk, n=200, f_range=None, f_logspace=True):
    """
    Bode plot of ZerosAndPoles object using matplotlib
    """
    (f,y) = zpk.frequencyResponse(n=n, f_range=f_range, f_logspace=f_logspace)

    y_A   = numpy.abs(y)
    y_phi = Misc.to_deg( Misc.continuousAngle(y) )

    plt.figure()
    plt.subplot(211)
    if f_logspace:
        plt.loglog(f, y_A)
    else:
        plt.plot(f, y_A)
    plt.grid(True, which="both")
    plt.ylabel("Amplitude")

    plt.subplot(212)
    if f_logspace:
        plt.semilogx(f, y_phi)
    else:
        plt.plot(f, y_A)
    plt.grid(True, which="both")
    plt.xlabel("Frequency [Hz]")
    plt.ylabel("Phase [deg]")

    plt.show()


if __name__ == "__main__":
    
    # lti1 = lti.LTI(zpk=[[(2**4, [], [-2,-2,-2,-2])]])
    # print("lti1 = " + str(lti1))
    # plotBode(lti1)

    lti2 = lti.LTI( ss=([[1,2,3],[4,5,6],[7,8,9]],
                     [[11,12],[21,22],[31,32]],
                     [[11,12,13],[21,22,23]],
                    ),
                 info = "Linearized system of a drive train",
                 info_u = (["u1", "u2"], ["N", "Nm"] , ["Force acting on flange_a", "Torque acting on flange_b"]),
                 info_y = (["y1", "y2"], ["m", "rad"], ["Position of mass", "Angle of inertia"]),
                 info_x = (["x1", "x2", "x3"], ["V", "A", "W"], ["Voltage of source", "Current of source", "Active power"])
              )
    plotBode(lti2)
