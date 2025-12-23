import importlib
import json
import logging
import os
import shutil
import time
from datetime import datetime

from camel.agents import RolePlaying
from camel.configs import ChatGPTConfig
from camel.typing import TaskType, ModelType
from chatdev.chat_env import ChatEnv, ChatEnvConfig
from chatdev.statistics import get_info
from camel.web_spider import modal_trans
from chatdev.utils import log_visualize, now


def check_bool(s):
    return s.lower() == "true"


class ChatChain:

    def __init__(self,
                 config_path: str = None,
                 config_phase_path: str = None,
                 config_role_path: str = None,
                 task_prompt: str = None,
                 project_name: str = None,
                 org_name: str = None,
                 model_type: ModelType = None,
                 code_path: str = None) -> None:
        """
        参数:
            config_path: ChatChainConfig.json 的路径
            config_phase_path: PhaseConfig.json 的路径
            config_role_path: RoleConfig.json 的路径
            task_prompt: 用户输入的软件提示
            project_name: 用户输入的软件名称
            org_name: 人类用户的组织名称
        """

        # 加载配置文件
        self.config_path = config_path
        self.config_phase_path = config_phase_path
        self.config_role_path = config_role_path
        self.project_name = project_name
        self.org_name = org_name
        self.model_type = model_type
        self.code_path = code_path

        with open(self.config_path, 'r', encoding="utf8") as file:
            self.config = json.load(file)
        with open(self.config_phase_path, 'r', encoding="utf8") as file:
            self.config_phase = json.load(file)
        with open(self.config_role_path, 'r', encoding="utf8") as file:
            self.config_role = json.load(file)

        # 初始化chatchain配置和招聘
        self.chain = self.config["chain"]
        self.recruitments = self.config["recruitments"]
        self.web_spider = self.config["web_spider"]

        # 初始化默认最大聊天回合数
        self.chat_turn_limit_default = 10

        # 初始化Chatenv
        self.chat_env_config = ChatEnvConfig(clear_structure=check_bool(self.config["clear_structure"]),
                                             gui_design=check_bool(self.config["gui_design"]),
                                             git_management=check_bool(self.config["git_management"]),
                                             incremental_develop=check_bool(self.config["incremental_develop"]),
                                             background_prompt=self.config["background_prompt"],
                                             with_memory=check_bool(self.config["with_memory"]))
                                             
        self.chat_env = ChatEnv(self.chat_env_config)

        # 用户输入提示将自我改进（如果在ChatChainConfig.json中设置“self_improve”: “True”）
        # 自我改进是在 self.preprocess 中完成的。
        self.task_prompt_raw = task_prompt
        self.task_prompt = ""

        # 初始化角色提示
        self.role_prompts = dict()
        for role in self.config_role:
            self.role_prompts[role] = "\n".join(self.config_role[role])

        # 初始化日志
        self.start_time, self.log_filepath = self.get_logfilepath()

        # 初始化 SimplePhase 实例
        # 从 chatdev.phase 导入 PhaseConfig.json 中使用的所有阶段
        # 注意 PhaseConfig.json 中只存在 SimplePhases
        # ComposedPhases 在 ChatChainConfig.json 中定义，并将在 self.execute_step 中导入
        self.compose_phase_module = importlib.import_module("chatdev.composed_phase")
        self.phase_module = importlib.import_module("chatdev.phase")
        self.phases = dict()
        for phase in self.config_phase:
            assistant_role_name = self.config_phase[phase]['assistant_role_name']
            user_role_name = self.config_phase[phase]['user_role_name']
            phase_prompt = "\n\n".join(self.config_phase[phase]['phase_prompt'])
            phase_class = getattr(self.phase_module, phase)
            phase_instance = phase_class(assistant_role_name=assistant_role_name,
                                         user_role_name=user_role_name,
                                         phase_prompt=phase_prompt,
                                         role_prompts=self.role_prompts,
                                         phase_name=phase,
                                         model_type=self.model_type,
                                         log_filepath=self.log_filepath)
            self.phases[phase] = phase_instance

    def make_recruitment(self):
        """
        招聘所有员工
        返回值：无

        """
        for employee in self.recruitments:
            self.chat_env.recruit(agent_name=employee)

    def execute_step(self, phase_item: dict):
        """
        execute single phase in the chain
        Args:
            phase_item: single phase configuration in the ChatChainConfig.json

        Returns:

        """

        phase = phase_item['phase']
        phase_type = phase_item['phaseType']
        # 对于SimplePhase，只需从self.phases中查找并执行“Phase.execute”方法。
        if phase_type == "SimplePhase":
            max_turn_step = phase_item['max_turn_step']
            need_reflect = check_bool(phase_item['need_reflect'])
            if phase in self.phases:
                self.chat_env = self.phases[phase].execute(self.chat_env,
                                                           self.chat_turn_limit_default if max_turn_step <= 0 else max_turn_step,
                                                           need_reflect)
            else:
                raise RuntimeError(f"Phase '{phase}' is not yet implemented in chatdev.phase")
        # For ComposedPhase, we create instance here then conduct the "ComposedPhase.execute" method
        elif phase_type == "ComposedPhase":
            cycle_num = phase_item['cycleNum']
            composition = phase_item['Composition']
            compose_phase_class = getattr(self.compose_phase_module, phase)
            if not compose_phase_class:
                raise RuntimeError(f"Phase '{phase}' is not yet implemented in chatdev.compose_phase")
            compose_phase_instance = compose_phase_class(phase_name=phase,
                                                         cycle_num=cycle_num,
                                                         composition=composition,
                                                         config_phase=self.config_phase,
                                                         config_role=self.config_role,
                                                         model_type=self.model_type,
                                                         log_filepath=self.log_filepath)
            self.chat_env = compose_phase_instance.execute(self.chat_env)
        else:
            raise RuntimeError(f"PhaseType '{phase_type}' is not yet implemented.")

    def execute_chain(self):
        """
        execute the whole chain based on ChatChainConfig.json
        Returns: None

        """
        for phase_item in self.chain:
            self.execute_step(phase_item)

    def get_logfilepath(self):
        """
        get the log path (under the software path)
        Returns:
            start_time: time for starting making the software
            log_filepath: path to the log

        """
        start_time = now()
        filepath = os.path.dirname(__file__)
        # root = "/".join(filepath.split("/")[:-1])
        root = os.path.dirname(filepath)
        # directory = root + "/WareHouse/"
        directory = os.path.join(root, "WareHouse")
        log_filepath = os.path.join(directory,
                                    "{}.log".format("_".join([self.project_name, self.org_name, start_time])))
        return start_time, log_filepath

    def pre_processing(self):
        """
        remove useless files and log some global config settings
        Returns: None

        """
        filepath = os.path.dirname(__file__)
        root = os.path.dirname(filepath)
        directory = os.path.join(root, "WareHouse")

        if self.chat_env.config.clear_structure:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                # logs with error trials are left in WareHouse/
                if os.path.isfile(file_path) and not filename.endswith(".py") and not filename.endswith(".log"):
                    os.remove(file_path)
                    print("{} Removed.".format(file_path))

        software_path = os.path.join(directory, "_".join([self.project_name, self.org_name, self.start_time]))
        self.chat_env.set_directory(software_path)

        if self.chat_env.config.with_memory is True:
            self.chat_env.init_memory()

        # copy config files to software path
        shutil.copy(self.config_path, software_path)
        shutil.copy(self.config_phase_path, software_path)
        shutil.copy(self.config_role_path, software_path)

        # copy code files to software path in incremental_develop mode
        if check_bool(self.config["incremental_develop"]):
            for root, dirs, files in os.walk(self.code_path):
                relative_path = os.path.relpath(root, self.code_path)
                target_dir = os.path.join(software_path, 'base', relative_path)
                os.makedirs(target_dir, exist_ok=True)
                for file in files:
                    source_file = os.path.join(root, file)
                    target_file = os.path.join(target_dir, file)
                    shutil.copy2(source_file, target_file)
            self.chat_env._load_from_hardware(os.path.join(software_path, 'base'))

        # write task prompt to software
        with open(os.path.join(software_path, self.project_name + ".prompt"), "w") as f:
            f.write(self.task_prompt_raw)

        preprocess_msg = "**[预处理]**\n\n"
        chat_gpt_config = ChatGPTConfig()

        preprocess_msg += "**ChatDev 开始** ({})\n\n".format(self.start_time)
        preprocess_msg += "**时间戳**: {}\n\n".format(self.start_time)
        preprocess_msg += "**配置路径**: {}\n\n".format(self.config_path)
        preprocess_msg += "**阶段配置路径**: {}\n\n".format(self.config_phase_path)
        preprocess_msg += "**角色配置路径**: {}\n\n".format(self.config_role_path)
        preprocess_msg += "**任务提示**: {}\n\n".format(self.task_prompt_raw)
        preprocess_msg += "**项目名称**: {}\n\n".format(self.project_name)
        preprocess_msg += "**日志文件**: {}\n\n".format(self.log_filepath)
        preprocess_msg += "**ChatDev 配置**:\n{}\n\n".format(self.chat_env.config.__str__())
        preprocess_msg += "**ChatGPT 配置**:\n{}\n\n".format(chat_gpt_config)
        log_visualize(preprocess_msg)

        # 初始化任务提示
        if check_bool(self.config['self_improve']):
            self.chat_env.env_dict['task_prompt'] = self.self_task_improve(self.task_prompt_raw)
        else:
            self.chat_env.env_dict['task_prompt'] = self.task_prompt_raw
        if(check_bool(self.web_spider)):
            self.chat_env.env_dict['task_description'] = modal_trans(self.task_prompt_raw)

    def post_processing(self):
        """
        summarize the production and move log files to the software directory
        Returns: None

        """

        self.chat_env.write_meta()
        filepath = os.path.dirname(__file__)
        root = os.path.dirname(filepath)

        if self.chat_env_config.git_management:
            log_git_info = "**[Git 信息]**\n\n"

            self.chat_env.codes.version += 1
            os.system("cd {}; git add .".format(self.chat_env.env_dict["directory"]))
            log_git_info += "cd {}; git add .\n".format(self.chat_env.env_dict["directory"])
            os.system("cd {}; git commit -m \"v{} Final Version\"".format(self.chat_env.env_dict["directory"],
                                                                          self.chat_env.codes.version))
            log_git_info += "cd {}; git commit -m \"v{} Final Version\"\n".format(self.chat_env.env_dict["directory"],
                                                                                  self.chat_env.codes.version)
            log_visualize(log_git_info)

            git_info = "**[Git Log]**\n\n"
            import subprocess

            # execute git log
            command = "cd {}; git log".format(self.chat_env.env_dict["directory"])
            completed_process = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE)

            if completed_process.returncode == 0:
                log_output = completed_process.stdout
            else:
                log_output = "执行时出错 " + command

            git_info += log_output
            log_visualize(git_info)

        post_info = "**[Post Info]**\n\n"
        now_time = now()
        time_format = "%Y%m%d%H%M%S"
        datetime1 = datetime.strptime(self.start_time, time_format)
        datetime2 = datetime.strptime(now_time, time_format)
        duration = (datetime2 - datetime1).total_seconds()

        post_info += "Software Info: {}".format(
            get_info(self.chat_env.env_dict['directory'], self.log_filepath) + "\n\n🕑**duration**={:.2f}s\n\n".format(
                duration))

        post_info += "ChatDev Starts ({})".format(self.start_time) + "\n\n"
        post_info += "ChatDev Ends ({})".format(now_time) + "\n\n"

        directory = self.chat_env.env_dict['directory']
        if self.chat_env.config.clear_structure:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                if os.path.isdir(file_path) and file_path.endswith("__pycache__"):
                    shutil.rmtree(file_path, ignore_errors=True)
                    post_info += "{} Removed.".format(file_path) + "\n\n"

        log_visualize(post_info)

        logging.shutdown()
        time.sleep(1)

        shutil.move(self.log_filepath,
                    os.path.join(root + "/WareHouse", "_".join([self.project_name, self.org_name, self.start_time]),
                                 os.path.basename(self.log_filepath)))

    # @staticmethod
    def self_task_improve(self, task_prompt):
        """
        让代理改进用户查询提示
        参数:
            task_prompt: 原始用户查询提示

        返回:
            revised_task_prompt: 提示工程师代理改进后的提示

        """
        self_task_improve_prompt = """我将给你一个简短的软件设计需求描述，
            请将其重写为一个详细的提示，使大型语言模型能够更好地理解如何根据该提示制作这个软件，
            提示应确保LLM构建的软件能够正确运行，这是你需要考虑的最重要部分。
            请记住，修订后的提示应该尽量详细，尽量清晰，
            以下是简短描述:\"{}\"。
            如果修订后的提示是描述的修订版本，
            那么你应该以\"<INFO> 修订后的描述\"的格式返回消息，不要以其他格式返回消息。""".format(task_prompt)
        role_play_session = RolePlaying(
            assistant_role_name="Prompt Engineer",
            assistant_role_prompt="你是一个专业的提示工程师，可以改进用户输入提示，使LLM更好地理解这些提示。",
            user_role_prompt="您是一个想要使用LLM来构建软件的用户。",
            user_role_name="User",
            task_type=TaskType.CHATDEV,
            task_prompt="对用户查询进行即时工程",
            with_task_specify=False,
            model_type=self.model_type,
        )

        # log_visualize("System", role_play_session.assistant_sys_msg)
        # log_visualize("System", role_play_session.user_sys_msg)

        _, input_user_msg = role_play_session.init_chat(None, None, self_task_improve_prompt)
        assistant_response, user_response = role_play_session.step(input_user_msg, True)
        revised_task_prompt = assistant_response.msg.content.split("<INFO>")[-1].lower().strip()
        log_visualize(role_play_session.assistant_agent.role_name, assistant_response.msg.content)
        log_visualize(
            "**[任务提示自我提升]**\n**原始任务提示**: {}\n**改进的任务提示**: {}".format(
                task_prompt, revised_task_prompt))
        return revised_task_prompt
