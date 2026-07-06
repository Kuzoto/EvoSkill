#!/bin/bash
#SBATCH --job-name=evoskill-reset
#SBATCH --time=00:10:00
#SBATCH --partition=normal_q
#SBATCH --output=job-outputs/reset-%j.out
#SBATCH --error=job-outputs/reset-%j.err
#SBATCH --mem=4G

cd "$SLURM_SUBMIT_DIR"

if [ -f .env ]; then
    set -a; source .env; set +a
fi

export PATH="$HOME/.local/bin:$HOME/.npm-global/bin:$HOME/.opencode/bin:$PATH"
export PYTHONPATH=$PYTHONPATH:$SLURM_SUBMIT_DIR
export PYTHONUNBUFFERED=1
unset CLAUDECODE

mkdir -p job-outputs

echo "Running evoskill reset..."
yes | uv run evoskill reset "$@"

echo "Job complete."
