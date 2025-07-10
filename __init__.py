# Author: zch9241[zch2426936965@gmail.com]
# 

from PIL import Image
import random

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
    action_names_with_random = ["random"] + action_names
    character_names_with_random = ["random"] + character_names


except Exception as e:
    print(f"[CharacterSelector] Error loading data: {e}")
    character_names =["Error loading data"]
    action_names = ["Error loading data"]
    character_names_with_random = ["random", "Error loading data"]
    action_names_with_random = ["random", "Error loading data"]

# 定义节点类
class PromptAndLoraLoader:
    """
    加载lora, 构造提示词
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL", ),
                "clip": ("CLIP", ),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "character": (character_names_with_random, ),
                "action": (action_names_with_random, ),
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

    RETURN_TYPES = ("MODEL", "CLIP", "CONDITIONING", "CONDITIONING", "STRING")
    RETURN_NAMES = ("model", "clip", "positive_cond", "negative_cond", "character_name")
    FUNCTION = "build_workflow"
    CATEGORY = "WAI Character Selector"
    
    def build_workflow(self, model, clip, seed, character, action, add_nsfw, 
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

        if character == "random" or action == "random":
            print(f"[PromptAndLoraLoader] Seed: {seed}, Selected Character: {selected_character}, Selected Action: {selected_action}")
        else:
            print(f"[PromptAndLoraLoader] Selected Character: {selected_character}, Selected Action: {selected_action}")

        # 动态加载lora
        lora_loader = LoraLoader()
        
        if add_details:
            model, clip = lora_loader.load_lora(
                model, clip, "add-detail-xl.safetensors", add_details_lora_weight, add_details_lora_weight
            )
            print("[PromptAndLoraLoader] Loaded add-detail-xl lora with weight:", add_details_lora_weight)
        if enhance_body:
            model, clip = lora_loader.load_lora(
                model, clip, "ChihunHentai_20230709225610-000004.safetensors", enhance_body_lora_weight, enhance_body_lora_weight
            )
            print("[PromptAndLoraLoader] Loaded ChihunHentai lora with weight:", enhance_body_lora_weight)
        if enhance_quality:
            model, clip = lora_loader.load_lora(
                model, clip, "spo_sdxl_10ep_4k-data_lora_webui.safetensors", enhance_quality_lora_weight, enhance_quality_lora_weight
            )
            print("[PromptAndLoraLoader] Loaded spo_sdxl_10ep_4k-data_lora_webui lora with weight:", enhance_quality_lora_weight)
        if enhance_character:
            model, clip = lora_loader.load_lora(
                model, clip, "ponyv4_noob1_2_adamW-000017.safetensors", enhance_character_lora_weight, enhance_character_lora_weight
            )
            print("[PromptAndLoraLoader] Loaded ponyv4_noob1_2_adamW-000017 lora with weight:", enhance_character_lora_weight)
        
        
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

        pos_prompt = ", ".join(part for part in pos_prompt_parts if part)

        neg_prompt = settings["neg_prompt"]
        
        print(f"[PromptAndLoraLoader] Positive Prompt: {pos_prompt}")
        print(f"[PromptAndLoraLoader] Negative Prompt: {neg_prompt}")

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

        return (model, clip, final_pos_conditioning, final_neg_conditioning, selected_character)



class CharacterImagePreviewer:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "character": ("STRING", {"forceInput": True})
            }
        }
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("character_image",)
    FUNCTION = "get_character_image"
    CATEGORY = "WAI Character Selector"
    
    def get_character_image(self, character):
        """根据角色名称获取对应的预览图像。"""
        if character in character_names:
            character_prompt = characters[character]
            for character_image in character_images:
                if list(character_image.keys()) == [character_prompt]:
                    character_image_data = character_image[character_prompt]
                    break
            pil_image = utils.base64_to_pil(character_image_data)
            tensor_image = utils.pil_to_tensor(pil_image)
            return (tensor_image, )
        else:
            # 如果找不到图像，返回一个黑色的空图像，避免工作流中断
            print(f"[CharacterImagePreviewer] No image found for character: {character}. Returning a black image.")
            black_image = Image.new('RGB', (64, 64), 'black')
            return (utils.pil_to_tensor(black_image),)


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
    CATEGORY = "WAI Character Selector"

    def concatenate(self, text_a, text_b, separator=", "):
        # 过滤掉空的输入，避免产生多余的分隔符
        parts = [text for text in [text_a, text_b] if text and text.strip()]
        result = separator.join(parts)
        return (result,)


# 注册节点
NODE_CLASS_MAPPINGS = {
    "PromptAndLoraLoader": PromptAndLoraLoader,
    "CharacterImagePreviewer": CharacterImagePreviewer,
    "TextConcatenate": TextConcatenate,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptAndLoraLoader": "(WAI)角色提示词生成器",
    "CharacterImagePreviewer": "(WAI)角色图片预览",
    "TextConcatenate": "文本连接器",
}

print("[WAI_NSFW_illustrious_character_select_for_ComfyUI] Node loaded successfully.")