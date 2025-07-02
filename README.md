
## ⚙️ Prerequisites

Make sure you have the following :

1. Install [Claude Desktop App](https://claude.ai/)
2. Install [uv](https://docs.astral.sh/uv/guides/install-python/)

---

## 💪 Installation

### 1.create a project folder (mcpserver) and open it in any code editor. 
### Open the terminal in the created folder


### 2. 

```bash
uv init . 
```

### 3. Add project dependencies 

```bash
uv add "mcp[cli]"
```

### 5. adding the tool to your cluade application

```bash
uv run mcp install server.py 
```

---

## 📾 To fix the tool not showing in Claude app

- Edit claude_destop_configuration in file > settings > developer > edit config
- Add the absolute path of uv in   "command": "uv"
- Restart the Claude Desktop App




