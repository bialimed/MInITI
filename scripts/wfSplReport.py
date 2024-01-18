#!/usr/bin/env python3

__author__ = 'Frederic Escudie'
__copyright__ = 'Copyright (C) 2020 CHU Toulouse'
__license__ = 'GNU General Public License'
__version__ = '1.0.0'

import os
import sys
import json
import logging
import argparse


########################################################################
#
# FUNCTIONS
#
########################################################################
def getTemplate():
    return """<html>
    <head>
        <title>MSI analysis</title>
        <meta charset="UTF-8">
        <meta name="version" content="##report_version##">
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
    parser.add_argument('-s', '--sample-name', help='The sample name.')
    parser.add_argument('-v', '--version', action='version', version=__version__)
    group_input = parser.add_argument_group('Inputs')
    group_input.add_argument('-i', '--input-report', required=True, help='Path to the MSI report file (format: MSIReport).')
    group_input.add_argument('-p', '--input-stable-peaks', required=True, help='Path to the most represented lengths by locus from stable microsatellites model (format: JSON).')
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
    report_content = report_content.replace("##report_version##", __version__)
    report_content = report_content.replace("##sample_name##", json.dumps(args.sample_name))
    report_content = report_content.replace("##data_method##", args.data_method_name)
    with open(args.input_stable_peaks) as reader_peaks:
        report_content = report_content.replace("##model_peaks##", json.dumps(json.load(reader_peaks)))
    with open(args.input_report) as reader:
        report_content = report_content.replace("##msi_data##", json.dumps(json.load(reader)))
    with open(args.output_report, "w") as writer:
        writer.write(report_content)
    log.info("End of job")
