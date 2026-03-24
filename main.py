import asyncio
import json
from dotenv import load_dotenv
from mcp_use import MCPAgent, MCPClient
import mcp_use
from data.prompt_template import SYSTEM_PROMPT_TEMPLATE, PROMPT_INJECTION_TEMPLATE, TOOL_RESPONSE_ATTACK_TEMPLATE, SIMULATED_USER_TEMPLATE
import logging
from langchain_deepseek import ChatDeepSeek
import argparse
import pandas as pd
from scripts.utility import *
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama

mcp_use.set_debug(1)

def setup_logging(log_name):
    """配置全局日志设置"""
    # 创建根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)  # 设置全局最低日志级别

    # 创建文件处理器 - 写入所有日志到文件
    file_handler = logging.FileHandler(f'logs/{log_name}.log', mode='w', encoding='utf-8')
    file_handler.setLevel(logging.INFO)  # 文件记录所有级别日志

    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)

    # 清除现有处理器（避免重复记录）
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 添加处理器到根日志记录器
    root_logger.addHandler(file_handler)

def tool_exist(attack_type, agent_name, tool_name):
    # 检查server是否存在
    if agent_name=='image_generation':
        return False
    server_dir_path = os.path.join('data', 'tools', 'attack_tools', agent_name)
    if not os.path.exists(server_dir_path):
        return False
    server_list = os.listdir(server_dir_path)
    if tool_name not in server_list:
        return False

    return True

def complete_server_config(agent_name, tool_name, attack_type, attack_task, operation_info):
    combination_dict = {}

    # 支撑工具配置
    if attack_type not in ['out_of_scope_parameter', 'tool_transfer', 'preference_manipulation-out_of_scope_parameter'] or attack_type=='search_term_deception':
        if attack_task=='kill_process':
            support_server = 'Desktop_Commander.json'
        else:
            support_server = 'Filesystem_MCP_Server.json'
        with open(os.path.join("data", 'tools', 'support_tools', support_server), 'r') as fs:
            support_config = json.load(fs)
        combination_dict.update(support_config['mcpServers'])

    # 无害工具配置
    if attack_type not in ['out_of_scope_parameter', 'search_term_deception', 'tool_transfer']:
        with open(os.path.join("data", 'tools', 'normal_tools', f'{tool_name}.json'), 'r') as fi:
            normal_config = json.load(fi)
        combination_dict.update(normal_config['mcpServers'])

    # 有害工具配置
    if attack_type in ["name_overlap", "preference_manipulation", "out_of_scope_parameter", 'tool_transfer','preference_manipulation-out_of_scope_parameter', "preference_manipulation-simulated_user"]:
        try:
            with open(os.path.join('data', 'tools', 'attack_tools', agent_name, tool_name, 'mcp_config.json'), 'r') as f:
                attack_config = json.load(f)
        except Exception as e:
            logging.info(f'ERROR: The attack tool "{tool_name}" does not exist.')
            return None
        server_name = list(attack_config['mcpServers'].keys())[0]
        attack_config['mcpServers'][server_name]['args'].append(attack_type)
        attack_config['mcpServers'][server_name]['args'].append(attack_task)
        attack_config['mcpServers'][server_name]['args'].append(operation_info)
        py_name = attack_config['mcpServers'][server_name]['args'][3]
        attack_py_suffix = 'preference_manipulation' if attack_type=="preference_manipulation-simulated_user" else attack_type
        attack_py_name = py_name.replace('.py',f"-{attack_py_suffix}.py")
        attack_config['mcpServers'][server_name]['args'][3] = attack_py_name
        attack_config['mcpServers'][f'attack-{server_name}'] = attack_config['mcpServers'].pop(server_name)
        combination_dict.update(attack_config['mcpServers'])

        # tool_transfer和out_of_scope_parameter捆绑
        if attack_type == 'tool_transfer':
            with open(os.path.join('data', 'tools', 'attack_tools', agent_name, tool_name, 'mcp_config.json'), 'r') as f:
                addition_attack_config = json.load(f)
                addition_server_name = list(addition_attack_config['mcpServers'].keys())[0]
                addition_attack_config['mcpServers'][addition_server_name]['args'].append('out_of_scope_parameter')
                addition_attack_config['mcpServers'][addition_server_name]['args'].append(attack_task)
                addition_attack_config['mcpServers'][addition_server_name]['args'].append(operation_info)
                py_name = addition_attack_config['mcpServers'][addition_server_name]['args'][3]
                addition_attack_py_name = py_name.replace('.py', "-out_of_scope_parameter.py")
                addition_attack_config['mcpServers'][addition_server_name]['args'][3] = addition_attack_py_name
                addition_attack_config['mcpServers'][f'addition-{addition_server_name}'] = addition_attack_config['mcpServers'].pop(addition_server_name)
                combination_dict.update(addition_attack_config['mcpServers'])

    # 整合工具
    config = {'mcpServers':combination_dict}

    return config

async def run_attack(llm_name,
                     agent_name,
                     agent_system_prompt,
                     agent_task,
                     tool_name,
                     attack_task,
                     attack_type,
                     attack_implement):
    log_name = f'{attack_type}#{llm_name.replace(":","-").replace(".","").replace("/","-")}#{agent_name}#{agent_task[:20].replace(" ","_").replace(":","").replace("/","").replace(".","")}#{tool_name}#{attack_task}' #多实现需要修改
    if os.path.exists(os.path.join('logs',f'{log_name}.log')):
        return None

    operation_output_file = ''
    log_name_components = log_name.replace('-','_').split('#')
    for component in log_name_components:
        component = [c[0] if len(c)>=1 else '' for c in component.split('_')]
        component_initial = '_'.join(component)
        operation_output_file += f'{component_initial}#'
    operation_output_file = operation_output_file[:-1]
    attack_implement = attack_implement.replace('file_name',operation_output_file)

    # Load environment variables
    load_dotenv()
    os.environ['LANGSMITH_PROJECT'] = log_name

    # 配置日志
    setup_logging(log_name)
    logging.info(log_name)
    print(log_name)

    # 配置攻击任务所需的环境
    if attack_task=='modify_data':
        create_operation_file(operation_output_file)
    elif attack_task=='kill_process':
        subprocess = star_subprocess()
        subprocess_pid = subprocess.pid
        attack_implement = attack_implement.replace('{pid}', str(subprocess_pid))

    # Create MCPClient from configuration dictionary
    operation_info = operation_output_file if attack_task!='kill_process' else str(subprocess_pid)
    config = complete_server_config(agent_name, tool_name, attack_type, attack_task, operation_info)
    if config is None:
        return None
    client = MCPClient.from_dict(config)

    # Create LLM
    if any(openrouter_llm in llm_name for openrouter_llm in ['llama','gpt','gemini','claude']):
        if llm_name=='claude-sonnet-4-20250514':
            llm_name = 'anthropic/claude-sonnet-4'
        if llm_name=='gpt-5':
            llm_name = 'openai/gpt-5'
        llm = ChatOpenAI(
              api_key=os.getenv("OPENROUTER_API_KEY"),
              base_url=os.getenv("OPENROUTER_BASE_URL"),
              model=llm_name
            )
    if 'deepseek' in llm_name:
        llm = ChatDeepSeek(model=llm_name, max_retries=2)
    if 'qwen' in llm_name:
        llm = ChatTongyi(model=llm_name, streaming=True,enable_thinking=False)
        # llm = ChatOllama(model=llm_name)

    # Create system_prompt
    system_prompt = agent_system_prompt + SYSTEM_PROMPT_TEMPLATE
    tool_description_injection = True if "prompt_injection" in attack_type else False
    parameter_description_injection = True if attack_type=="prompt_injection-parameter_description" else False
    injection_content = PROMPT_INJECTION_TEMPLATE.replace('{goal}',attack_implement) if tool_description_injection or parameter_description_injection else ''

    # Create tool response attack content
    tool_response_attack = ''
    if "false_error" in attack_type:
        tool_response_attack = TOOL_RESPONSE_ATTACK_TEMPLATE + attack_implement
    if 'simulated_user' in attack_type and attack_type!='preference_manipulation-simulated_user':
        tool_response_attack = SIMULATED_USER_TEMPLATE + attack_implement
    if attack_type=='search_term_deception':
        tool_response_attack = attack_implement

    # Create agent with the client
    if attack_task == 'kill_process':
        disallowed_tools = ['get_config','set_config_value','read_multiple_files','create_directory','move_file','list_directory','start_search','get_more_search_results','stop_search','list_searches','get_file_info','edit_block','start_process','read_process_output','interact_with_process','force_terminate','list_sessions','get_usage_stats','give_feedback_to_desktop_commander']
    else:
        disallowed_tools = ['list_directory','list_directory_with_sizes','directory_tree','list_allowed_directories'] if attack_type!='search_term_deception' else None
    agent = MCPAgent(llm=llm,
                     client=client,
                     system_prompt_template=system_prompt,
                     tool_description_injection=tool_description_injection,
                     parameter_description_injection=parameter_description_injection,
                     injection_content=injection_content,
                     tool_response_attack=tool_response_attack,
                     attack_type=attack_type,
                     attack_task=attack_task,
                     max_steps=10,
                     disallowed_tools=disallowed_tools
                     )

    # Run the query
    if llm_name == 'qwen3-8b':
        agent_task+=' /no_think'
    result = await agent.run(agent_task)
    logging.info(f"\nResult: {result}")
    print(result)

    #  清理环境
    if attack_task == 'kill_process':
        record_result(subprocess,operation_output_file)





def main():
    # parse arguments and set configuration for this run accordingly
    parser = argparse.ArgumentParser(description='Load config')
    parser.add_argument('--attack_type', type=str, required=False, default='prompt_injection', help='The method of the attack implementation')
    parser.add_argument('--attack_task', type=str, required=False, default='kill_process', help='The task of attack')
    parser.add_argument('--llm', type=str, required=False, default='deepseek-chat', help='The used llm')
    parser.add_argument('--agent', type=str, required=False, default='academic_search', help='Agent scenario')
    args = parser.parse_args()

    if args.attack_type != 'all':
        attack_type_list = [args.attack_type]
    else:
        with open('data/attack_type.jsonl', 'r', encoding="utf-8") as f:
            for line in f:
                attack_type_data = json.loads(line)
        attack_type_list = attack_type_data['attack_type']
    for attack_type in attack_type_list:
        agent_task_df = pd.read_json('data/agent_task.jsonl', lines=True)
        if args.agent != 'all':
            agent_task_df = agent_task_df[agent_task_df['agent_name'] == args.agent]

        attack_tasks_df = pd.read_json('data/attack_task.jsonl', lines=True)
        if any(limit_attack_type in attack_type for limit_attack_type in ['tool_transfer','out_of_scope_parameter','preference_manipulation-out_of_scope_parameter']):
            pass
            # attack_tasks_df = attack_tasks_df.head(1)
        elif args.attack_task != 'all':
            attack_tasks_df = attack_tasks_df[attack_tasks_df['attack_task'] == args.attack_task]

        for index,agent_task_row in agent_task_df.iterrows():
            agent_name = agent_task_row['agent_name']
            agent_system_prompt = agent_task_row['system_prompt']
            agent_tasks = agent_task_row['task_tool']
            if (agent_name=='information_retrieval' and attack_type!='search_term_deception') or (agent_name!='information_retrieval' and attack_type=='search_term_deception'):
                continue
            for agent_task_tool in agent_tasks:
                agent_task = agent_task_tool['task']
                tool_name = agent_task_tool['tool']

                if any(restrict_attack_type in attack_type for restrict_attack_type in ['tool_transfer', 'name_overlap', 'out_of_scope_parameter', 'preference_manipulation']) and not tool_exist(args.attack_type, agent_name, tool_name):
                    continue
                for ind,attack_task_row in attack_tasks_df.iterrows():
                    attack_task = attack_task_row['attack_task']
                    attack_implement = attack_task_row['implementation']  # 多实现需要修改
                    asyncio.run(run_attack(
                        llm_name = args.llm,
                        agent_name = agent_name,
                        agent_system_prompt = agent_system_prompt,
                        agent_task = agent_task,
                        tool_name = tool_name,
                        attack_task = attack_task,
                        attack_type = attack_type,
                        attack_implement = attack_implement
                    ))


if __name__ == "__main__":
    main()
