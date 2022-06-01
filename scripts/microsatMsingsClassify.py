#!/usr/bin/env python3

__author__ = 'Frederic Escudie'
__copyright__ = 'Copyright (C) 2022 CHU Toulouse'
__license__ = 'GNU General Public License'
__version__ = '1.0.0'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'prod'

from anacore.msi.base import LocusRes, MSIReport, Status
import argparse
import logging
from numpy import average, std
import os
from scipy.stats import norm
import sys


########################################################################
#
# FUNCTIONS
#
########################################################################
def getHighestPeak(distrib):
    highest_peak = {"length": None, "count": 0}
    for length, count in distrib.items():
        if count >= highest_peak["count"]:
            highest_peak["length"] = length
            highest_peak["count"] = count
    return highest_peak


def getModelBaseline(locus_models, peak_height_cutoff=0.05):
    models_nb_peaks = list()
    for curr_ref in locus_models:
        if curr_ref.results["model"].status == Status.stable:
            models_nb_peaks.append(
                getMSINGSNbPeaks(curr_ref.results["model"].data["nb_by_length"], peak_height_cutoff)
            )
    return {
        "average": average(models_nb_peaks),
        "count": len(models_nb_peaks),
        "std_dev": std(models_nb_peaks)
    }


def getNbPeaks(distrib, min_count=0):
    nb_peak = 0
    for length, count in distrib.items():
        if count >= min_count:
            nb_peak += 1
    return nb_peak


def getMSINGSNbPeaks(nb_by_length, peak_height_cutoff):
    highest_peak = getHighestPeak(nb_by_length)
    min_peak_height = peak_height_cutoff * highest_peak["count"]
    return getNbPeaks(nb_by_length, min_peak_height)


def getScore(nb_peaks, models_peaks):
    return 1 - norm.cdf(nb_peaks, loc=models_peaks["avg"], scale=models_peaks["std_dev"])


def getStatus(nb_peaks, models_peaks, std_dev_rate):
    nb_peaks_threshold = models_peaks["avg"] + models_peaks["std_dev"] * std_dev_rate
    if nb_peaks >= nb_peaks_threshold:
        status = Status.instable
    else:
        status = Status.stable
    return status


def process(args):
    msi_evaluated = MSIReport.parse(args.input_evaluated)
    # Classify loci
    msi_models = MSIReport.parse(args.input_model)
    model_baseline = dict()
    for msi_spl in msi_evaluated:
        for locus in msi_spl:
            if locus.position not in model_baseline:
                model_baseline[locus.position] = getModelBaseline(
                    [curr_model.loci[locus.position] for curr_model in msi_models if locus.position in curr_model.loci],
                    args.peak_height_cutoff
                )
            models_peaks = model_baseline[locus.position]
            locus_res_src = locus.results[args.data_method]
            locus_res = LocusRes(data=locus_res_src.data)
            locus_res._class = locus.results[args.data_method]._class
            if locus_res_src.getCount() >= args.min_depth:
                nb_peaks = getMSINGSNbPeaks(locus_res_src.data["nb_by_length"], args.peak_height_cutoff)
                locus_res.status = getStatus(nb_peaks, models_peaks, args.std_dev_rate)
                locus_res.score = getScore(nb_peaks, models_peaks)
            locus.results[args.status_method] = locus_res
        # Classify sample
        if args.consensus_method == "majority":
            msi_spl.setStatusByMajority(args.status_method, args.min_voting_loci)
        elif args.consensus_method == "ratio":
            msi_spl.setStatusByInstabilityRatio(args.status_method, args.min_voting_loci, args.instability_ratio)
        elif args.consensus_method == "count":
            msi_spl.setStatusByInstabilityCount(args.status_method, args.min_voting_loci, args.instability_count)
        msi_evaluated.setScore(args.status_method, args.undetermined_weight, args.locus_weight_is_score)
    # Write output
    MSIReport.write(msi_evaluated, args.output_report)


########################################################################
#
# MAIN
#
########################################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Predict stability classes and scores for loci and samples using mSINGS v4.0 like algorithm.')
    parser.add_argument('-d', '--data-method', default="aln", help='The name of the method storing locus metrics and where the status will be set. [Default: %(default)s]')
    parser.add_argument('-s', '--status-method', default="mSINGSLike", help='The name of the method storing locus metrics and where the status will be set. [Default: %(default)s]')
    parser.add_argument('-v', '--version', action='version', version=__version__)
    group_locus = parser.add_argument_group('Locus classifier')  # Locus status
    group_locus.add_argument('-m', '--min-depth', default=150, type=int, help='The minimum numbers of reads or fragments to determine the status. [Default: %(default)s]')
    group_locus.add_argument('-p', '--peak-height-cutoff', default=0.05, type=float, help='Minimum height to consider a peak in size distribution as rate of the highest peak. [Default: %(default)s]')
    group_locus.add_argument('-s', '--std-dev-rate', default=2.0, type=float, help='The locus is tagged as unstable if the number of peaks is upper than models_avg_nb_peaks + std_dev_rate * models_std_dev_nb_peaks. [Default: %(default)s]')
    group_status = parser.add_argument_group('Sample consensus status')  # Sample status
    group_status.add_argument('-c', '--consensus-method', default='ratio', choices=['count', 'majority', 'ratio'], help='Method used to determine the sample status from the loci status. Count: if the number of unstable is upper or equal than instability-count the sample will be unstable otherwise it will be stable ; Ratio: if the ratio of unstable/determined loci is upper or equal than instability-ratio the sample will be unstable otherwise it will be stable ; Majority: if the ratio of unstable/determined loci is upper than 0.5 the sample will be unstable, if it is lower than stable the sample will be stable. [Default: %(default)s]')
    group_status.add_argument('-l', '--min-voting-loci', default=3, type=int, help='Minimum number of voting loci (stable + unstable) to determine the sample status. If the number of voting loci is lower than this value the status for the sample will be undetermined. [Default: %(default)s]')
    group_status.add_argument('-i', '--instability-ratio', default=0.2, type=float, help='[Only with consensus-method = ratio] If the ratio unstable/(stable + unstable) is superior than this value the status of the sample will be unstable otherwise it will be stable. [Default: %(default)s]')
    group_status.add_argument('-u', '--instability-count', default=3, type=int, help='[Only with consensus-method = count] If the number of unstable loci is upper or equal than this value the sample will be unstable otherwise it will be stable. [Default: %(default)s]')
    group_score = parser.add_argument_group('Sample prediction score')  # Sample score
    group_score.add_argument('-w', '--undetermined-weight', default=0.5, type=float, help='The weight of the undetermined loci in sample score calculation. [Default: %(default)s]')
    group_score.add_argument('-g', '--locus-weight-is-score', action='store_true', help='Use the prediction score of each locus as wheight of this locus in sample prediction score calculation. [Default: %(default)s]')
    group_input = parser.add_argument_group('Inputs')  # Inputs
    group_input.add_argument('-r', '--input-model', required=True, help='Path to the file containing the references samples used in learn step (format: MSIReport).')
    group_input.add_argument('-e', '--input-evaluated', required=True, help='Path to the file containing the samples with loci to classify (format: MSIReport).')
    group_output = parser.add_argument_group('Outputs')  # Outputs
    group_output.add_argument('-o', '--output-report', required=True, help='The path to the output file (format: MSIReport).')
    args = parser.parse_args()

    if args.consensus_method != "ratio" and args.instability_ratio != parser.get_default('instability_ratio'):
        raise Exception('The parameter "instability-ratio" can only used with consensus-ratio set to "ratio".')
    if args.consensus_method != "count" and args.instability_count != parser.get_default('instability_count'):
        raise Exception('The parameter "instability-count" can only used with consensus-ratio set to "count".')

    # Logger
    logging.basicConfig(format='%(asctime)s -- [%(filename)s][pid:%(process)d][%(levelname)s] -- %(message)s')
    log = logging.getLogger(os.path.basename(__file__))
    log.setLevel(logging.INFO)
    log.info("Command: " + " ".join(sys.argv))

    # Process
    process(args)

    log.info("End of job")
