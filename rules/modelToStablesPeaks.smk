__author__ = 'Frederic Escudie'
__copyright__ = 'Copyright (C) 2024 CHU Toulouse'
__license__ = 'GNU General Public License'
__version__ = '1.0.0'


def modelToStablesPeaks(
        in_model="microsat/microsatModel.json",
        out_stables_peaks="microsat/model_stablesPeaks.json",
        out_stderr="logs/{sample}_modelToStablesPeaks_stderr.txt",
        params_model_min_support=None,
        params_keep_outputs=False,
        params_stderr_append=False):
    """Extract stable microsatellites most represented length by locus from model."""
    rule modelToStablesPeaks:
        input:
            in_model
        output:
            out_stables_peaks if params_keep_outputs else temp(out_stables_peaks)
        log:
            out_stderr
        params:
            bin_path = os.path.abspath(os.path.join(workflow.basedir, "scripts/modelToStablesPeaks.py")),
            model_min_support = "" if params_model_min_support is None else "--min-support {}".format(params_model_min_support),
        resources:
            extra = "",
            mem = "2G",
            partition = "normal"
        threads: 1
        shell:
            "{params.bin_path}"
            " {params.min_support}"
            " --input-model {input}"
            " --output-peaks {output}"
            " {params.stderr_redirection} {log}"
