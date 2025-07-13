(function() {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.type = "text/css";
    link.href = "extensions/WAI_NSFW_illustrious_character_select_for_ComfyUI/style.css";	// 这个路径确实有点奇怪，写成style.css就不行
    document.head.appendChild(link);
})();

import { app } from "../../../scripts/app.js";
import { ComfyWidgets } from "../../../scripts/widgets.js";

app.registerExtension({
	name: "Comfy.WAICharSelect.Util",

	async beforeRegisterNodeDef(nodeType, nodeData, app) {
		if (nodeData.name === "PromptAndLoraLoader") {
			const onNodeCreated = nodeType.prototype.onNodeCreated;
			nodeType.prototype.onNodeCreated = function () {
				onNodeCreated?.apply(this, arguments);

				const characterWidget = this.widgets.find(w => w.name === "character");
				const actionWidget = this.widgets.find(w => w.name === "action");

				// 如果不是随机模式，把seed相关控件设置为不可见
				const handleModeChange = (value, canvas, node, pos, event) => {
					const seedWidget = this.widgets.find(w => w.name === "seed");
					const controlWidget = this.widgets.find(w => w.name === "control_after_generate");

					if (!seedWidget || !controlWidget) return;
					if (characterWidget.value !== "random" && actionWidget.value !== "random") {
						seedWidget.hidden = true;
						controlWidget.hidden = true;
					} else {
						seedWidget.hidden = false;
						controlWidget.hidden = false;
					}

					canvas?.draw(true, true);
				}
				characterWidget.callback = handleModeChange;
				actionWidget.callback = handleModeChange;

				// 初始化
				handleModeChange("random", app.canvas, this);
			}

			const onExecuted = nodeType.prototype.onExecuted;
			nodeType.prototype.onExecuted = function (message) {
				onExecuted?.apply(this, arguments);
				
				if (!this.canvas_widget_class) {
					this.canvas_widget_class = "prompt-and-lora-loader-node";
					this.setDirtyCanvas(true, false); // 强制重绘以应用类名
				}

				// 记忆存在random选项时的cha/act数据，修改相应控件，以便重新运行工作流时使用
				if (message.selected_character && message.selected_action) {
					const characterWidget = this.widgets.find(w => w.name === "character");
					const actionWidget = this.widgets.find(w => w.name === "action");

					if (characterWidget && characterWidget.value === "random") {
						characterWidget.value = message.selected_character[0];
					}
					if (actionWidget && actionWidget.value === "random") {
						actionWidget.value = message.selected_action[0];
					}
				}
				// 图片处理
				this.imgs = []; 
				if (message.images) {
					for (const imgData of message.images) {
						const img = new Image();
						img.src = app.api.apiURL(
							`/view?filename=${encodeURIComponent(
								imgData.filename
							)}&type=${imgData.type}&subfolder=${encodeURIComponent(
								imgData.subfolder
							)}&t=${+new Date()}`
						);
						this.imgs.push(img);
					}
				}

				let widgetsWereChanged = false;
				// 文本处理
				if (message.text && message.text.length > 0) {
					widgetsWereChanged = true;
					const text = message.text[0];

					// 若原本有文本框控件，无需创建
					let stringWidget = this.widgets.find(w => w.name === "text_char_act_info")
					if (!stringWidget) {
						stringWidget = ComfyWidgets["STRING"](this, "text_char_act_info", ["STRING", { multiline: true }], app).widget;
						stringWidget.inputEl.readOnly = true;
						stringWidget.inputEl.style.opacity = 0.6;
						stringWidget.inputEl.classList.add("wai_char_select_textarea");
						}
					stringWidget.value = text;
					}
				// 重绘
				if (widgetsWereChanged || message.images) {
					this.setDirtyCanvas(true, true);
					requestAnimationFrame(() => {
						const sz = this.computeSize();
						if (sz[0] < this.size[0]) {
							sz[0] = this.size[0];
						}
						if (sz[1] < this.size[1]) {
							sz[1] = this.size[1];
						}
						this.onResize?.(sz);
						app.graph.setDirtyCanvas(true, false);
					});
				}
			}
		}
	},
});