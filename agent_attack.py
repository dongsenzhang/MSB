import os
import yaml
import argparse
import subprocess
import sys

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Load YAML config file')
    parser.add_argument('--cfg_path', type=str, required=True,
                        help='Path to the YAML configuration file')
    args = parser.parse_args()

    with open(args.cfg_path, 'r') as file:
        cfg = yaml.safe_load(file)

    attack_types = cfg["attack_type"]
    attack_tasks = cfg.get("attack_task", None)
    llms = cfg.get("llms", None)
    agents = cfg.get('agents', None)

    python_exe = sys.executable

    processes = []

    for attack_type in attack_types:
        for attack_task in attack_tasks:
            for llm in llms:
                for agent in agents:
                    cmd_title = f'{attack_type}#{llm}#{attack_task}#{agent}'
                    print(f'[LAUNCH] {cmd_title}')

                    cmd = [
                        python_exe, "main.py",
                        "--attack_type", str(attack_type),
                        "--attack_task", str(attack_task),
                        "--llm", str(llm),
                        "--agent", str(agent),
                    ]

                    p = subprocess.Popen(cmd)
                    processes.append((cmd_title, p))

    for title, p in processes:
        ret = p.wait()
        print(f'[FINISH] {title} exit code = {ret}')
