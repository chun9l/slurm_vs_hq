import json
import os 
import subprocess
from dateutil import parser
import pickle
import glob
import re

def extract_times(run_dir, run_name):
    data = {}
    job_count = 0
    with open(f"{run_dir}/{run_name}_slurm_um.json", "r") as h:
        json_data = json.load(h)
    for i in json_data:
        job = json_data[i]["jobs"][0]
        job_id = job["job_id"]
        cpu_cores = int(job["required"]["CPUs"])
        submit = job["time"]["submission"]
        start = job["time"]["start"]
        end = job["time"]["end"]
        if len(job["steps"]) == 2:
            batch = job["steps"][0]["time"]["total"]["seconds"] + job["steps"][0]["time"]["total"]["microseconds"] / 1e6
            extern = job["steps"][1]["time"]["total"]["seconds"] + job["steps"][1]["time"]["total"]["microseconds"] / 1e6
            job_steps = (batch + extern)
            if job_count >= 5:
                job_steps = job_steps / cpu_cores
        else:
            raise Exception("Incorrect job steps")
        makespan = end - submit
        if makespan == 0:
            makespan += job_steps
            lag = 0
        else: 
            lag = end - submit - job_steps
        slr = makespan / job_steps
        try:
            data[str(i)] = {"makespan": makespan, "cpu-time": job_steps, "lag": lag, "slr": slr}
        except:
            print(job_id, submit, start, end, job_steps)
        job_count += 1

    with open(f"{run_dir}/{run_name}_slurm_um.pkl", "wb") as h:
        pickle.dump(data, h)


def create_json(run_dir, run_name):
    if os.path.isfile(f"{run_dir}/{run_name}_slurm_um.json"):
        print(f"{run_name}_slurm_um.json exists! Skipping json creation")
    else:
        main_dir = f"{run_dir}/{run_name}"

        json_dict = {}
        iteration = 0
        for slurm_output in sorted(glob.glob(main_dir + os.sep + "slurm*.out")):
            job_id = int(re.split("slurm-(\d+)", slurm_output)[1])
            cmd = ["sacct", "-j", str(job_id), "--json"]
            output = subprocess.run(cmd, stdout=subprocess.PIPE)
            # search for the batch step in the json for microsecond. submit still same
            json_data = json.loads(output.stdout.decode("utf-8"))
            json_dict[str(iteration)] = json_data
            iteration += 1
        with open(f"{run_dir}/{run_name}_slurm_um.json", "w") as h:
            h.write(json.dumps(json_dict))

run_dir = "../../results/raw_data/umbridge/slurm_um/10jobs"
run_name = "gs2"

create_json(run_dir, run_name)
extract_times(run_dir, run_name)
