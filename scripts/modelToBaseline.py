#!/usr/bin/env python3

__author__ = 'Frederic Escudie'
__copyright__ = 'Copyright (C) 2022 CHU-Toulouse'
__license__ = 'GNU General Public License'
__version__ = '1.0.0'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'prod'

from anacore.msi.msisensor import BaselineIO, BaselineRecord
from anacore.BEDIO import getAreas
from anacore.reportIO import ReportIO
from anacore.sequenceIO import IdxFastaIO
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
    parser = argparse.ArgumentParser(description='Write MSIsensor-pro baseline file from model (ReportIO).')
    parser.add_argument('-s', '--flank-size', type=int, default=5, help='Size of flanking sequence for microsatellites.')
    parser.add_argument('-n', '--method-name', default="model", help='Name of method storing model information in model file. [Default: %(default)s].')
    parser.add_argument('-v', '--version', action='version', version=__version__)
    group_input = parser.add_argument_group('Inputs')  # Inputs
    group_input.add_argument('-m', '--input-models', required=True, help='Path to the file containing the references samples used in learn step (format: ReportIO).')
    group_input.add_argument('-s', '--input-sequences', required=True, help='Path to the reference sequences file (format: fasta).')
    group_input.add_argument('-t', '--input-targets', required=True, help='Path to the microsatellites locations file (format: BED).')
    group_output = parser.add_argument_group('Outputs')  # Outputs
    group_output.add_argument('-o', '--output-baseline', required=True, help='The path to the output file (format: TSV).')
    args = parser.parse_args()

    # Logger
    logging.basicConfig(format='%(asctime)s -- [%(filename)s][pid:%(process)d][%(levelname)s] -- %(message)s')
    log = logging.getLogger(os.path.basename(__file__))
    log.setLevel(logging.INFO)
    log.info("Command: " + " ".join(sys.argv))

    # Process
    with BaselineIO(args.output_baseline, "w") as baseline_fh:
        models = ReportIO(args.input_models)
        with IdxFastaIO(args.input_sequences) as ref_fh:
            for target in getAreas(args.input_targets):
                baseline_fh.write(
                    BaselineRecord.fromModel(
                        ref_fh,
                        target,
                        models,
                        model_method=args.model_method,
                        flank_size=args.flank_size
                    )
                )
    log.info("End of job")
