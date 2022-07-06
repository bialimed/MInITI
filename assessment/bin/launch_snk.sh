#!/bin/bash
wf=$1
config=$2
out=$3

assessment_bin_dir=`dirname $0`
assessment_bin_dir=`realpath ${assessment_bin_dir}`
assessment_dir=`dirname ${assessment_bin_dir}`
application_dir=`dirname ${assessment_dir}`

unset PYTHONPATH && export DRMAA_LIBRARY_PATH=$SGE_ROOT/lib/linux-rhel7-x64/libdrmaa.so && \
source /Anapath/soft/conda/current/bin/activate miniti && \
snakemake \
--printshellcmds \
--jobs 100 \
--latency-wait 240 \
--restart-times 2 \
--drmaa " -V -q normal -l h_vmem={cluster.vmem} -pe smp {cluster.threads} -l pri_normal=1" \
--cluster-config ${application_dir}/config/cluster.json \
--use-conda --conda-prefix /Anapath/soft/conda/current/envs \
--snakefile ${application_dir}/$wf \
--configfile $config \
--directory $out \
> $out/wf_log.txt \
2> $out/wf_stderr.txt
