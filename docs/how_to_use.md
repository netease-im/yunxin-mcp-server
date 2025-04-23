
## 如何使用

你可以使用任意支持工具调用的大模型客户端以及大模型来使用yunxin_mcp_server

以下以deepseek和cherry-studio为例

### 下载cherry-studio

参考：[链接](https://cherry-ai.com/download)

### deepseek账号注册

参考：[链接](https://www.deepseek.com/)

### 配置mcp-server

参考：[链接](https://docs.cherry-ai.com/advanced-basic/mcp)

### 启用yunxin-mcp-server

* ui 配置

![img_40.png](img_40.png)


* json配置

```json
{
  "mcpServers": {
    "yunxin_mcp": {
      "name": "yunxin-mcp-server",
      "type": "stdio",
      "command": "uvx",
      "args": [
        "yunxin_mcp_server"
      ],
      "env": {
        "AppKey": "your_appkey",
        "AppSecret": "your_secret"
      }
    }
  }
}
```

### 有任何问题欢迎联系云信技术支持！