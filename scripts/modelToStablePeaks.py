#!/usr/bin/env python3

__author__ = 'Frederic Escudie'
__copyright__ = 'Copyright (C) 2023 CHU Toulouse'
__license__ = 'GNU General Public License'
__version__ = '1.0.0'

from anacore.msi.base import Status
from anacore.msi.reportIO import ReportIO
import argparse
import json
import logging
import os
import sys


########################################################################
#
# FUNCTIONS
#
########################################################################
def getHigherPeakByLocus(models, min_support_reads=0):
    """
    Return length of the higher peak of each model by locus.

    :param models: The list of MSIReport representing the models (status known and stored in Expected result).
    :type models: list
    :param min_support_reads: The minimum number of reads on locus to use the stability status of the current model.
    :type min_support_reads: int
    :return: By locus the list of higher peak length.
    :rtype: dict
    """
    higher_by_locus = {}
    models_samples = ReportIO.parse(models)
    for curr_spl in models_samples:
        for locus_id, curr_locus in curr_spl.loci.items():
            if locus_id not in higher_by_locus:
                higher_by_locus[locus_id] = []
            if "model" in curr_locus.results:
                locus_res = curr_locus.results["model"]
                if locus_res.status == Status.stable and locus_res.data["lengths"].getCount() > min_support_reads / 2:
                    max_peak = None
                    max_count = -1
                    for length, count in locus_res.data["lengths"].items():
                        if count >= max_count:  # "=" for select the tallest
                            max_count = count
                            max_peak = int(length)
                    higher_by_locus[locus_id].append(max_peak)
            higher_by_locus[locus_id] = sorted(higher_by_locus[locus_id])
    return higher_by_locus


########################################################################
#
# MAIN
#
########################################################################
if __name__ == "__main__":
    # Manage parameters
    parser = argparse.ArgumentParser(description="Extract stable microsatellites most represented length by locus from model.")
    parser.add_argument('-s', '--min-support', default=0, type=int, help='Minimum number of reads/fragments in size distribution to keep a model sample in the stable model peak retrieval process. [Default: %(default)s]')
    parser.add_argument('-v', '--version', action='version', version=__version__)
    group_input = parser.add_argument_group('Inputs')
    group_input.add_argument('-m', '--input-model', required=True, help='Path to the model file (format: MSIReport).')
    group_output = parser.add_argument_group('Outputs')
    group_output.add_argument('-o', '--output-peaks', help='Path to the outputted the stable microsatellites most represented length by locus from model (format: JSON).')
    args = parser.parse_args()

    # Logger
    logging.basicConfig(format='%(asctime)s - %(name)s [%(levelname)s] %(message)s')
    log = logging.getLogger(os.path.basename(__file__))
    log.setLevel(logging.INFO)
    log.info("Command: " + " ".join(sys.argv))

    # Process
    higher_peaks_by_locus = getHigherPeakByLocus(args.input_model, args.min_support)
    with open(args.output_peaks, "w") as writer:
        json.dump(higher_peaks_by_locus, writer)
    log.info("End of job")
