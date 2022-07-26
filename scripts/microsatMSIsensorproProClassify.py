#!/usr/bin/env python3

__author__ = 'Frederic Escudie'
__copyright__ = 'Copyright (C) 2022 CHU Toulouse'
__license__ = 'GNU General Public License'
__version__ = '1.0.0'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'prod'

from anacore.msi.base import Status
from anacore.msi.locus import LocusRes
from anacore.msi.reportIO import ReportIO
from anacore.msisensorpro import ProEval
import argparse
import logging
import os
import sys


########################################################################
#
# FUNCTIONS
#
########################################################################
def getModelBaseline(locus_models):
    baseline = {
        "scores": {Status.stable: [], Status.unstable: []},
        "threshold": None,
        "ref_len": None
    }
    for curr_ref in locus_models:
        if "model" in curr_ref.results:
            baseline["ref_len"] = curr_ref.results["model"].data["MSIsensor-pro"]["ref_len"]
            curr_status = curr_ref.results["model"].status
            if curr_status in {Status.stable, Status.unstable}:
                baseline["scores"][curr_status].append(
                    curr_ref.results["model"].data["MSIsensor-pro"]["pro_p"]
                )
    baseline["threshold"] = ProEval.getThresholdFromScores(baseline["scores"][Status.stable])
    return baseline


def getScore(nb_peaks, models_peaks, status):
    pass


def getStatus(pro_p, baseline_locus):
    if pro_p >= baseline_locus["threshold"]:
        status = Status.unstable
    else:
        status = Status.stable
    return status


def process(args):
    eval_list = ReportIO.parse(args.input_evaluated)
    # Classify loci
    models = ReportIO.parse(args.input_model)
    model_baseline = dict()
    for curr_spl in eval_list:
        for locus_id, locus in curr_spl.loci.items():
            # Model
            if locus.position not in model_baseline:
                model_baseline[locus.position] = getModelBaseline(
                    [curr_model.loci[locus.position] for curr_model in models if locus.position in curr_model.loci]
                )
            baseline_locus = model_baseline[locus.position]
            # Classify
            locus_data = locus.results[args.data_method].data
            if args.data_method != args.status_method:  # Data come from another method
                locus_data = {"lengths": locus_data["lengths"]}
            locus_res = LocusRes(Status.undetermined, None, locus_data)
            if locus_data["lengths"].getCount() >= args.min_depth:
                locus_data["pro_p"], locus_data["pro_q"] = ProEval.getSlippageScores(
                    baseline_locus["ref_len"],
                    locus_data["lengths"]
                )
                locus_res.status = getStatus(locus_data["pro_p"], baseline_locus)
                ##########locus_res.score = getScore(locus_data["pro_p"], models_locus, locus_res.status)
            locus.results[args.status_method] = locus_res
        # Classify sample
        curr_spl.setStatusByInstabilityRatio(args.status_method, args.min_voting_loci, args.instability_ratio)
        curr_spl.setScore(args.status_method, args.undetermined_weight, args.locus_weight_is_score)
    # Write output
    ReportIO.write(eval_list, args.output_report)


########################################################################
#
# MAIN
#
########################################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Predict stability classes and scores for loci and samples using MSIsensor-pro pro v1.2.0 like algorithm.')
    parser.add_argument('--data-method', default="MSIsensor-pro pro", help='The name of the method storing locus metrics and where the status will be set. [Default: %(default)s]')
    parser.add_argument('--status-method', default="MSIsensor-pro pro", help='The name of the method storing locus metrics and where the status will be set. [Default: %(default)s]')
    parser.add_argument('-v', '--version', action='version', version=__version__)
    group_locus = parser.add_argument_group('Locus classifier')  # Locus status
    group_locus.add_argument('-m', '--min-depth', default=60, type=int, help='The minimum numbers of reads or fragments to determine the status. [Default: %(default)s]')
    group_status = parser.add_argument_group('Sample consensus status')  # Sample status
    group_status.add_argument('-i', '--instability-ratio', default=0.2, type=float, help='If the ratio unstable/(stable + unstable) is superior than this value the status of the sample will be unstable otherwise it will be stable. [Default: %(default)s]')
    group_status.add_argument('-l', '--min-voting-loci', default=0.5, type=float, help='Minimum number of voting loci (stable + unstable) to determine the sample status. If the number of voting loci is lower than this value the status for the sample will be undetermined. [Default: %(default)s]')
    group_score = parser.add_argument_group('Sample prediction score')  # Sample score
    group_score.add_argument('-g', '--locus-weight-is-score', action='store_true', help='Use the prediction score of each locus as wheight of this locus in sample prediction score calculation. [Default: %(default)s]')
    group_score.add_argument('-w', '--undetermined-weight', default=0, type=float, help='The weight of the undetermined loci in sample score calculation. [Default: %(default)s]')
    group_input = parser.add_argument_group('Inputs')  # Inputs
    group_input.add_argument('-e', '--input-evaluated', required=True, help='Path to the file containing the samples with loci to classify (format: MSIReport).')
    group_input.add_argument('-r', '--input-model', required=True, help='Path to the file containing the references samples used in learn step (format: MSIReport).')
    group_output = parser.add_argument_group('Outputs')  # Outputs
    group_output.add_argument('-o', '--output-report', required=True, help='The path to the output file (format: MSIReport).')
    args = parser.parse_args()

    # Logger
    logging.basicConfig(format='%(asctime)s -- [%(filename)s][pid:%(process)d][%(levelname)s] -- %(message)s')
    log = logging.getLogger(os.path.basename(__file__))
    log.setLevel(logging.INFO)
    log.info("Command: " + " ".join(sys.argv))

    # Process
    process(args)

    log.info("End of job")
