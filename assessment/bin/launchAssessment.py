#!/usr/bin/env python3

__author__ = 'Frederic Escudie'
__copyright__ = 'Copyright (C) 2018 CHU Toulouse'
__license__ = 'GNU General Public License'
__version__ = '2.1.0'

from anacore.bed import getAreas
from anacore.msi.reportIO import ReportIO
from anacore.sv import HashedSVIO
import argparse
import hashlib
from itertools import product
import logging
import pandas as pd
import os
from sklearn.model_selection import ShuffleSplit
import shutil
import subprocess
import sys


########################################################################
#
# FUNCTIONS
#
########################################################################
def getSplFromLibName(lib_name):
    """
    Return sample name from library name.

    :param lib_name: The library name.
    :type lib_name: str
    :return: The sample name.
    :rtype: str
    """
    return lib_name.split("_")[0]


def getLibFromDataFolder(aln_folder):
    """
    Return libraries information from folder containing fastq.

    :param data_folder: Path to the folder containing fastq.
    :type data_folder: str
    :return: The list of libraries. Each element is a dictionary containing the following keys: name, spl_name, R1, R2.
    :rtype: list
    """
    libraries = []
    for filename in sorted(os.listdir(aln_folder)):
        if filename.endswith(".bam"):
            filepath = os.path.join(aln_folder, filename)
            libraries.append({
                "name": filename.split(".")[0],
                "path": os.path.abspath(filepath)
            })
    return libraries


def getStatus(in_annotations, samples):
    """
    Return status by locus by sample.

    :param in_annotations: Path to the file containing status by locus by sample (format: TSV).
    :type in_annotations: str
    :param samples: List of samples names.
    :type samples: list
    :return: Status by locus by sample.
    :rtype: dict
    """
    status_by_spl = {}
    samples = set(samples)
    with HashedSVIO(in_annotations, title_starter="") as FH:
        for record in FH:
            spl_name = getSplFromLibName(record["sample"])
            if spl_name in samples:
                status_by_spl[spl_name] = {key: value for key, value in record.items() if key not in ["sample", "sample_status"]}
                status_by_spl[spl_name]["sample"] = record["status"]
    for spl in samples:
        if spl not in status_by_spl:
            raise Exception("Sample {} has no expected data.".format(spl))
    return status_by_spl


def train(libraries, out_folder, cfg_tpl_path, status_path, targets_path, padding, min_support_reads, stitching, duplicates, log):
    os.makedirs(out_folder)
    # Create config
    cfg_path = os.path.join(out_folder, "config.yml")
    with open(cfg_tpl_path) as reader:
        with open(cfg_path, "w") as writer:
            for line in reader:
                line = line.replace("##KEEP_DUPLICATES##", str(duplicates == "with").lower())
                line = line.replace("##MIN_SUPPORT##", str(int(min_support_reads / 2)) if stitching else str(min_support_reads))
                line = line.replace("##PADDING##", str(padding))
                line = line.replace("##STITCH_COUNT##", str(stitching == "with").lower())
                writer.write(line)
    # Create raw
    raw_folder = os.path.join(out_folder, "raw")
    os.makedirs(raw_folder)
    for lib in libraries:
        os.symlink(lib["path"], os.path.join(raw_folder, lib["name"] + ".bam"))
        os.symlink(lib["path"][:-4] + ".bai", os.path.join(raw_folder, lib["name"] + ".bai"))
    # Design
    os.symlink(status_path, os.path.join(out_folder, "status.tsv"))
    os.symlink(targets_path, os.path.join(out_folder, "targets.bed"))
    # Command
    bin_dir = os.path.dirname(os.path.abspath(__file__))
    cmd = [
        os.path.join(bin_dir, "launch_snk.sh"),
        "Snakefile_learn",
        cfg_path,
        out_folder
    ]
    log.debug("submit: ".join(cmd))
    subprocess.check_call(cmd)


def predict(libraries, out_folder, cfg_tpl_path, targets_path, model_path, clf, padding, min_support_reads, stitching, duplicates, log):
    os.makedirs(out_folder)
    # Create config
    cfg_path = os.path.join(out_folder, "config.yml")
    with open(cfg_tpl_path) as reader:
        with open(cfg_path, "w") as writer:
            for line in reader:
                line = line.replace("##CLASSIFIER##", clf["class"])
                line = line.replace("##CLASSIFIER_PARAMS##", clf["params"])
                line = line.replace("##KEEP_DUPLICATES##", str(duplicates == "with").lower())
                line = line.replace("##MIN_SUPPORT##", str(int(min_support_reads / 2)) if stitching else str(min_support_reads))
                line = line.replace("##MODEL_PATH##", model_path)
                line = line.replace("##PADDING##", str(padding))
                line = line.replace("##STITCH_COUNT##", str(stitching == "with").lower())
                writer.write(line)
    # Create raw
    raw_folder = os.path.join(out_folder, "raw")
    os.makedirs(raw_folder)
    for lib in libraries:
        os.symlink(lib["path"], os.path.join(raw_folder, lib["name"] + ".bam"))
        os.symlink(lib["path"][:-4] + ".bai", os.path.join(raw_folder, lib["name"] + ".bai"))
    # Design
    os.symlink(targets_path, os.path.join(out_folder, "targets.bed"))
    # Command
    bin_dir = os.path.dirname(os.path.abspath(__file__))
    cmd = [
        os.path.join(bin_dir, "launch_snk.sh"),
        "Snakefile_tag",
        cfg_path,
        out_folder
    ]
    log.debug("submit: ".join(cmd))
    subprocess.check_call(cmd)


def getResInfoTitles(loci_id_by_name):
    """
    Return titles for the result dataframe.

    :param loci_id_by_name: List of locus names.
    :type loci_id_by_name: dict
    :return: Titles for results dataframe.
    :rtype: list
    """
    titles = [
        "dataset_id",
        "lib_name",
        "config",
        "classifier",
        "padding",
        "min_support",
        "stitching",
        "duplicates",
        "spl_expected_status",
        "spl_observed_status",
        "spl_pred_score"
    ]
    for locus_name in sorted(loci_id_by_name):
        titles.extend([
            locus_name + "_expected_status",
            locus_name + "_observed_status",
            locus_name + "_pred_score",
            locus_name + "_pred_support"
        ])
    return titles


def getMethodResInfo(dataset_id, clf_name, padding, min_support, stitching, duplicates, loci_id_by_name, reports, status_by_spl, method_name):
    """
    Return rows from the specified method for the results dataframe.

    :param dataset_id: Dataset ID.
    :type dataset_id: str
    :param loci_id_by_name: List of locus names.
    :type loci_id_by_name: dict
    :param reports: List of MSISample.
    :type reports: list
    :param status_by_spl: Status by locus by sample name.
    :type status_by_spl: dict
    :param method_name: Name of the processed method.
    :type method_name: str
    :return: Rows for results dataframe.
    :rtype: list
    """
    dataset_res = []
    for curr_report in reports:
        expected = status_by_spl[curr_report.name]
        row = [
            dataset_id,
            curr_report.name,  # sample name
            "clf={}, pad={}, min_supp={}, sitch={}, dup={}".format(clf_name, padding, min_support, stitching, duplicates),
            clf_name,
            padding,
            min_support,
            stitching,
            duplicates
        ]
        row.extend([
            expected["sample"],  # expected
            curr_report.results[method_name].status,  # observed
            curr_report.results[method_name].score  # score
        ])
        for locus_name in sorted(loci_id_by_name):
            locus_pos = loci_id_by_name[locus_name]
            locus_res = curr_report.loci[locus_pos].results[method_name]
            row.extend([
                expected[locus_name],  # expected
                locus_res.status,  # observed
                locus_res.score,  # score
                locus_res.data["lengths"].getCount()  # support
            ])
        dataset_res.append(row)
    return dataset_res


def getDatasetsInfoTitles(loci_id_by_name):
    """
    Return titles for datasets dataframe.

    :param loci_id_by_name: List of locus names.
    :type loci_id_by_name: dict
    :return: Titles for datasets dataframe.
    :rtype: list
    """
    titles = ["dataset_id", "dataset_md5"]
    # Train dataset
    titles.extend(["train_nb_spl", "train_nb_spl_stable", "train_nb_spl_unstable", "train_nb_spl_undetermined"])
    for locus_name in sorted(loci_id_by_name):
        titles.extend([
            "train_nb_" + locus_name + "_stable",
            "train_nb_" + locus_name + "_unstable",
            "train_nb_" + locus_name + "_undetermined"
        ])
    # titles.append("learn_exec_time")
    # Test dataset
    titles.extend(["test_nb_spl", "test_nb_spl_stable", "test_nb_spl_unstable", "test_nb_spl_undetermined"])
    for locus_name in sorted(loci_id_by_name):
        titles.extend([
            "test_nb_" + locus_name + "_stable",
            "test_nb_" + locus_name + "_unstable",
            "test_nb_" + locus_name + "_undetermined"
        ])
    # titles.append("tag_exec_time")
    # Samples
    titles.extend(["train_samples", "test_samples"])
    return titles


def getDatasetsInfo(dataset_id, dataset_md5, loci_id_by_name, train_samples, test_samples, status_by_spl):
    """
    Return rows for datasets dataframe.

    :param dataset_id: Dataset ID.
    :type dataset_id: str
    :param dataset_md5: Checksum of the trainning samples indexes.
    :type dataset_md5: str
    :param loci_id_by_name: List of locus names.
    :type loci_id_by_name: dict
    :param reports: List of MSISample classified.
    :type reports: list
    :param learn_log: Logging information from MIAmS_learn.
    :type learn_log: dict
    :param tag_log: Logging information from MIAmS_tag.
    :type tag_log: dict
    :param status_by_spl: Status by locus by sample name.
    :type status_by_spl: dict
    :return: Rows for datasets dataframe.
    :rtype: list
    """
    train_status = [status_by_spl[spl] for spl in train_samples]
    test_status = [status_by_spl[spl] for spl in test_samples]
    row = [dataset_id, dataset_md5]
    # Train dataset
    spl_status = [spl_status["sample"] for spl_status in train_status]
    row.extend([
        len(train_samples),
        spl_status.count("MSS"),
        spl_status.count("MSI"),
        spl_status.count("Undetermined")
    ])
    for locus_name in sorted(loci_id_by_name):
        locus_status = [spl_status[locus_name] for spl_status in train_status]
        row.extend([
            locus_status.count("MSS"),
            locus_status.count("MSI"),
            locus_status.count("Undetermined")
        ])
    # row.append(learn_log["End_time"] - learn_log["Start_time"])
    # Test dataset
    spl_status = [spl_status["sample"] for spl_status in test_status]
    row.extend([
        len(test_samples),
        spl_status.count("MSS"),
        spl_status.count("MSI"),
        spl_status.count("Undetermined")
    ])
    for locus_name in sorted(loci_id_by_name):
        locus_status = [spl_status[locus_name] for spl_status in test_status]
        row.extend([
            locus_status.count("MSS"),
            locus_status.count("MSI"),
            locus_status.count("Undetermined")
        ])
    # row.append(tag_log["End_time"] - tag_log["Start_time"])
    # Samples
    row.extend([
        ", ".join(train_samples),
        ", ".join(test_samples)
    ])
    return row


def getMSISamples(in_folder, samples):
    """
    Return MSIReport from data output folder of MIAmS_tag.

    :param in_folder: Path to the data output folder of MIAmS_tag.
    :type in_folder: str
    :return: List of MSISample objects.
    :rtype: list
    """
    samples_res = list()
    for spl_name in samples:
        filepath = os.path.join(in_folder, "report", "data", spl_name + "_stabilityStatus.json")
        samples_res.append(ReportIO.parse(filepath)[0])
    return samples_res


class ClfAction(argparse.Action):
    """Manage classifiers parameter to convert in list of dict."""

    @staticmethod
    def parsed(classifiers):
        new_classifiers = []
        for curr_clf in classifiers:
            struct_clf = {
                "name": curr_clf,
                "class": curr_clf,
                "params": ""
            }
            if curr_clf.startswith("RandomForest:"):
                struct_clf["class"] = "RandomForest"
                n_estimators = curr_clf.split(":")[1]
                struct_clf["params"] = '{"n_estimators": ' + n_estimators + '}'
            new_classifiers.append(struct_clf)
        return new_classifiers

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, ClfAction.parsed(values))


########################################################################
#
# MAIN
#
########################################################################
if __name__ == "__main__":
    # Manage parameters
    parser = argparse.ArgumentParser(description="Launch classification on evaluation datasets.")
    parser.add_argument('-i', '--start-dataset-id', type=int, default=0, help="This option allow you to skip the n first test. [Default: %(default)s]")
    parser.add_argument('-n', '--nb-tests', type=int, default=100, help="The number of couple of test and train datasets created from the original dataset. [Default: %(default)s]")
    parser.add_argument('-a', '--test-ratio', type=float, default=0.4, help="The sample ratio for testing versus samples for learning. [Default: %(default)s]")
    clf_dflt = ["SVC", "RandomForest:10", "RandomForest:50"]
    parsed_clf_dflt = ClfAction.parsed(clf_dflt)
    parser.add_argument('-c', '--classifiers', default=parsed_clf_dflt, nargs='+', action=ClfAction, help="Classifiers evaluates (example: DecisionTree, KNeighbors, LogisticRegression, RandomForest, RandomForest:n). [Default: {}]".format(clf_dflt))
    parser.add_argument('-v', '--version', action='version', version=__version__)
    # Loci classification
    group_loci = parser.add_argument_group('Loci classification')
    group_loci.add_argument('--padding', default=[2], nargs='+', type=int, help='Minimum number of nucleotids aligned on each side around the microsatellite to take read into account. This parameter is used to skip reads containing an incomplete microsatellite. [Default: %(default)s]')
    group_loci.add_argument('--duplicates', default=["without"], nargs='+', choices=["with", "without"], help='Duplicates reads are taking into account in lengths distribution ("with"). [Default: %(default)s]')
    group_loci.add_argument('--stitching', default=["without"], nargs='+', choices=["with", "without"], help='Reads pair is taking account if the length of repeat is the same on two mates (one count). Otherwise, reads are not take into account. [Default: %(default)s]')
    group_loci.add_argument('-t', '--tag-min-support-reads', default=[50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170], nargs='+', type=int, help='The minimum numbers of reads for determine the status. [Default: %(default)s]')
    group_loci.add_argument('-e', '--learn-min-support-reads', default=100, type=int, help='The minimum numbers of reads for use loci in learning step. [Default: %(default)s]')
    # Sample classification
    group_spl = parser.add_argument_group('Sample classification')
    group_spl.add_argument('--consensus-method', default='ratio', choices=['count', 'majority', 'ratio'], help='Method used to determine the sample status from the loci status. Count: if the number of unstable is upper or equal than instability-count the sample will be unstable otherwise it will be stable ; Ratio: if the ratio of unstable/determined loci is upper or equal than instability-ratio the sample will be unstable otherwise it will be stable ; Majority: if the ratio of unstable/determined loci is upper than 0.5 the sample will be unstable, if it is lower than stable the sample will be stable. [Default: %(default)s]')
    group_spl.add_argument('--min-voting-loci', default=4, type=int, help='Minimum number of voting loci (stable + unstable) to determine the sample status. If the number of voting loci is lower than this value the status for the sample will be undetermined. [Default: %(default)s]')
    group_spl.add_argument('--instability-ratio', default=0.33, type=float, help='[Only with consensus-method = ratio] If the ratio unstable/(stable + unstable) is superior than this value the status of the sample will be unstable otherwise it will be stable. [Default: %(default)s]')
    group_spl.add_argument('--instability-count', default=3, type=int, help='[Only with consensus-method = count] If the number of unstable loci is upper or equal than this value the sample will be unstable otherwise it will be stable. [Default: %(default)s]')
    # Sample classification score
    group_score = parser.add_argument_group('Sample prediction score')
    group_score.add_argument('--undetermined-weight', default=0.0, type=float, help='[Used for all the classifiers different from MSINGS] The weight of undetermined loci in sample prediction score calculation. [Default: %(default)s]')
    group_score.add_argument('--locus-weight-is-score', action='store_true', help='[Used for all the classifiers different from MSINGS] Use the prediction score of each locus as wheight of this locus in sample prediction score calculation. [Default: %(default)s]')
    # Inputs
    group_input = parser.add_argument_group('Inputs')
    group_input.add_argument('-d', '--data-folder', required=True, help="The folder containing data to process. It must aln/, targets.bed and status_annot.tsv.")
    group_input.add_argument('-w', '--work-folder', default=os.getcwd(), help="The working directory. [Default: %(default)s]")
    # Outputs
    group_output = parser.add_argument_group('Outputs')
    group_output.add_argument('-r', '--results-path', default="results.tsv", help='Path to the output file containing the description of the results and expected value for each samples in each datasets (format: TSV). [Default: %(default)s]')
    group_output.add_argument('-s', '--datasets-path', default="datasets.tsv", help='Path to the output file containing the description of the datasets (format: TSV). [Default: %(default)s]')
    args = parser.parse_args()

    # Parameters
    aln_folder = os.path.join(args.data_folder, "aln")
    annotation_path = os.path.abspath(os.path.join(args.data_folder, "status.tsv"))
    targets_path = os.path.abspath(os.path.join(args.data_folder, "targets.bed"))
    test_cfg_tpl_path = os.path.join(args.data_folder, "cfg_tag.yml")
    train_cfg_tpl_path = os.path.join(args.data_folder, "cfg_learn.yml")
    if not os.path.exists(args.work_folder):
        os.makedirs(args.work_folder)

    # Logger
    logging.basicConfig(format='%(asctime)s -- [%(filename)s][pid:%(process)d][%(levelname)s] %(message)s')
    log = logging.getLogger()
    log.setLevel(logging.INFO)
    log.info("Command: " + " ".join(sys.argv))

    # Load data
    librairies = getLibFromDataFolder(aln_folder)
    status_by_spl = getStatus(annotation_path, [lib["name"] for lib in librairies])
    for lib in librairies:
        lib["status"] = status_by_spl[lib["name"]]
    loci_id_by_name = {
        locus.name: "{}:{}-{}".format(locus.chrom, locus.start - 1, locus.end)
        for locus in getAreas(targets_path)
    }

    # Process assessment
    cv = ShuffleSplit(n_splits=args.nb_tests, test_size=args.test_ratio, random_state=42)
    dataset_id = 0
    ordered_spl_names = sorted(list(set(lib["name"] for lib in librairies)))  # All replicates of one sample will be managed in same content (train or test)
    for train_idx, test_idx in cv.split(ordered_spl_names, groups=[status_by_spl[spl_name]["sample"] for spl_name in ordered_spl_names]):
        dataset_md5 = hashlib.md5(",".join(map(str, train_idx)).encode('utf-8')).hexdigest()
        if args.start_dataset_id > dataset_id:
            log.info("Skip already processed dataset {}/{} ({}).".format(dataset_id, args.nb_tests - 1, dataset_md5))
        else:
            log.info("Start processing dataset {}/{} ({}).".format(dataset_id, args.nb_tests - 1, dataset_md5))
            # File mode
            use_header = False
            out_mode = "a"
            if dataset_id == 0:
                use_header = True
                out_mode = "w"
            # Temp file
            train_out_folder = os.path.join(args.work_folder, "learn_out_dataset-{}".format(dataset_id))
            test_out_folder = os.path.join(args.work_folder, "tag_out_dataset-{}".format(dataset_id))
            # Create dataset
            train_names = {spl_name for idx, spl_name in enumerate(ordered_spl_names) if idx in train_idx}
            test_names = {spl_name for idx, spl_name in enumerate(ordered_spl_names) if idx in test_idx}
            train_samples = [lib for lib in librairies if lib["name"] in train_names]  # Select all libraries corresponding to the train samples
            test_samples = [lib for lib in librairies if lib["name"] in test_names]  # Select all libraries corresponding to the test samples
            datasets_df_rows = [
                getDatasetsInfo(
                    dataset_id,
                    dataset_md5,
                    loci_id_by_name,
                    test_names,
                    train_names,
                    status_by_spl
                )
            ]
            datasets_df = pd.DataFrame.from_records(datasets_df_rows, columns=getDatasetsInfoTitles(loci_id_by_name))
            with open(args.datasets_path, out_mode) as FH_out:
                datasets_df.to_csv(FH_out, header=use_header, sep='\t')
            for (padding, stitching, duplicates) in product(args.padding, args.stitching, args.duplicates):
                # Train
                train(train_samples, train_out_folder, train_cfg_tpl_path, annotation_path, targets_path, padding, args.learn_min_support_reads, stitching, duplicates, log)
                # Predict
                for clfier_idx, clf in enumerate(args.classifiers):
                    for min_support in args.tag_min_support_reads:
                        model_path = os.path.abspath(os.path.join(train_out_folder, "microsat", "microsatModel.json"))
                        predict(test_samples, test_out_folder, test_cfg_tpl_path, targets_path, model_path, clf, padding, min_support, stitching, duplicates, log)
                        reports = getMSISamples(test_out_folder, test_names)
                        res_df_rows = getMethodResInfo(
                            dataset_id,
                            clf["name"],
                            padding,
                            min_support,
                            stitching,
                            duplicates,
                            loci_id_by_name,
                            reports,
                            status_by_spl,
                            clf["class"]
                        )
                        if clfier_idx == 0:
                            res_df_rows.extend(
                                getMethodResInfo(
                                    dataset_id,
                                    "mSINGSUp",
                                    padding,
                                    min_support,
                                    stitching,
                                    duplicates,
                                    loci_id_by_name,
                                    reports,
                                    status_by_spl,
                                    "mSINGSUp"
                                )
                            )
                            res_df_rows.extend(
                                getMethodResInfo(
                                    dataset_id,
                                    "MSIsensor-pro_pro",
                                    padding,
                                    min_support,
                                    stitching,
                                    duplicates,
                                    loci_id_by_name,
                                    reports,
                                    status_by_spl,
                                    "MSIsensor-pro_pro"
                                )
                            )
                        with open(args.results_path, out_mode) as FH_out:
                            res_df = pd.DataFrame.from_records(res_df_rows, columns=getResInfoTitles(loci_id_by_name))
                            res_df.to_csv(FH_out, header=use_header, sep='\t')
                        use_header = False
                        out_mode = "a"
                        shutil.rmtree(test_out_folder)
                shutil.rmtree(train_out_folder)
        # Next dataset
        dataset_id += 1
    log.info("End of job")
