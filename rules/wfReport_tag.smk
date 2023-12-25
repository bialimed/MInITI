__author__ = 'Frederic Escudie'
__copyright__ = 'Copyright (C) 2020 IUCT-O'
__license__ = 'GNU General Public License'
__version__ = '1.0.0'


def wfReport(
        in_model,
        params_samples_names,
        in_classification="microsat/{sample}_stabilityStatus.json",
        in_resources_folder=None,
        out_run_report="report/run.html",
        out_spl_reports="report/{sample}.html",
        out_stderr_cpRsc="logs/reportCpReportResources_stderr.txt",
        out_stderr_run="logs/reportRun_stderr.txt",
        out_stderr_spl="logs/report{sample}_stderr.txt",
        params_classification_method_name=None,
        params_data_method_name="alnLength"):
    """Write samples and run reports."""
    # Copy web resources
    if in_resources_folder is None:
        in_resources_folder = os.path.abspath(os.path.join(workflow.basedir, "report_resources"))
    out_report_folder = os.path.dirname(out_spl_reports)
    out_resources_folder = os.path.join(out_report_folder, "resources")
    rule cpReportResources:
        input:
            in_resources_folder
        output:
            directory(out_resources_folder)
        log:
            out_stderr_cpRsc
        params:
            report_dir = out_report_folder
        resources:
            mem = "1G",
            partition = "normal"
        threads: 1
        shell:
            "mkdir -p {params.report_dir} && cp -r {input} {output}"
            " 2> {log}"
    # Create sample report
    rule wfSplReport:
        input:
            classification = in_classification,
            lib = out_resources_folder,  # Not input but necessary to output
            model = in_model
        output:
            out_spl_reports
        log:
            out_stderr_spl
        params:
            bin_path = os.path.abspath(os.path.join(workflow.basedir, "scripts/wfSplReport.py")),
            data_method_name = "" if params_data_method_name is None else "--data-method-name {}".format(params_data_method_name),
            sample = " --sample-name {sample}"
        resources:
            mem = "3G",
            partition = "normal"
        threads: 1
        conda:
            "envs/anacore-utils.yml"
        shell:
            "{params.bin_path}"
            " {params.sample}"
            " {params.data_method_name}"
            " --input-model {input.model}"
            " --input-report {input.classification}"
            " --output-report {output}"
            " 2> {log}"
    # Create run report
    rule wfRunReport:
        input:
            expand(in_classification, sample=params_samples_names)
        output:
            out_run_report
        log:
            out_stderr_run
        params:
            bin_path = os.path.abspath(os.path.join(workflow.basedir, "scripts/wfRunReport.py")),
            classification_method_name = "" if params_classification_method_name is None else "--classification-method-name {}".format(params_classification_method_name)
        resources:
            mem = "2G",
            partition = "normal"
        threads: 1
        conda:
            "envs/anacore-utils.yml"
        shell:
            "{params.bin_path}"
            " {params.classification_method_name}"
            " --inputs-report {input}"
            " --output-report {output}"
            " 2> {log}"
