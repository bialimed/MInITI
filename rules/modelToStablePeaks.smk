__author__ = 'Frederic Escudie'
__copyright__ = 'Copyright (C) 2024 CHU Toulouse'
__license__ = 'GNU General Public License'
__version__ = '1.0.0'


def modelToStablePeaks(
        in_model="microsat/microsatModel.json",
        out_stable_peaks="microsat/stable_model_peaks.json",
        out_stderr="logs/modelToStablePeaks_stderr.txt",
        params_model_min_support=None,
        params_keep_outputs=False,
        params_stderr_append=False):
    """Extract most represented lengths by locus from stable microsatellites model."""
    rule modelToStablePeaks:
        input:
            in_model
        output:
            out_stable_peaks if params_keep_outputs else temp(out_stable_peaks)
        log:
            out_stderr
        params:
            bin_path = os.path.abspath(os.path.join(workflow.basedir, "scripts/modelToStablePeaks.py")),
            model_min_support = "" if params_model_min_support is None else "--min-support {}".format(params_model_min_support)
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
