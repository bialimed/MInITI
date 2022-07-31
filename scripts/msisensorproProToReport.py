#!/usr/bin/env python3

__author__ = 'Frederic Escudie'
__copyright__ = 'Copyright (C) 2022 CHU-Toulouse'
__license__ = 'GNU General Public License'
__version__ = '1.0.0'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'prod'

from anacore.msi.msisensor import parseMSIsensorProResults, ProIO
from anacore.reportIO import ReportIO
import argparse
import logging
import os
import sys


#####################################################################
#
# MAIN
#
########################################################################
if __name__ == "__main__":
    # Manage parameters
    parser = argparse.ArgumentParser(description='Convert MSIsensor-pro pro results on all loci in report.')
    parser.add_argument('-v', '--version', action='version', version=__version__)
    group_locus = parser.add_argument_group('Locus classifier')  # Locus status
    group_locus.add_argument('--min-depth', default=60, type=int, help='The minimum numbers of reads or fragments to determine the status. [Default: %(default)s]')
    group_status = parser.add_argument_group('Sample consensus status')  # Sample status
    group_status.add_argument('--min-voting-ratio', default=0.5, type=float, help='Minimum number of determined on all loci to determine the sample status. If the number of voting loci is lower than this value the status for the sample will be undetermined. [Default: %(default)s]')
    group_status.add_argument('--instability-ratio', default=0.2, type=float, help='[Only with consensus-method = ratio] If the ratio unstable/(stable + unstable) is superior than this value the status of the sample will be unstable otherwise it will be stable. [Default: %(default)s]')
    group_score = parser.add_argument_group('Sample prediction score')  # Sample score
    group_score.add_argument('--undetermined-weight', default=0, type=float, help='The weight of the undetermined loci in sample score calculation. [Default: %(default)s]')
    group_score.add_argument('--locus-weight-is-score', action='store_true', help='Use the prediction score of each locus as wheight of this locus in sample prediction score calculation. [Default: %(default)s]')
    group_input = parser.add_argument_group('Inputs')  # Inputs
    group_input.add_argument('-d', '--input-distributions', required=True, help='Path to the file containing lengths distribution from MSIsensor (format: txt).')
    group_input.add_argument('-l', '--input-loci', required=True, help='Path to the file containing p_pro for all loci from MSIsensor (format: TSV).')
    group_output = parser.add_argument_group('Outputs')  # Outputs
    group_output.add_argument('-o', '--output-report', required=True, help='The path to the output file (format: ReportIO).')
    args = parser.parse_args()

    # Logger
    logging.basicConfig(format='%(asctime)s -- [%(filename)s][pid:%(process)d][%(levelname)s] -- %(message)s')
    log = logging.getLogger(os.path.basename(__file__))
    log.setLevel(logging.INFO)
    log.info("Command: " + " ".join(sys.argv))

    # Process
    loci = ProIO.loci(args.input_loci)
    spl = parseMSIsensorProResults(
        args.sample_name,
        args.input_loci,
        args.input_distributions,
        args.instability_ratio,
        args.min_voting_ratio,
        args.min_depth
    )
    spl.setScore("MSIsensor-pro_pro", args.undetermined_weight, args.locus_weight_is_score)
    ReportIO.write([spl], args.output_report)
    log.info("End of job")
