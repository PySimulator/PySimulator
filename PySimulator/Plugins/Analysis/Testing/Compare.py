#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Copyright (C) 2011-2015 German Aerospace Center DLR
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

import numpy



def normDiff(tAIn, fAIn, iA, sA, tBIn, fBIn, iB, sB, t1, t2):
    '''
    tAIn: numpy vector
    fAIn: numpy array (number of rows is equal to that of tAIn)
    iA:   numpy vector
    sA:   numpy vector (length is equal to length of iA)
    tBIn: numpy vector
    fBIn: numpy array (number of rows is equal to that of tBIn)
    iB:   numpy vector
    sB:   numpy vector (length is equal to length of iB)
    t1,t2: start and stop time for the integral norm
    '''

    error = False


    # nSignals = fAIn.shape[1]
    nSignals = len(iA)    
    NfAB = numpy.zeros((nSignals,))
    NfA = numpy.zeros((nSignals,))
    NfB = numpy.zeros((nSignals,))
    AfA = numpy.zeros((nSignals,))
    AfB = numpy.zeros((nSignals,))
    AfAB = numpy.zeros((nSignals,))

    if len(iB) <> nSignals:
        print "Number of indexes iA, iB must be equal."
        error = True        
    
    if error:
        return NfAB, NfA, NfB, True


    dt = abs(t1) + abs(t2) + 1

    # Add first and last point for possibly necessary extrapolations
    tA = numpy.hstack((min(tAIn[0] - dt, t1), tAIn, max(tAIn[-1] + dt, t2)))
    tB = numpy.hstack((min(tBIn[0] - dt, t1), tBIn, max(tBIn[-1] + dt, t2)))


    # Default values (for constant extrapolation)
    fA = numpy.vstack((fAIn[0, :], fAIn, fAIn[-1, :]))
    fB = numpy.vstack((fBIn[0, :], fBIn, fBIn[-1, :]))


    # Linear extrapolation where necessary
    if t1 < tA[1]:
        if tA[1] == tA[2]:
            '''
            for i in xrange(nSignals):
                if fA[1, iA[i]] <> fA[2, iA[i]]:
                    #print "Extrapolation for fA on left border of time grid not possible due to discontinuity in column " + str(iA[i]) + " for index " + str(i)
                    #error = True
                    #break
                    fA[0, iA[i]] = fA[1, iA[i]]
                else:
                    fA[0, iA[i]] = fA[1, iA[i]]
            '''
            fA[0, iA] = fA[1, iA]
        else:
            fA[0, iA] = fA[1, iA] + (fA[2, iA] - fA[1, iA]) * (tA[0] - tA[1]) / (tA[2] - tA[1])
    if t1 < tB[1]:
        if tB[1] == tB[2]:
            '''
            for i in xrange(nSignals):
                if fB[1, iB[i]] <> fB[2, iB[i]]:
                    #print "Extrapolation for fB on left border of time grid not possible due to discontinuity in column " + str(iB[i]) + " for index " + str(i)
                    #error = True
                    #break
                    fB[0, iB[i]] = fB[1, iB[i]]
                else:
                    fB[0, iB[i]] = fB[1, iB[i]]
            '''
            fB[0, iB] = fB[1, iB]
        else:
            fB[0, iB] = fB[1, iB] + (fB[2, iB] - fB[1, iB]) * (tB[0] - tB[1]) / (tB[2] - tB[1])
    if t2 > tA[-2]:
        if tA[-2] == tA[-3]:
            '''
            for i in xrange(nSignals):
                if fA[-2, iA[i]] <> fA[-3, iA[i]]:
                    #print "Extrapolation for fA on right border of time grid not possible due to discontinuity in column " + str(iA[i]) + " for index " + str(i)
                    #error = True
                    #break
                    fA[-1, iA[i]] = fA[-2, iA[i]]
                else:
                    fA[-1, iA[i]] = fA[-3, iA[i]]
            '''
            fA[-1, iA] = fA[-2, iA]
        else:
            fA[-1, iA] = fA[-3, iA] + (fA[-2, iA] - fA[-3, iA]) * (tA[-1] - tA[-3]) / (tA[-2] - tA[-3])
    if t2 > tB[-2]:
        if tB[-2] == tB[-3]:
            '''
            for i in xrange(nSignals):
                if fB[-2, iB[i]] <> fB[-3, iB[i]]:
                    #print "Extrapolation for fB on right border of time grid not possible due to discontinuity in column " + str(iB[i]) + " for index " + str(i)
                    #error = True
                    #break
                    fB[-1, iB[i]] = fB[-2, iB[i]]
                else:
                    fB[-1, iB[i]] = fB[-3, iB[i]]
            '''
            fB[-1, iB] = fB[-2, iB]
        else:
            fB[-1, iB] = fB[-3, iB] + (fB[-2, iB] - fB[-3, iB]) * (tB[-1] - tB[-3]) / (tB[-2] - tB[-3])

   
    if error:
        return NfAB, NfA, NfB, True


    '''
    Now begin computing the integrals
    '''

    s2 = t1
    s1 = t1
    kf = 0
    kg = 0
    initial = True


    # Loop over the time intervals
    while s2 < t2:
        if s1 == tA[kf + 1] or initial:
            while tA[kf + 1] <= s1:
                kf += 1
        if s1 == tB[kg + 1] or initial:
            while tB[kg + 1] <= s1:
                kg += 1

        s1 = s2
        s2 = min(tA[kf + 1], tB[kg + 1], t2)

        FA1 = sA * (fA[kf, iA] + (fA[kf + 1, iA] - fA[kf, iA]) * ((s1 - tA[kf]) / (tA[kf + 1] - tA[kf])))
        FA2 = sA * (fA[kf, iA] + (fA[kf + 1, iA] - fA[kf, iA]) * ((s2 - tA[kf]) / (tA[kf + 1] - tA[kf])))
        r1 = FA1 >= 0  # sgn(FA1)
        r2 = FA2 >= 0  # sgn(FA2)
        iRe = r1 == r2
        iRi = numpy.logical_not(iRe)
        AfA[iRe] = (2 * r1[iRe] - 1) * 0.5 * (FA1[iRe] + FA2[iRe]) * (s2 - s1)
        tm = s1 - FA1[iRi] * (s2 - s1) / (FA2[iRi] - FA1[iRi])
        AfA[iRi] = (2 * r1[iRi] - 1) * 0.5 * (FA1[iRi] * (tm - s1) + FA2[iRi] * (tm - s2))
        '''
        if any(AfA) < 0:
            print "Internal error: AfA < 0; AfA = " + str(AfA)
            error = True
            return
        '''

        FB1 = sB * (fB[kg, iB] + (fB[kg + 1, iB] - fB[kg, iB]) * ((s1 - tB[kg]) / (tB[kg + 1] - tB[kg])))
        FB2 = sB * (fB[kg, iB] + (fB[kg + 1, iB] - fB[kg, iB]) * ((s2 - tB[kg]) / (tB[kg + 1] - tB[kg])))
        r1 = FB1 >= 0  # sgn(FB1)
        r2 = FB2 >= 0  # sgn(FB2)
        iRe = r1 == r2
        iRi = numpy.logical_not(iRe)
        AfB[iRe] = (2 * r1[iRe] - 1) * 0.5 * (FB1[iRe] + FB2[iRe]) * (s2 - s1)
        tm = s1 - FB1[iRi] * (s2 - s1) / (FB2[iRi] - FB1[iRi])
        AfB[iRi] = (2 * r1[iRi] - 1) * 0.5 * (FB1[iRi] * (tm - s1) + FB2[iRi] * (tm - s2))
        '''
        if any(AfB) < 0:
            print "Internal error: AfB < 0; AfB = " + str(AfB)
            error = True
            return
        '''

        FAB1 = FA1 - FB1
        FAB2 = FA2 - FB2
        r1 = FAB1 >= 0  # sgn(FAB1)
        r2 = FAB2 >= 0  # sgn(FAB2)
        iRe = r1 == r2
        iRi = numpy.logical_not(iRe)
        AfAB[iRe] = (2 * r1[iRe] - 1) * 0.5 * (FAB1[iRe] + FAB2[iRe]) * (s2 - s1)
        tm = s1 - FAB1[iRi] * (s2 - s1) / (FAB2[iRi] - FAB1[iRi])
        AfAB[iRi] = (2 * r1[iRi] - 1) * 0.5 * (FAB1[iRi] * (tm - s1) + FAB2[iRi] * (tm - s2))
        '''
        if any(AfAB) < 0:
            print "Internal error: AfAB < 0; AfAB = " + str(AfAB)
            error = True
            return
        '''

        initial = False

        NfAB += AfAB
        NfA += AfA
        NfB += AfB

    return NfAB / (t2 - t1), NfA / (t2 - t1), NfB / (t2 - t1), error


def normDiffPar(fA, fB):
    '''
        fA, fB, numpy vectors
    '''

    if len(fA) <> len(fB):
        return None, None, None, True

    return abs(fA - fB), abs(fA), abs(fB), False




def Compare(tA, fA, iA, sA, tB, fB, iB, sB, tol=1e-3):

    tA2 = tA
    fA2 = fA
    tB2 = tB
    fB2 = fB

    if tA is None and tB is None:
        diff, NfA, NfB, error = normDiffPar(sA * fA2[0, iA], sB * fB2[0, iB])
    else:
        if tA is None or tB is None:
            if tA is None:
                tA2 = [0]
                tStart = tB[0]
                tStop = tB[-1]
            if tB is None:
                tB2 = [0]
                tStart = tA[0]
                tStop = tA[-1]
        else:
            tStart = min(tA[0], tB[0])
            tStop = max(tA[-1], tB[-1])
        
        if tStart == tStop:
            diff, NfA, NfB, error = normDiffPar(sA * fA2[0, iA], sB * fB2[0, iB])
        else:
            diff, NfA, NfB, error = normDiff(tA2, fA2, iA, sA, tB2, fB2, iB, sB, tStart, tStop)

    if error:
        return [False]*len(diff), diff / (1 + NfA + NfB), error
    else:
        return diff <= tol * (1 + NfA + NfB), diff / (1 + NfA + NfB), error


if __name__ == "__main__":

    t1 = numpy.arange(19)
    t2 = numpy.arange(10) * 2

    f1 = numpy.arange(19) * 3.65
    f2 = numpy.arange(10) * 2 * 3.65

    f3 = numpy.arange(19) * 5.9
    f4 = numpy.arange(10) * 2.001 * 5.9

    F1 = numpy.hstack((numpy.reshape(f1, (len(f1), 1)), numpy.reshape(f3, (len(f3), 1))))
    F2 = numpy.hstack((numpy.reshape(f2, (len(f2), 1)), numpy.reshape(f4, (len(f4), 1))))

    print Compare(t1, F1, t2, F2, 0, 18.002, 1e-3)



