# Trading 212 AI Market Intelligence

An AI-powered stock market intelligence dashboard built with Flask, Google Gemini AI, Trading 212 API, and Yahoo Finance.

## Features

- 📈 Live market movers
- 🤖 AI-generated stock analysis
- 💼 Trading 212 portfolio integration
- 🔥 Top gainers & losers tracking
- ⚡ Sudden spikes & crashes detection
- 📊 Sector analysis
- 🧠 AI investment picks
- 🌐 Real-time market insights

---

# Technologies Used

- Python
- Flask
- Google Gemini AI
- Trading 212 API
- Yahoo Finance (yfinance)
- Requests

---

# Project Structure

.
├── app.py
├── requirements.txt
├── START_WINDOWS.bat
└── templates/
    └── index.html

---

# Installation

## 1. Clone Repository

```bash
git clone https://github.com/your-username/your-repository.git
cd your-repository
```

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Configuration

You can configure API keys inside `app.py` or use environment variables.

## Trading 212 API Key

```python
T212_API_KEY = "YOUR_API_KEY"
```

## Gemini API Key

```python
GEMINI_API_KEY = "YOUR_API_KEY"
```

---

# Running the Application

## Windows

Double click:

```text
START_WINDOWS.bat
```

OR run manually:

```bash
python app.py
```

---

# Open in Browser

```text
http://localhost:5000
```

---

# API Endpoints

| Endpoint | Description |
|----------|-------------|
| /api/status | Trading 212 account status |
| /api/portfolio | Portfolio information |
| /api/market_movers | Top market movers |
| /api/ai_scan | AI market analysis |

---

# AI Scan Types

Supported AI scan modes:

- winners
- losers
- spikes
- crashes
- sectors
- full
- picks
- portfolio_analysis
- custom

---

# Requirements

```text
flask>=3.0.0
requests>=2.31.0
google-generativeai>=0.8.0
yfinance>=0.2.36
```

---

# Security Warning

⚠️ Never expose your API keys publicly.

For production use environment variables instead of hardcoding keys.

Example:

```bash
set T212_API_KEY=your_key
set GEMINI_API_KEY=your_key
```

---

# Future Improvements

- User authentication
- Interactive stock charts
- Live websocket updates
- Database integration
- Docker deployment
- Trading automation
- Dark mode UI

---

# Author

Developed by Azzam

---

# License

This project is for educational and research purposes.
