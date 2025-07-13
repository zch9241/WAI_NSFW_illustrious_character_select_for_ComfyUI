# Author: zch9241[zch2426936965@gmail.com]
# 

import os
import random
import time

import numpy as np
from PIL import Image


import folder_paths
from nodes import LoraLoader

from . import utils


# 加载配置文件
try:
    settings = utils.get_config('settings.json')
    actions = utils.get_config('action.json')    # 动作名-提示词
    characters = utils.get_config('zh_TW.json')   # 角色名-提示词
    
    # 动作名
    action_names = list(actions.keys())
    
    # 角色预览图像(角色提示词-图片数据)
    character_images = []
    for i in range(11):
        img_data = utils.get_config(f'output_{i + 1}.json')
        if img_data:
            character_images.extend(img_data)
    
    # 角色名
    character_names = list(characters.keys())
    
    # 随机
    action_names_ = ["skip", "random"] + action_names
    character_names_ = ["skip", "random"] + character_names


except Exception as e:
    print(f"[WAI_NSFW_illustrious_character_select_for_ComfyUI] Error loading data: {e}")
    character_names =["Error loading data"]
    action_names = ["Error loading data"]
    character_names_ = ["skip", "random", "Error loading data"]
    action_names_ = ["skip", "random", "Error loading data"]


class PromptAndLoraLoader:
    """
    加载lora, 构造提示词
    """
    
    def __init__(self):
        self.output_dir = folder_paths.get_temp_directory()
        self.type = "temp"
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ("MODEL", ),
                "clip": ("CLIP", ),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "character": (character_names_, {"default": "random"}),
                "action": (action_names_, {"default": "random"}),
                "workflow_control": ("BOOLEAN", {"default": False, "label_on": "使用当前配置生成（工作流将继续运行）", "label_off": "预览随机选项（工作流将被终止）"}),
                "add_nsfw": ("BOOLEAN", {"default": True}),
                "add_details": ("BOOLEAN", {"default": True}),
                "add_details_lora_weight": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.01}),
                "enhance_body": ("BOOLEAN", {"default": False}),
                "enhance_body_lora_weight": ("FLOAT", {"default": 0.9, "min": 0.0, "max": 10.0, "step": 0.01}),
                "enhance_quality": ("BOOLEAN", {"default": True}),
                "enhance_quality_lora_weight": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 10.0, "step": 0.01}),
                "enhance_character": ("BOOLEAN", {"default": True}),
                "enhance_character_lora_weight": ("FLOAT", {"default": 0.8, "min": 0.0, "max": 10.0, "step": 0.01}),
            },
            "optional":{
                 "positive_conditioning_in": ("CONDITIONING", ),
                 "negative_conditioning_in": ("CONDITIONING", ),
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP", "CONDITIONING", "CONDITIONING", "BOOLEAN")
    RETURN_NAMES = ("model", "clip", "positive_conditioning", "negative_conditioning", "gate_passthrough")
    FUNCTION = "build_workflow"
    CATEGORY = "WAI Character Selector"
    OUTPUT_NODE = True
    
    def build_workflow(self, model, clip, seed, character, action, workflow_control, add_nsfw, 
                       add_details, add_details_lora_weight,
                       enhance_body, enhance_body_lora_weight,
                       enhance_quality, enhance_quality_lora_weight,
                       enhance_character, enhance_character_lora_weight,
                       positive_conditioning_in=None, negative_conditioning_in=None):
        # 随机功能
        rng = random.Random(seed)
        if character == "random":
            selected_character = rng.choice(character_names)
        else:
            selected_character = character
            
        if action == "random":
            selected_action = rng.choice(action_names)
        else:
            selected_action = action

        is_random = character == "random" or action == "random"
        if is_random:
            print(f"[PromptAndLoraLoader] Seed: {seed}, Selected Character: {selected_character}, Selected Action: {selected_action}")
        else:
            print(f"[PromptAndLoraLoader] Selected Character: {selected_character}, Selected Action: {selected_action}")

        # 动态加载lora
        lora_loader = LoraLoader()
        
        if add_details:
            lora_name = "add-detail-xl.safetensors"
            model, clip = lora_loader.load_lora(
                model, clip, lora_name, add_details_lora_weight, add_details_lora_weight
            )
            print(f"[PromptAndLoraLoader] Loaded {lora_name.strip('.safetensors')} lora with weight: {add_details_lora_weight}")
        if enhance_body:
            lora_name = "ChihunHentai_20230709225610-000004.safetensors"
            model, clip = lora_loader.load_lora(
                model, clip, lora_name, enhance_body_lora_weight, enhance_body_lora_weight
            )
            print(f"[PromptAndLoraLoader] Loaded {lora_name.strip('.safetensors')} lora with weight: {enhance_body_lora_weight}")
        if enhance_quality:
            lora_name = "spo_sdxl_10ep_4k-data_lora_webui.safetensors"
            model, clip = lora_loader.load_lora(
                model, clip, lora_name, enhance_quality_lora_weight, enhance_quality_lora_weight
            )
            print(f"[PromptAndLoraLoader] Loaded {lora_name.strip('.safetensors')} lora with weight: {enhance_quality_lora_weight}")
        if enhance_character:
            lora_name = "ponyv4_noob1_2_adamW-000017.safetensors"
            model, clip = lora_loader.load_lora(
                model, clip, lora_name, enhance_character_lora_weight, enhance_character_lora_weight
            )
            print(f"[PromptAndLoraLoader] Loaded {lora_name.strip('.safetensors')} lora with weight: {enhance_character_lora_weight}")
        
        
        # 构建提示词
        pos_prompt_parts = []
        
        pos_prompt_parts.append(settings["pos_prompt"])
        if selected_character in character_names:
            pos_prompt_parts.append(characters[selected_character])
        if selected_action in action_names:
            pos_prompt_parts.append(actions[selected_action])
        if add_nsfw:
            pos_prompt_parts.append(settings["nsfw"])
        if enhance_body:
            pos_prompt_parts.append(settings["chihunhentai"])
        if enhance_quality:
            pos_prompt_parts.append(settings["quality"])

        pos_prompt = ", ".join(part.strip().strip(",") for part in pos_prompt_parts if part)

        neg_prompt = settings["neg_prompt"]
        
        print(f"[PromptAndLoraLoader] Positive Prompt: {pos_prompt}\n")
        print(f"[PromptAndLoraLoader] Negative Prompt: {neg_prompt}\n")

        # 解析
        pos_tokens = clip.tokenize(pos_prompt)
        pos_cond, pos_pooled = clip.encode_from_tokens(pos_tokens, return_pooled=True)
        pos_conditioning = [[pos_cond, {"pooled_output": pos_pooled}]]
        neg_tokens = clip.tokenize(neg_prompt)
        neg_cond, neg_pooled = clip.encode_from_tokens(neg_tokens, return_pooled=True)
        neg_conditioning = [[neg_cond, {"pooled_output": neg_pooled}]]

        
        # 如果有上游的 conditioning，合并它们
        if positive_conditioning_in is not None:
            final_pos_conditioning = positive_conditioning_in + pos_conditioning
        else:
            final_pos_conditioning = pos_conditioning
        if negative_conditioning_in is not None:
            final_neg_conditioning = negative_conditioning_in + neg_conditioning
        else:
            final_neg_conditioning = neg_conditioning
        
        # 在节点内显示选择的角色图像
        if selected_character in character_names:
            character_prompt = characters[selected_character]
            for character_image in character_images:
                if list(character_image.keys()) == [character_prompt]:
                    character_image_data = character_image[character_prompt]
                    break
            pil_image = utils.base64_to_pil(character_image_data)
        else:
            print(f"[PromptAndLoraLoader] No image found for character: {selected_character}. Returning a black image.")
            pil_image = Image.new('RGB', (64, 64), 'black')

        file_prefix = f"character_{time.time()}_{np.random.randint(1000)}"
        file_path = os.path.join(self.output_dir, f"{file_prefix}.png")
        pil_image.save(file_path, "PNG")
        
        return_image = [{
            "filename": os.path.basename(file_path),
            "subfolder": "",
            "type": self.type
        }]
        text = [f"角色: {selected_character}\n动作: {selected_action}"]
        
        ui_payload = {
            "images": return_image, 
            "text": text,
            "selected_character": [selected_character],
            "selected_action": [selected_action],
        }
        # False = 暂停, True = 继续
        gate_passthrough = workflow_control
        
        return {"ui": ui_payload, "result": (model, clip, final_pos_conditioning, final_neg_conditioning, gate_passthrough)}


class ConditionalGate:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "gate_input": ("BOOLEAN", {"forceInput": True}),
                "positive_conditioning": ("CONDITIONING",),
                "negative_conditioning": ("CONDITIONING",),
            }
        }
    
    RETURN_TYPES = ("CONDITIONING", "CONDITIONING",)
    RETURN_NAMES = ("positive_conditioning", "negative_conditioning",)
    FUNCTION = "gate"
    CATEGORY = "WAI Character Selector/Utils"

    def gate(self, gate_input, positive_conditioning, negative_conditioning):
        if not gate_input:
            print("\033[93m[WAI ConditionalGate] 门已关闭。工作流在此处被有意终止。这不是一个错误。\033[0m")
            raise Exception("工作流已由'(WAI)流程控制门'终止。")
        print("\033[92m[WAI ConditionalGate] 门已打开。工作流继续执行。\033[0m")
        return (positive_conditioning, negative_conditioning)


class TextConcatenate:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text_a": ("STRING", {"multiline": True, "default": ""}),
                "text_b": ("STRING", {"multiline": True, "default": ""}),
            },
            "optional": {
                "separator": ("STRING", {"default": ", "})
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "concatenate"
    CATEGORY = "WAI Character Selector/Utils"

    def concatenate(self, text_a, text_b, separator=", "):
        # 过滤掉空的输入，避免产生多余的分隔符
        parts = [text for text in [text_a, text_b] if text and text.strip()]
        result = separator.join(parts)
        return (result,)


NODE_CLASS_MAPPINGS = {
    "PromptAndLoraLoader": PromptAndLoraLoader,
    "ConditionalGate": ConditionalGate,
    "TextConcatenate": TextConcatenate,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptAndLoraLoader": "(WAI)角色提示词生成器",
    "ConditionalGate": "(WAI)工作流控制门",
    "TextConcatenate": "文本连接器",
}
WEB_DIRECTORY = "./web"
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']

print("[WAI_NSFW_illustrious_character_select_for_ComfyUI] Node loaded successfully.")