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
	name: "Comfy.PromptAndLoraLoader",
	async beforeRegisterNodeDef(nodeType, nodeData, app) {
		const onExecuted = nodeType.prototype.onExecuted;
		nodeType.prototype.onExecuted = function (message) {
			onExecuted?.apply(this, arguments);
			
			if (!this.canvas_widget_class) {
				this.canvas_widget_class = "prompt-and-lora-loader-node";
				this.setDirtyCanvas(true, false); // 强制重绘以应用类名
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

			// 文本处理
			const permanentWidgets = [];
			let insertionIndex = -1; // -1 表示尚未找到插入点
			let widgetsWereChanged = false;

			if (this.widgets) {
				for (const w of this.widgets) {
					if (w.name?.startsWith("text_")) {
						w.onRemove?.();
						widgetsWereChanged = true;
						// 在第一次遇到旧文本控件时记录插入位置
						if (insertionIndex === -1) {
							insertionIndex = permanentWidgets.length;
						}
					} else {
						permanentWidgets.push(w);
					}
				}
			}

			const newTextWidgets = [];
			if (message.text && message.text.length > 0) {
				widgetsWereChanged = true;
				for (const text of message.text) {
					const newWidget = ComfyWidgets["STRING"](this, "text_" + Math.random(), ["STRING", { multiline: true }], app).widget;
					newWidget.inputEl.readOnly = true;
					newWidget.inputEl.style.opacity = 0.6;
					newWidget.inputEl.classList.add("wai_char_select_textarea")
					newWidget.value = text;
					newWidget.style
					newTextWidgets.push(newWidget);
				}
			}

			// 如果没有找到旧的文本控件作为标记，则默认添加到末尾
			if (insertionIndex === -1) {
				insertionIndex = permanentWidgets.length;
			}
			
			permanentWidgets.splice(insertionIndex, 0, ...newTextWidgets);

			this.widgets = permanentWidgets;

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
	},
});