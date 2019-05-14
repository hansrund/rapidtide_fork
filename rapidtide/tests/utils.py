#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
Utility functions for testing rapidtide.
"""

import os

import numpy as np


def get_rapidtide_root():
    """
    Returns the path to the base rapidtide directory, terminated with separator.
    Based on function by Yaroslav Halchenko used in Neurosynth Python package.
    """
    thisdir, thisfile = os.path.split(os.path.join(os.path.realpath(__file__)))
    return os.path.join(thisdir, '..') + os.path.sep


def get_scripts_path():
    """
    Returns the path to test datasets, terminated with separator. Test-related
    data are kept in tests folder in "testdata".
    Based on function by Yaroslav Halchenko used in Neurosynth Python package.
    """
    return os.path.realpath(os.path.join(get_rapidtide_root(), 'scripts')) + os.path.sep


def get_test_data_path():
    """
    Returns the path to test datasets, terminated with separator. Test-related
    data are kept in tests folder in "testdata".
    Based on function by Yaroslav Halchenko used in Neurosynth Python package.
    """
    return os.path.realpath(os.path.join(get_rapidtide_root(), 'tests', 'testdata')) + os.path.sep


def get_test_target_path():
    """
    Returns the path to test comparison data, terminated with separator. Test-related
    data are kept in tests folder in "testtargets".
    Based on function by Yaroslav Halchenko used in Neurosynth Python package.
    """
    return os.path.realpath(os.path.join(get_rapidtide_root(), 'tests', 'testtargets')) + os.path.sep


def get_test_temp_path():
    """
    Returns the path to test temporary directory, terminated with separator.
    Based on function by Yaroslav Halchenko used in Neurosynth Python package.
    """
    return os.path.realpath(os.path.join(get_rapidtide_root(), 'tests', 'tmp')) + os.path.sep


def get_examples_path():
    """
    Returns the path to examples src directory, where larger test files live, terminated with separator. Test-related
    data are kept in tests folder in "data".
    Based on function by Yaroslav Halchenko used in Neurosynth Python package.
    """
    return os.path.realpath(os.path.join(get_rapidtide_root(), 'data', 'examples', 'src')) + os.path.sep


def mse(vec1, vec2):
    """
    Compute mean-squared error.
    """
    return np.mean(np.square(vec2 - vec1))
