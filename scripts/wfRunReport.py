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
from anacore.msi.base import MSIReport


########################################################################
#
# FUNCTIONS
#
########################################################################
class ScoreClassAction(argparse.Action):
    """Manages score class parameter."""

    def __call__(self, parser, namespace, values, option_string=None):
        class_by_score = {}
        for curr in values:
            class_name, score = curr.split(":", 1)
            class_by_score[float(score)] = class_name
        setattr(namespace, self.dest, class_by_score)


def getTemplate():
    return """<html>
    <head>
        <title>Run</title>
        <meta charset="UTF-8">
        <meta name="author" content="Escudie Frederic">
        <meta name="version" content="1.0.0">
        <meta name="copyright" content="2020 IUCT-O">
        <!-- jQuery -->
        <script type="text/javascript" charset="utf8" src="resources/jquery_3.3.1.min.js"></script>
        <!-- DataTables -->
        <link type="text/css" charset="utf8" rel="stylesheet" href="resources/datatables_1.10.18.min.css"/>
        <script type="text/javascript" charset="utf8" src="resources/pdfmake_0.1.36.min.js"></script>
        <script type="text/javascript" charset="utf8" src="resources/vfs_fonts_0.1.36.min.js"></script>
        <script type="text/javascript" charset="utf8" src="resources/datatables_1.10.18.min.js"></script>
        <!-- Bootstrap -->
        <link type="text/css" charset="utf8" rel="stylesheet" href="resources/bootstrap-4.3.1-dist/css/bootstrap.min.css">
        <script type="text/javascript" charset="utf8" src="resources/bootstrap-4.3.1-dist/js/bootstrap.min.js"></script>
        <!-- WebComponents -->
        <script type="text/javascript" charset="utf8" src="resources/vue_2.6.10.min.js"></script>
        <link type="text/css" charset="utf8" rel="stylesheet" href="resources/webCmpt.min.css"></link>
        <script type="text/javascript" charset="utf8" src="resources/webCmpt.min.js"></script>
    </head>
    <body>
        <nav class="navbar fixed-top justify-content-center">
            <span class="align-middle">Run</span>
        </nav>
        <div class="page-content">
            <div class="card">
                <h3 class="card-header">Samples</h3>
                <div class="card-block">
                    <div class="row">
                        <div class="col-sm-0 col-md-1"></div>
                        <div class="col-sm-12 col-md-10">
                            <dynamic-table
                                :data="samples"
                                :header="columns"
                                title="Samples">
                            </dynamic-table>
                        </div>
                        <div class="col-sm-0 col-md-1"></div>
                    </div>
                </div>
            </div>
        </div>
        <script>
            function classByScore(score) {
                const thresholds = ##class_by_score##
                let class_name = "danger"
                const asc_thresholds = Object.keys(thresholds).sort(function (a, b) {  return parseFloat(a) - parseFloat(b)  })
                asc_thresholds.forEach(function(curr_threshold){
                    if( parseFloat(curr_threshold) <= parseFloat(score) ){
                        class_name = thresholds[curr_threshold]
                    }
                })
                return "msi-label msi-label-" + class_name
            }
            
            new Vue({
                el: ".page-content",
                data: {
                    "columns": [
                        {
                            "title": "Name",
                            "href": function(entry, col){ return `${entry.Name}.html` },
                            "sort": "asc"
                        },
                        {
                            "title": "Status",
                            "class": "msi-sticker",
                            "entryClass": function(entry, col){
                                return entry.Status
                            }
                        },
                        {
                            "title": "Score",
                            "is_html": true,
                            "value": function(entry, col){
                                let score = null
                                if (entry.Status != "Undetermined") {
                                    return `<span class="${classByScore(entry.Score)}">${entry.Score.toFixed(2)}</span>`
                                }
                                return score
                            }
                        },
                        {
                            "title": "Rate",
                            "value": function(entry, col){
                                return entry.Rate == null ? null : entry.Rate.toFixed(2)
                            }
                        },
                        {"title": "Support"}
                    ],
                    "samples": ##samples##
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
    parser = argparse.ArgumentParser(description="Create HTML report for run.")
    parser.add_argument('-c', '--class-by-score', action=ScoreClassAction, default={0.70: "warning", 0.95: "good"}, help='Minimum score for each score class "warning, "succes" and "good" (format "warning:0.7 success:0.9". The others values have the class "danger". [Default: %(default)s]')
    parser.add_argument('-m', '--classification-method-name', default="SVC", help='The name of the method storing results in MSISample. [Default: %(default)s]')
    parser.add_argument('-v', '--version', action='version', version=__version__)
    group_input = parser.add_argument_group('Inputs')
    group_input.add_argument('-r', '--inputs-report', required=True, nargs='+', help='Pathes to MSI reports (format: MSIReport).')
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
    report_content = report_content.replace("##class_by_score##", json.dumps(args.class_by_score))
    samples = []
    for curr_report in args.inputs_report:
        msi_spl = MSIReport.parse(curr_report)[0]
        print(msi_spl.name, msi_spl.getNbUnstable(args.classification_method_name), msi_spl.getNbDetermined(args.classification_method_name))
        samples.append({
            "Name": msi_spl.name,
            "Rate": None if msi_spl.getNbDetermined(args.classification_method_name) == 0 else msi_spl.getNbUnstable(args.classification_method_name) / msi_spl.getNbDetermined(args.classification_method_name),
            "Score": msi_spl.results[args.classification_method_name].score,
            "Status": msi_spl.results[args.classification_method_name].status,
            "Support": msi_spl.getNbDetermined(args.classification_method_name)
        })
    report_content = report_content.replace("##samples##", json.dumps(samples))
    with open(args.output_report, "w") as writer:
        writer.write(report_content)
    log.info("End of job.")
