#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   Copyright 2016-2024 Blaise Frederick
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
#
import argparse
import sys

import numpy as np

import rapidtide.io as tide_io
import rapidtide.maskutil as tide_mask
import rapidtide.workflows.parser_funcs as pf


def summarize(thevoxels, method="mean"):
    theshape = thevoxels.shape
    if len(theshape) > 1:
        numtimepoints = theshape[1]
    else:
        numtimepoints = 1

    if method == "mean":
        themethod = np.mean
    elif method == "sum":
        themethod = np.sum
    elif method == "median":
        themethod = np.median
    else:
        print(f"illegal summary method {method} in summarize")
        sys.exit()

    if numtimepoints > 1:
        regionsummary = np.nan_to_num(themethod(thevoxels, axis=0))
    else:
        regionsummary = np.nan_to_num(themethod(thevoxels))
    return regionsummary


def _get_parser():
    # get the command line parameters
    parser = argparse.ArgumentParser(
        prog="atlasaverage",
        description="Average data within atlas regions.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "datafile",
        type=lambda x: pf.is_valid_file(parser, x),
        help="The name of the 3 or 4D nifti file with the data to be averaged over atlas regions.",
    )
    parser.add_argument(
        "templatefile",
        type=lambda x: pf.is_valid_file(parser, x),
        help="The name of the atlas region NIFTI file",
    )
    parser.add_argument("outputroot", help="The root name of the output files.")

    # add optional arguments
    parser.add_argument(
        "--normmethod",
        dest="normmethod",
        action="store",
        type=str,
        choices=["none", "pct", "var", "std", "p2p"],
        help=(
            "Normalization to apply to input timecourses (in addition to demeaning) prior to "
            "combining. Choices are 'none' (no normalization, default), 'pct' (divide by mean), "
            "'var' (unit variance), 'std' (unit standard deviation), and 'p2p' (unit range)."
        ),
        default="none",
    )
    parser.add_argument(
        "--summarymethod",
        dest="summarymethod",
        action="store",
        type=str,
        choices=["mean", "median", "sum"],
        help=("Method to summarize a region.  Choices are 'mean' (default), 'median', and 'sum'."),
        default="mean",
    )
    parser.add_argument(
        "--ignorezeros",
        dest="ignorezeros",
        action="store_true",
        help=("Zero value voxels will not be included in calculation of summary statistics."),
        default=False,
    )
    parser.add_argument(
        "--regionlistfile",
        type=lambda x: pf.is_valid_file(parser, x),
        help=(
            "The name of of a text file containing the integer region numbers to summarize, one per line.  "
            "Values that do not exist in the atlas will return NaNs."
        ),
        default=None,
    )
    parser.add_argument(
        "--includemask",
        dest="includespec",
        metavar="MASK[:VALSPEC]",
        help=(
            "Only use atlas voxels that are also in file MASK in calculating the region summaries "
            "(if VALSPEC is given, only voxels "
            "with integral values listed in VALSPEC are used). "
        ),
        default=None,
    )
    parser.add_argument(
        "--excludemask",
        dest="excludespec",
        metavar="MASK[:VALSPEC]",
        help=(
            "Do not use atlas voxels that are also in file MASK in calculating the region summaries "
            "(if VALSPEC is given, voxels "
            "with integral values listed in VALSPEC are excluded). "
        ),
        default=None,
    )
    parser.add_argument(
        "--extramask",
        dest="extramaskname",
        metavar="MASK",
        type=lambda x: pf.is_valid_file(parser, x),
        help=(
            "Additional mask to apply select voxels for region summaries. Zero voxels in this mask will be excluded."
        ),
        default=None,
    )
    parser.add_argument(
        "--headerline",
        dest="headerline",
        action="store_true",
        help="Add a header line to the text output summary of 3D files.",
        default=False,
    )
    parser.add_argument(
        "--datalabel",
        dest="datalabel",
        action="store",
        type=str,
        metavar="LABEL",
        help="Label to add to the beginning of the text summary line.",
        default=None,
    )
    parser.add_argument(
        "--debug",
        dest="debug",
        action="store_true",
        help="Output additional debugging information.",
        default=False,
    )

    return parser


def atlasaverage(args):
    if args.normmethod == "none":
        print("will not normalize timecourses")
    elif args.normmethod == "pct":
        print("will normalize timecourses to percentage of mean")
    elif args.normmethod == "std":
        print("will normalize timecourses to standard deviation of 1.0")
    elif args.normmethod == "var":
        print("will normalize timecourses to variance of 1.0")
    elif args.normmethod == "p2p":
        print("will normalize timecourses to p-p deviation of 1.0")

    print("loading fmri data")
    input_img, input_data, input_hdr, thedims, thesizes = tide_io.readfromnifti(args.datafile)
    if args.debug:
        print("loading template data")
    (
        template_img,
        template_data,
        template_hdr,
        templatedims,
        templatesizes,
    ) = tide_io.readfromnifti(args.templatefile)

    print("checking dimensions")
    if not tide_io.checkspacematch(input_hdr, template_hdr):
        print("template file does not match spatial coverage of input fmri file")
        sys.exit()

    print("reshaping")
    xsize = thedims[1]
    ysize = thedims[2]
    numslices = thedims[3]
    numtimepoints = thedims[4]
    numvoxels = int(xsize) * int(ysize) * int(numslices)

    templatevoxels = np.reshape(template_data, numvoxels).astype(int)
    inputvoxels = np.reshape(input_data, (numvoxels, numtimepoints))
    print("reshaped inputdata shape", inputvoxels.shape)

    # process masks
    if args.includespec is not None:
        (
            args.includename,
            args.includevals,
        ) = tide_io.processnamespec(
            args.includespec, "Including voxels where ", "in offset calculation."
        )
    else:
        args.includename = None
        args.includevals = None
    if args.excludespec is not None:
        (
            args.excludename,
            args.excludevals,
        ) = tide_io.processnamespec(
            args.excludespec, "Excluding voxels where ", "from offset calculation."
        )
    else:
        args.excludename = None
        args.excludevals = None

    includemask, excludemask, extramask = tide_mask.getmaskset(
        "anatomic",
        args.includename,
        args.includevals,
        args.excludename,
        args.excludevals,
        template_hdr,
        numvoxels,
        extramask=args.extramaskname,
    )
    themask = inputvoxels[:, 0] * 0 + 1
    if args.debug:
        print(f"{themask.shape=}")
    if includemask is not None:
        themask = themask * includemask.reshape((numvoxels))
        if args.debug:
            tide_io.savetonifti(
                includemask.reshape((xsize, ysize, numslices)),
                template_hdr,
                f"{args.outputroot}_includemask",
            )
    if excludemask is not None:
        themask = themask * (1 - excludemask.reshape((numvoxels)))
        if args.debug:
            tide_io.savetonifti(
                excludemask.reshape((xsize, ysize, numslices)),
                template_hdr,
                f"{args.outputroot}_excludemask",
            )
    if extramask is not None:
        themask = themask * extramask.reshape((numvoxels))
        if args.debug:
            tide_io.savetonifti(
                extramask.reshape((xsize, ysize, numslices)),
                template_hdr,
                f"{args.outputroot}_extramask",
            )

    # decide what regions we will summarize
    if args.regionlistfile is None:
        numregions = np.max(templatevoxels)
        regionlist = range(1, numregions + 1)
    else:
        regionlist = tide_io.readvec(args.regionlistfile).astype(int)
        numregions = len(regionlist)
    timecourses = np.zeros((numregions, numtimepoints), dtype="float")
    print(f"{numregions=}, {regionlist=}")

    if numtimepoints > 1:
        print("processing 4D input file")
        for theregion in regionlist:
            theregionvoxels = (
                inputvoxels[np.where(templatevoxels * themask == theregion)[0], :] + 0.0
            )
            print(
                "extracting",
                theregionvoxels.shape[1],
                "voxels from region",
                theregion,
                "of",
                numregions,
            )

            # demean
            themeans = np.mean(theregionvoxels, axis=1)
            theregionvoxels -= themeans[:, None]

            if args.normmethod == "none":
                thenormfac = themeans * 0.0 + 1.0
            elif args.normmethod == "pct":
                thenormfac = themeans
            elif args.normmethod == "var":
                thenormfac = np.var(theregionvoxels, axis=1)
            elif args.normmethod == "std":
                thenormfac = np.std(theregionvoxels, axis=1)
            elif args.normmethod == "p2p":
                thenormfac = np.max(theregionvoxels, axis=1) - np.min(theregionvoxels, axis=1)
            else:
                print("illegal normalization method", args.normmethod)
                _get_parser().print_help()
                raise
            if args.debug:
                print(theregionvoxels.shape, thenormfac.shape)
            for theloc in range(theregionvoxels.shape[0]):
                if thenormfac[theloc] != 0.0:
                    theregionvoxels[theloc, :] /= thenormfac[theloc]
            if theregionvoxels.shape[1] > 0:
                timecourses[theregion - 1, :] = summarize(
                    theregionvoxels, method=args.summarymethod
                )
        if args.debug:
            print("timecourses shape:", timecourses.shape)
        tide_io.writenpvecs(timecourses, args.outputroot)
    else:
        print("processing 3D input file")
        outputvoxels = inputvoxels * 0.0
        theregnums = []
        thevals = []
        if args.datalabel is not None:
            theregnums.append("Region")
            thevals.append(args.datalabel)
        for theregion in regionlist:
            theregnums.append(str(theregion))
            theregionvoxels = inputvoxels[np.where(templatevoxels * themask == theregion)]
            initnum = theregionvoxels.shape[0]
            if args.ignorezeros:
                theregionvoxels = theregionvoxels[np.where(theregionvoxels != 0.0)]
                numremoved = theregionvoxels.shape[0] - initnum
                if numremoved > 0:
                    extrabit = f" ({numremoved} voxels removed)"
                else:
                    extrabit = ""
                if args.debug:
                    print(
                        f"extracting {theregionvoxels.shape[0]} "
                        f"non-zero voxels from region {theregion} of {numregions}{extrabit}"
                    )
            else:
                if args.debug:
                    print(
                        f"extracting {theregionvoxels.shape[0]} "
                        f"voxels from region {theregion} of {numregions}"
                    )
            if theregionvoxels.shape[0] > 0:
                regionval = summarize(theregionvoxels, method=args.summarymethod)
                outputvoxels[np.where(templatevoxels == theregion)] = regionval
                thevals.append(str(regionval))
            else:
                if args.debug:
                    print(f"\tregion {theregion} is empty")
                thevals.append("None")
        template_hdr["dim"][4] = 1
        tide_io.savetonifti(
            outputvoxels.reshape((xsize, ysize, numslices)),
            template_hdr,
            args.outputroot,
        )
        if args.includename is not None or args.excludename is not None:
            tide_io.savetonifti(
                (templatevoxels * themask).reshape((xsize, ysize, numslices)),
                template_hdr,
                f"{args.outputroot}_maskedatlas",
            )
        if args.headerline:
            tide_io.writevec(
                [",".join(theregnums), ",".join(thevals)],
                f"{args.outputroot}_regionsummaries.csv",
            )
        else:
            tide_io.writevec(
                [",".join(thevals)],
                f"{args.outputroot}_regionsummaries.csv",
            )
