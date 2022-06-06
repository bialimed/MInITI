#!/usr/bin/env python3

__author__ = 'Frederic Escudie'
__copyright__ = 'Copyright (C) 2020 IUCT-O'
__license__ = 'GNU General Public License'
__version__ = '1.0.0'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'prod'

import os
import sys
import json
import logging
import argparse
from anacore.msi.base import Status
from anacore.msi.reportIO import ReportIO


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
    return higher_by_locus


def getTemplate():
    return """<html>
    <head>
        <title>MSI analysis</title>
        <meta charset="UTF-8">
        <meta name="author" content="Escudie Frederic">
        <meta name="version" content="1.0.0">
        <meta name="copyright" content="2020 CHU Toulouse">
        <!-- uuid -->
        <script type="text/javascript" charset="utf8" src="resources/uuid_8.3.2.min.js"></script>
        <!-- jQuery -->
        <script type="text/javascript" charset="utf8" src="resources/jquery_3.3.1.min.js"></script>
        <!-- HighCharts -->
        <script type="text/javascript" charset="utf8" src="resources/highcharts_7.1.0.min.js"></script>
        <script type="text/javascript" charset="utf8" src="resources/highcharts-more_7.1.0.min.js"></script>
        <!-- DataTables -->
        <link type="text/css" charset="utf8" rel="stylesheet" href="resources/datatables_1.10.18.min.css"/>
        <script type="text/javascript" charset="utf8" src="resources/pdfmake_0.1.36.min.js"></script>
        <script type="text/javascript" charset="utf8" src="resources/vfs_fonts_0.1.36.min.js"></script>
        <script type="text/javascript" charset="utf8" src="resources/datatables_1.10.18.min.js"></script>
        <!-- Popper -->
        <script type="text/javascript" charset="utf8" src="resources/popper_1.16.1.min.js"></script>
        <!-- Bootstrap -->
        <link type="text/css" charset="utf8" rel="stylesheet" href="resources/bootstrap-4.3.1-dist/css/bootstrap.min.css">
        <script type="text/javascript" charset="utf8" src="resources/bootstrap-4.3.1-dist/js/bootstrap.min.js"></script>
        <!-- FontAwesome -->
        <link type="text/css" charset="utf8" rel="stylesheet" href="resources/fontawesome-free-5.13.0-dist/css/all.min.css">
        <!-- WebComponents -->
        <link type="text/css" charset="utf8" rel="stylesheet" href="resources/webCmpt.min.css"></script>
        <script type="text/javascript" charset="utf8" src="resources/vue_2.6.10.min.js"></script>
        <script type="text/javascript" charset="utf8" src="resources/webCmpt.min.js"></script>
    </head>
    <body>
        <nav class="navbar fixed-top justify-content-center">
            <span class="align-middle">
                <template v-if="sample_name === null">MSI analysis</template>
                <template v-else>Sample {{sample_name}}</template>
            </span>
        </nav>
        <div class="page-content">
            <div class="card">
                <h3 class="card-header">Sample</h3>
                <div class="card-block">
                    <msi-sample-card v-if="msi != null"
                        :analysis="msi">
                    </msi-sample-card>
                </div>
            </div>
            <div class="card">
                <h3 class="card-header">Loci</h3>
                <div class="card-block">
                    <msi-loci-card v-if="msi != null"
                        :analysis="msi"
                        :model_peaks="model_peaks"
                        :reference_method="data_method">
                    </msi-loci-card>
                </div>
            </div>
        </div>
        <script>
            // Navbar
            new Vue({
                el: "nav.fixed-top",
                data: {
                    "sample_name": ##sample_name##
                }
            })
            // Page content
            new Vue({
                el: ".page-content",
                data: {
                    "data_method": "##data_method##",
                    "model_peaks": ##model_peaks##,
                    "msi": null
                },
                mounted: function(){
                    this.loadData()
                },
                methods: {
                    loadData: function(){
                        this.msi = MSIReport.fromJSON(##msi_data##)
                    }
                }
            })
        </script>
    </body>
</html>"""


########################################################################
#
# MAIN
#
########################################################################
if __name__ == "__main__":
    # Manage parameters
    parser = argparse.ArgumentParser(description="Create HTML report for one sample.")
    parser.add_argument('-d', '--data-method-name', default="alnLength", help='The name of the method storing length distribution. [Default: %(default)s]')
    parser.add_argument('-u', '--model-min-support', type=int, help='Minimum number of reads/fragments in size distribution to keep a model sample in the stable model peak retrieval process. [Default: %(default)s]')
    parser.add_argument('-s', '--sample-name', help='The sample name.')
    parser.add_argument('-v', '--version', action='version', version=__version__)
    group_input = parser.add_argument_group('Inputs')
    group_input.add_argument('-m', '--input-model', required=True, help='Path to the model file (format: MSIReport).')
    group_input.add_argument('-i', '--input-report', required=True, help='Path to the MSI report file (format: MSIReport).')
    group_output = parser.add_argument_group('Outputs')
    group_output.add_argument('-o', '--output-report', help='Path to the outputted report file (format: HTML).')
    args = parser.parse_args()

    # Logger
    logging.basicConfig(format='%(asctime)s - %(name)s [%(levelname)s] %(message)s')
    log = logging.getLogger(os.path.basename(__file__))
    log.setLevel(logging.INFO)
    log.info("Command: " + " ".join(sys.argv))

    # Process
    report_content = getTemplate()
    report_content = report_content.replace("##sample_name##", json.dumps(args.sample_name))
    report_content = report_content.replace("##data_method##", args.data_method_name)
    model_min_support = 0 if args.model_min_support is None else args.model_min_support
    higher_peak_by_locus = getHigherPeakByLocus(args.input_model, model_min_support)
    report_content = report_content.replace("##model_peaks##", json.dumps(higher_peak_by_locus))
    with open(args.input_report) as reader:
        report_content = report_content.replace("##msi_data##", json.dumps(json.load(reader)))
    with open(args.output_report, "w") as writer:
        writer.write(report_content)
    log.info("End of job.")
