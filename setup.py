import subprocess
import os
import langchain
import shutil

def replace_content(file_path, target_str, new_str, uv_abs_path=None):
    with open(file_path, 'r') as f:
            content = f.read()
    content = content.replace(target_str, new_str)
    if uv_abs_path is not None:
        content = content.replace('"uv"', f'"{uv_path}"')
    with open(file_path, 'w') as f:
        f.write(content)

script_dir = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(script_dir,'logs')
if not os.path.exists(log_path):
    os.mkdir(log_path)
output_path = os.path.join(script_dir,'operation_space','output')
if not os.path.exists(output_path):
    os.mkdir(output_path)
# 1. Put the full path to the uv executable
result = subprocess.run(['which', 'uv'], capture_output=True, text=True)
uv_path = result.stdout.strip()
try:
    if result.returncode != 0:
        raise FileNotFoundError("uv executable not found in PATH. Please check if UV is installed.")
except Exception as e:
    print(e)

# 2. Put the full path to the mcp config
for root, dirs, files in os.walk(os.path.join(script_dir, 'data', 'tools')):
    if 'attack_tools' in root and 'mcp_config.json' in files:
        attack_tool_path = os.path.join(root, 'mcp_config.json')
        parent_dir_abs_path = os.path.abspath(root)
        replace_content(attack_tool_path, '/ABSOLUTE/PATH/TO/PARENT/FOLDER/', parent_dir_abs_path, uv_path)

        mcp_name = os.path.basename(root)
        normal_tool_path = os.path.join(script_dir, 'data','tools','normal_tools',f'{mcp_name}.json')
        replace_content(normal_tool_path, '/ABSOLUTE/PATH/TO/PARENT/FOLDER/', parent_dir_abs_path, uv_path)


info_path = os.path.join(script_dir,'operation_space','information')
output_path = os.path.join(script_dir,'operation_space','output')
support_tool_path = os.path.join(script_dir,'data','tools','support_tools','Filesystem_MCP_Server.json')
replace_content(support_tool_path, "/ABSOLUTE/PATH/TO/operation_space/information", info_path)
replace_content(support_tool_path, "/ABSOLUTE/PATH/TO/operation_space/output", output_path)

# 3. Modify the agent configuration in langchain
langchain_path = os.path.dirname(langchain.__file__)
target_file = os.path.join(langchain_path, 'agents', 'agent.py')
src_file = os.path.join(script_dir,'scripts', 'agent.py')
if os.path.exists(src_file):
    shutil.move(src_file, target_file)

# 4. Set the path for the task
agent_task_path = os.path.join(script_dir, 'data', 'agent_task.jsonl')
replace_content(agent_task_path, "/ABSOLUTE/PATH/TO/SPACE/INFORMATION", info_path)

attack_task_path = os.path.join(script_dir, 'data', 'attack_task.jsonl')
attack_output_path = os.path.join(script_dir,'operation_space','output', 'file_name.txt')
replace_content(attack_task_path, "/ABSOLUTE/PATH/TO/SPACE/OUTPUT/FILENAME", attack_output_path)
personal_info_path = os.path.join(script_dir,'operation_space','information', 'personal_information.json')
replace_content(attack_task_path, "/ABSOLUTE/PATH/TO/SPACE/INFORMATION/PERSONAL", personal_info_path)

print("Setup completed successfully!")