# LangChain Studio - Quick Start Guide

## 🚀 Your Application is LIVE

**URL**: <http://localhost:5000>

## What You Have

A fully functional, premium web application for LangChain with:

### ✨ Working Features

- ✅ **Chat Interface** - Send messages and get responses
- ✅ **Model Selector** - Choose from 4 AI models
- ✅ **Navigation** - Switch between Chat, Models, Agents, Chains
- ✅ **Responsive Design** - Works on all devices
- ✅ **Dark Mode** - Premium glassmorphism UI

### 📁 Project Location

```
c:\Users\Terrance\langchain\langchain-web-app\
```

## Quick Commands

### View Application

```bash
# Open in browser
http://localhost:5000
```

### Stop Server

```
Press CTRL+C in the terminal
```

### Restart Server

```bash
cd c:\Users\Terrance\langchain\langchain-web-app
python app.py
```

### View Logs

Server logs appear in the terminal where you ran `python app.py`

## File Structure

```
langchain-web-app/
├── app.py              # Backend (Flask server)
├── requirements.txt    # Dependencies
├── DEPLOYMENT.md       # Full documentation
├── templates/
│   └── index.html     # Main page
└── static/
    ├── style.css      # Styling
    └── app.js         # Frontend logic
```

## How to Use

### 1. Chat

- Type a message in the input box
- Press Enter or click the send button
- See your message and the response appear

### 2. Switch Views

- Click "Models" to see available AI models
- Click "Agents" or "Chains" for placeholder views
- Click "Chat" to return to the chat interface

### 3. Clear Chat

- Click the trash icon in the header to clear all messages

### 4. Change Model

- Use the dropdown in the header to select different models
- Currently in demo mode (echoes your messages)

## Next Steps

### Add Real AI (OpenAI Example)

1. Get an OpenAI API key from <https://platform.openai.com>
2. Install: `pip install langchain-openai`
3. Update `app.py`:

```python
from langchain_openai import ChatOpenAI
import os

# Add at the top
os.environ["OPENAI_API_KEY"] = "your-api-key-here"
llm = ChatOpenAI(model="gpt-3.5-turbo")

# In the /api/chat endpoint, replace the demo response with:
response_text = llm.invoke(user_message).content
```

### Customize the Design

Edit `static/style.css` to change:

- Colors (see `:root` variables)
- Fonts
- Spacing
- Animations

### Add More Features

See `DEPLOYMENT.md` for ideas:

- Authentication
- Database integration
- RAG (document upload)
- Streaming responses
- Agent system

## Troubleshooting

### Can't Access <http://localhost:5000>

- Check if the server is running (look for "Running on..." message)
- Try <http://127.0.0.1:5000> instead
- Make sure no other app is using port 5000

### Changes Not Showing

- Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
- Clear browser cache
- Restart the Flask server

### Import Errors

```bash
pip install -r requirements.txt --upgrade
```

## Support

- **LangChain Docs**: <https://python.langchain.com>
- **Flask Docs**: <https://flask.palletsprojects.com>
- **Full Deployment Guide**: See `DEPLOYMENT.md`

---

**Status**: 🟢 Running on <http://localhost:5000>

Enjoy building with LangChain! 🦜🔗
