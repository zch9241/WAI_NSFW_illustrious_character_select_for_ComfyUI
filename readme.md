# WAI NSFW illustrious character select for ComfyUI

这是一个为 [ComfyUI](https://github.com/comfyanonymous/ComfyUI) 设计的自定义节点扩展包。它移植并扩展了流行的 Stable Diffusion WebUI 扩展 [WAI-NSFW-illustrious-character-select](https://github.com/lanner0403/WAI-NSFW-illustrious-character-select) ，以 ComfyUI 原生的、基于节点的方式实现。

通过本扩展，你可以轻松地从预设的列表中选择角色和动作，自动添加风格化的增强提示词，并通过模块化的节点自由组合，构建出强大而灵活的生成工作流。

本扩展暂时没有实现AI补充提示词和随机选人选动作的功能

## 安装方式

通过 `绘世启动器` 或 `ComfyUI Manager` 安装即可

## 节️点详解

在 ComfyUI 的节点菜单中，你可以在 `Character Selector` 分类下找到以下节点：

### 1. (WAI)角色提示词生成器

这是构建提示词的基础节点。

**功能**: 提供下拉菜单选择角色和动作，以及一系列复选框来添加风格化提示词。

**输入**: 无。

**输出**:

* `positive_prompt` (STRING): 正向提示词
* `negative_prompt` (STRING): 反向提示词
* `character_name` (STRING): 角色名-提示词

**用途**: 用于生成核心的角色和风格提示词片段。

### 2. (WAI)角色图片预览

一个方便的视觉辅助工具。

**功能**: 根据选择的角色名，显示对应的预览图。

**输入**:

* `character`: 来自 `(WAI)角色提示词生成器`

**输出**:

* `IMAGE`: 图像数据，可以连接到 `Preview Image` 节点进行显示。

### 3. 文本连接器

**功能**: 拼接两段字符串，这个没必要解释了吧。

### 4. (WAI)角色图片预览

这是连接提示词和采样器的关键桥梁。

**功能**: 接收文本字符串，将其编码为 `CONDITIONING`，并能与上游传入的 `CONDITIONING` 进行合并。

**输入**:

* `clip`: 来自 `Load Checkpoint` 节点的 CLIP 模型。
* `text`: 来自 `(WAI)角色提示词生成器` 或其他文本节点的字符串。
* `weight`: 滑块，用于调整 `text` 输入的提示词权重。
* `conditioning_in` (可选): 连接上一个 `CONDITIONING` 节点的输出。

**输出**:

* `CONDITIONING`: 合并后的最终 `CONDITIONING`，可直接连接到 `KSampler` 的 `positive` 或 `negative` 端口。

## 推荐工作流

详见项目根目录下的[WAI.json](WAI.json)

## 致谢

本项目的所有配置文件均来自 [@lanner0403](https://github.com/lanner0403/) 的项目 [WAI-NSFW-illustrious-character-select](https://github.com/lanner0403/WAI-NSFW-illustrious-character-select)
