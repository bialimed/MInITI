#!/bin/bash

# Parameters
if [ "$#" -eq 0 ]; then
    echo -e "[\033[0;31mERROR\033[0m] The working directory must be provided: $0 CONDA_ENVS_DIR WORK_DIR 'CLUSTER_SUBMISSION'"
    exit 1
elif [ "$#" -ne 3 ] && [ "$#" -ne 4 ]; then
    echo -e "[\033[0;31mERROR\033[0m] Illegal number of parameters"
    exit 1
fi
conda_envs_dir=$1
work_dir=$2
cluster_submission=$3
nb_threads=2
if [ "$#" -eq 4 ]; then
    nb_threads=$4
fi
test_dir=`dirname $0`
test_dir=`realpath ${test_dir}`
application_dir=`dirname ${test_dir}`

# Process learn
mkdir -p ${work_dir}/learn && \
cp -r ${application_dir}/test/raw ${work_dir}/learn/raw && \
cp -r ${application_dir}/test/config ${work_dir}/learn/config && \
snakemake \
  --use-conda \
  --conda-prefix ${conda_envs_dir} \
  --jobs ${nb_threads} \
  --jobname "miniti.{rule}.{jobid}" \
  --latency-wait 200 \
  --cluster "${cluster_submission}" \
  --snakefile ${application_dir}/Snakefile_learn \
  --configfile ${work_dir}/learn/config/wf_learn_config.yml \
  --directory ${work_dir}/learn \
  2> ${work_dir}/learn/wf_stderr.txt

  # Check execution
  if [ $? -ne 0 ]; then
      echo -e "[\033[0;31mERROR\033[0m] Workflow execution error (log: ${work_dir}/learn/wf_stderr.txt)"
      exit 1
  fi

# Process tag
mkdir -p ${work_dir}/tag && \
cp -r ${application_dir}/test/raw ${work_dir}/tag/raw && \
cp -r ${application_dir}/test/config ${work_dir}/tag/config && \
snakemake \
  --use-conda \
  --conda-prefix ${conda_envs_dir} \
  --jobs ${nb_threads} \
  --jobname "miniti.{rule}.{jobid}" \
  --latency-wait 200 \
  --cluster "${cluster_submission}" \
  --snakefile ${application_dir}/Snakefile_tag \
  --configfile ${work_dir}/tag/config/wf_tag_config.yml \
  --directory ${work_dir}/tag \
  2> ${work_dir}/tag/wf_stderr.txt

# Check execution
if [ $? -ne 0 ]; then
    echo -e "[\033[0;31mERROR\033[0m] Workflow execution error (log: ${work_dir}/tag/wf_stderr.txt)"
    exit 1
fi

# End of test
echo "Workflow execution success"
