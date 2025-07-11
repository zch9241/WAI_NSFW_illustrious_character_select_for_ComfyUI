import { app } from "../../../scripts/app.js";


app.registerExtension({
	name: "Comfy.PromptAndLoraLoader",
    
	async beforeRegisterNodeDef(nodeType, nodeData, app) {
		if (nodeData.name === "PromptAndLoraLoader") {
			const onExecuted = nodeType.prototype.onExecuted;
			nodeType.prototype.onExecuted = function (message) {
				onExecuted?.apply(this, arguments);

				if (message.images) {
					this.imgs = []; 
					
					for (const imgData of message.images) {
						const img = new Image();
						
						// ComfyUI 的标准 API 路径：/view?filename=...&subfolder=...&type=...
						img.src = api.apiURL(
							`/view?filename=${encodeURIComponent(
								imgData.filename
							)}&type=${imgData.type}&subfolder=${encodeURIComponent(
								imgData.subfolder
							)}&t=${+new Date()}`
						);
						this.imgs.push(img);
					}
					this.setDirtyCanvas(true, true); 
				}
			};
		}
	},


    getCustomWidgets(node) {
        if (node.name === "PromptAndLoraLoader") {
            return {
                IMAGE(node, inputName, inputData, app) {
                    const widget = {
                        name: "preview_widget",
                        type: "div",
                        draw: function (ctx, node, width, y) {
                            if (!node.imgs || node.imgs.length === 0) {
                                return;
                            }
                            
                            // 计算绘制区域
                            const margin = 10;
                            const x = margin;
                            const widgetY = y;
                            const availableWidth = width - 2 * margin;
                            
                            // 绘制第一张图片
                            const firstImage = node.imgs[0];
                            if (firstImage.naturalWidth > 0) {
                                const aspectRatio = firstImage.naturalWidth / firstImage.naturalHeight;
                                let drawWidth = availableWidth;
                                let drawHeight = drawWidth / aspectRatio;
                                
                                if (drawHeight > node.size[1] - widgetY - margin) {
                                    drawHeight = node.size[1] - widgetY - margin;
                                    drawWidth = drawHeight * aspectRatio;
                                }

                                ctx.drawImage(firstImage, x, widgetY, drawWidth, drawHeight);
                            }
                        },
                        computeSize: function(width) {
                            if (node.imgs && node.imgs.length > 0) {
                                return [width, 220]; 
                            }
                            return [width, 0];
                        }
                    };
                    node.addCustomWidget(widget);
                    return widget;
                }
            }
        }
    }
});