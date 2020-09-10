__author__ = 'Frederic Escudie'
__copyright__ = 'Copyright (C) 2020 IUCT-O'
__license__ = 'GNU General Public License'
__version__ = '1.0.0'


def microsatCreateModel(
        in_loci_status="raw/status.tsv",
        in_microsatellites="design/microsat.bed",
        in_length_distributions=None,  # ["microsat/spl1_microsatLenDistrib.json", "microsat/spl2_microsatLenDistrib.json"]
        out_info="microsat/microsatModel_info.tsv",
        out_model="microsat/microsatModel.json",
        out_stderr="logs/microsatCreateModel_stderr.txt",
        params_min_support=None,
        params_keep_output=False,
        params_stderr_append=False):
    """Create training data for MSI classifiers."""
    rule microsatCreateModel:
        input:
            loci_status = in_loci_status,
            microsatellites = in_microsatellites,
            length_distributions = in_length_distributions,
        output:
            info = out_info if params_keep_output else temp(out_info),
            model = out_model if params_keep_output else temp(out_model)
        log:
            out_stderr
        params:
            bin_path = "microsatCreateModel.py",
            min_support = "" if params_min_support is None else "--min-support {}".format(params_min_support),
            stderr_redirection = "2>" if not params_stderr_append else "2>>"
        conda:
            "envs/anacore-utils.yml"
        shell:
            "{params.bin_path}"
            " {params.min_support}"
            " --input-loci-status {input.loci_status}"
            " --input-microsatellites {input.microsatellites}"
            " --inputs-length-distributions {input.length_distributions}"
            " --output-info {output.info}"
            " --output-model {output.model}"
            " {params.stderr_redirection} {log}"
