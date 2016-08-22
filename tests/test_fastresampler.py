#!/usr/bin/env python
from tide_funcs import fastresampler
import numpy as np
import pylab as plt

def mse(vec1, vec2):
    return np.mean(np.square(vec2 - vec1))


def testfastresampler(debug=False):
    tr = 1.0
    padvalue = 30.0
    testlen = 1000
    shiftdist = 30
    timeaxis = np.arange(0.0, 1.0 * testlen) * tr
    #timecoursein = np.zeros((testlen), dtype='float')
    timecoursein = timeaxis * 0.0
    midpoint = int(testlen // 2) + 1
    timecoursein[midpoint] = 1.0
    timecoursein -= 0.5

    shiftlist = [-30, -20, -10, 0, 10, 20, 30]

    # generate the fast resampled regressor
    genlaggedtc = fastresampler(timeaxis, timecoursein, padvalue=padvalue)

    if debug:
        plt.figure()
        plt.ylim([-1.0, 2.0 * len(shiftlist) + 1.0])
        plt.hold(True)
        plt.plot(timecoursein)
        legend = ['Original']
        offset = 0.0

    for shiftdist in shiftlist:
        # generate the ground truth rolled regressor
        tcrolled = np.roll(timecoursein, shiftdist)

        # generate the fast resampled regressor
        tcshifted = genlaggedtc.yfromx(timeaxis - shiftdist, debug=debug)

        # plot if we are doing that
        if debug:
            offset += 1.0
            plt.plot(tcrolled + offset)
            legend.append('Roll ' + str(shiftdist))
            offset += 1.0
            plt.plot(tcshifted + offset)
            legend.append('Fastresampler ' + str(shiftdist))

        # do the tests
        assert mse(tcrolled, tcshifted) < 1e-10
        np.testing.assert_almost_equal(tcrolled, tcshifted, 6)

    if debug:
        plt.legend(legend)
        plt.show()
    
def main():
    testfastresampler(debug=True)

if __name__ == '__main__':
    main()
