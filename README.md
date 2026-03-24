# MCP Security Bench (MSB): Benchmarking Attacks Against Model Context Protocol in LLM Agents

This is the official code for the ICLR 2026 paper [MCP Security Bench (MSB): Benchmarking Attacks Against Model Context Protocol in LLM Agents](https://openreview.net/pdf?id=irxxkFMrry). The MCP Security Bench (MSB) is an end-to-end evaluation suite that systematically measures how well LLM agents resist MCP-specific attacks throughout the full tool-use pipeline: task planning, tool invocation, and response handling. It comprises more than 2,000 attack instances across 12 attack categories.

##  <img src="https://github.com/user-attachments/assets/81bed977-5250-4569-8457-52f4e8a82480" width="30" style="vertical-align: middle;"> MCP-specific Attacking Framework

<div align="center">
  <img src="./images/Framework.png" width="100%">
</div>

The MCP-specific attacking framework includes **Tool Signature Attack, Tool Parameters Attack, Tool Response Attack**, and **Retrieval Injection Attack**, which cover the full tool-use pipeline stages: task planning, tool calling and response handling.

## <img src="https://github.com/user-attachments/assets/6f9860cd-c31f-4930-8266-57eb69aee14b" width="30" style="vertical-align: middle;"> Getting Started

The development of MSB is based on [mcp-use](https://github.com/mcp-use/mcp-use/tree/1.3.7?tab=readme-ov-file)=1.3.7.

### Environment Installation

1. Git clone MSB
   
   ```
   git clone https://github.com/dongsenzhang/MSB.git
   ```

2. Install the dependencies

    ```
    conda create -n MSB python=3.11
    source activate MSB
    cd MSB
    pip install -r requirements.txt
    ```

3. Install uv and dependencies
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
    ```
   cd data/tools/attack_tools

    # Create virtual environment and activate it
    uv venv
    source .venv/bin/activate

    # Install dependencies
    uv add --requirements requirements.txt
   ```
4. Setup
    ```
    cd MSB
   python setup.py
   ```

### Use With LangChain

MSB works with various LLM providers through LangChain, check the [LangChain chat models documentation](https://docs.langchain.com/oss/python/integrations/providers/overview) and add your API keys for the provider you want to use to your `.env` file. You can spin up LLM in `main.py`. For example:

```
from langchain_openai import ChatOpenAI
# Create LLM
llm = ChatOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL"),
                model=llm_name
                )
```

### Quickstart

The `config/` directory contains YAML file that outlines the specific argument settings for each configuration.

```
python agent_attack.py --cfg_path config/all.yml # All attacks
```

### Customizable Arguments

The customizable arguments are stored in YAML files in `config/`. Please list the arguments you want to evaluate in a run. For example, if you want to run GPT-4o-mini and Qwen3 8B at the same time, you should set llms in the following format in YAML files.

```
llms:
  - qwen3-8b
  - openai/gpt-4o-mini
```


### Attack Types

Here are the yaml arguments representation for the agent `attack_type`.


|        **Attack Types**        |            **Attack**            |                  **YAML Argument**                 | **Remarks**                                |
|:--------------------------:|:----------------------------:|:----------------------------------------------:|----------------------------------------|
|    Tool Signature Attack   |      Name Collision (**NC**)     |                  name_overlap                  | Default to be combined with FE: **NC-FE**. |
|    Tool Signature Attack   | Preference Manipulation (**PM**) |             preference_manipulation            | Default to be combined with FE: **PM-FE**. |
|    Tool Signature Attack   |     Prompt Injection (**PI**)    |                prompt_injection                |                                        |
|   Tool Parameters Attack   |  Out-of-Scope Parameter (**OP**) |             out_of_scope_parameter             |                                        |
|    Tool Response Attack    |    User Impersonation (**UI**)   |                 simulated_user                 |                                        |
|    Tool Response Attack    |       False Error (**FE**)       |                   false_error                  |                                        |
|    Tool Response Attack    |      Tool Transfer (**TT**)      |                  tool_transfer                 | Default to be combined with OP: **TT-OP**. |
| Retrieval Injection Attack |   Retrieval Injection (**RI**)   |              search_term_deception             |                                        |
|        Mixed Attack        |             **PI-UI**            |         prompt_injection-simulated_user        |                                        |
|        Mixed Attack        |             **PI-FE**            |          prompt_injection-false_error          |                                        |
|        Mixed Attack        |             **PM-UI**            |     preference_manipulation-simulated_user     |                                        |
|        Mixed Attack        |             **PM-OP**            | preference_manipulation-out_of_scope_parameter |                                        |

### Metrics

The `logs/` record the complete process of the agent's task execution, while `operation_space/output` records the environmental state within the workspace. `metrics.py` calculates metrics by analyzing both of these sources.

```
python metrics.py --attack_type all --attack_task all --llm all --agent all --mode llm
```

The evaluation results output by `metrics.py` are located in the `data/` directory.

### Other Customizable Agruments

```
attack_type: The attack types of MCP attacks. For a detailed view, please refer to the 'data/attack_type'. 

attack_task: The task of the attack. For a detailed view, please refer to the 'data/attack_task'

llms: The LLMs to use in the evaluation.

agents: The scenario for agent operates. For a detailed view, please refer to the 'data/agent_task'

mode: Statistical dimensions of the metric.
    -- llm: LLM metrics under each attack.
    -- stage: statistics by tool invocation stage.
    -- tool: calculate metrics based on whether the tool configuration includes benign tools.
```

## <img src="https://github.com/user-attachments/assets/1f4b852e-95ef-4476-9ddb-161339ae2667" width="30" style="vertical-align: middle;"> Experimental Result

### MCP Attack

We evaluated 12 MCP attack types on 10 LLM agents, here shows the Attack Success Rate (ASR) for various attacks and LLM backbones.

| **LLM** | **PI** | **OP** | **UI** | **FE** | **RI** | **PI-UI** | **PI-FE** | **NC-FE** | **PM-FE** | **PM-UI** | **PM-OP** | **TT-OP** | **Average** |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Llama3.1 8B** | 4.92% | 46.25% | 35.08% | 19.02% | **0.00%** | 23.61% | 22.95% | 15.00% | 11.25% | 23.75% | 11.25% | 23.75% | **19.74%** |
| **Llama3.1 70B** | 4.92% | 58.75% | 42.95% | 17.05% | **0.00%** | **21.97%** | 23.61% | 17.50% | 8.75% | 28.75% | 12.50% | 43.75% | 23.37% |
| **Llama3.3 70B** | **0.00%** | 98.75% | 63.93% | 27.21% | **0.00%** | 67.54% | 66.23% | 16.25% | 18.75% | 54.43% | 76.25% | 70.00% | 46.61% |
| **Qwen3 8B** | 1.03% | 82.50% | 68.62% | 66.55% | **0.00%** | 61.03% | **22.07%** | 35.00% | 62.50% | 65.00% | 86.25% | 16.25% | 47.23% |
| **Qwen3 30B** | 2.07% | 62.50% | 34.14% | 25.86% | 15.00% | 26.21% | 26.21% | 6.25% | 41.25% | 36.25% | 41.25% | **8.75%** | 27.14% |
| **Gemini 2.5 Flash** | 52.46% | **36.25%** | 7.54% | 19.02% | **0.00%** | 63.93% | 76.39% | 12.50% | 20.00% | 6.25% | 26.25% | 42.50% | 30.26% |
| **DeepSeek-V3.1** | 18.36% | 92.50% | 65.57% | 85.25% | 75.00% | 79.67% | 77.38% | 13.75% | 55.00% | 37.50% | 55.00% | 76.25% | 60.94% |
| **Claude4 Sonnet** | 66.89% | 93.75% | 46.89% | 65.90% | 40.00% | 66.23% | 69.18% | 15.00% | 35.00% | 18.75% | 25.00% | 87.50% | 52.51% |
| **GPT-4o-mini** | 2.62% | 95.00% | 91.80% | 64.92% | 40.00% | 95.41% | 95.41% | 15.00% | 50.00% | 53.75% | **5.00%** | 93.75% | 58.56% |
| **GPT-5** | 48.85% | 98.75% | **0.33%** | **1.31%** | 30.00% | 55.08% | 49.18% | **0.00%** | **1.25%** | **0.00%** | 86.25% | 75.00% | 37.17% |
| **Average** | 20.21% | 76.50% | 45.69% | 39.21% | 20.00% | 56.07% | 52.86% | 14.62% | 30.38% | 32.44% | 42.50% | 53.75% | 40.35% |

The following figure is visual comparisons between PUA vs ASR, NRP vs ASR and NRP vs PUA.

<div align="center">
  <img src="./images/Visual_comparisons.jpg" width="100%">
</div>

### Multi-perspective results

We further compared the attack results from the perspective of (a) both the MCP pipeline stages and (b) tool configurations.

<div align="center">
  <img src="./images/Stage_tool_result.jpg" width="100%">
</div>


## License

MIT

## Citation

If you use our code or data in this repo or find our work helpful, please cite:

```
@inproceedings{
zhang2026mcp,
title={{MCP} Security Bench ({MSB}): Benchmarking Attacks Against Model Context Protocol in {LLM} Agents},
author={Dongsen Zhang and Zekun Li and Xu Luo and Xuannan Liu and Pei Pei Li and Wenjun Xu},
booktitle={The Fourteenth International Conference on Learning Representations},
year={2026},
url={https://openreview.net/forum?id=irxxkFMrry}
}
```