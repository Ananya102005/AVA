# AVA: Agent-based Virtual Stylist + Upcycler

[![Innovation Lab Badge](https://fetch.ai/images/innovation-lab-badge.svg)](https://www.fetch.ai/innovation-lab)


### Personal Styling and Sustainable Fashion Powered by Fetch.ai uAgents

---

## Table of Contents
- [Introduction](#introduction)
- [Problem Statement](#problem-statement)
- [Objective](#objective)
- [Solution Overview](#solution-overview)
- [Technology Stack](#technology-stack)
- [Core Features](#core-features)
- [System Flow](#system-flow)
- [Agent Details](#agent-details)
- [Agentverse Integration](#agentverse-integration)
- [Innovation Lab Badge Eligibility](#innovation-lab-badge-eligibility)
- [Running the Application](#running-the-application)
- [Future Improvements](#future-improvements)
- [License](#license)
- [Acknowledgements](#acknowledgements)

---

## 🧠 Introduction

**AVA (Agent-based Virtual Assistant)** is a decentralized, modular personal stylist and upcycling guide built using Fetch.ai's **uAgents framework**. AVA is a multi-agent system that helps users:
- Analyze their body type, face shape, and color palette
- Get fashion advice based on current trends
- Suggest personalized outfit recommendations
- Offer upcycling ideas for old clothing to promote sustainability

---

## ❓ Problem Statement

Finding personalized fashion advice and keeping up with daily trends is overwhelming. Moreover, most people discard old clothes instead of creatively reusing them, contributing to fashion waste.

---

## 🎯 Objective

To build an intelligent and autonomous style advisor using the Fetch.ai ecosystem, combining:
- AI-driven personalization
- Global fashion trends
- Circular fashion through upcycling
- Privacy-respecting architecture via uAgents

---

## 🤩 Solution Overview

AVA uses four specialized autonomous agents managed by a Bureau:
1. **Body Analyzer Agent**
2. **Stylist Agent**
3. **Upcycler Agent**
4. **Chatbot Agent**

These agents communicate using Fetch.ai's `uAgents` protocol to deliver real-time and personalized fashion experiences.

---

## 🛠 Technology Stack

| Layer             | Tools/Frameworks                      |
|------------------|----------------------------------------|
| **Agents**        | Fetch.ai uAgents                      |
| **AI/ML**         | Gemini AI (Google Generative AI SDK) |
| **Backend**       | Python, FastAPI                       |
| **Frontend**      | HTML, CSS ,JavaScript                            |
| **Database**      | In-memory |


---

## ✨ Core Features

- **Body Analyzer**: Determines user’s body type, face shape, and color palette using standard questionnaires.
- **Trend-Based Stylist**: Offers curated outfit suggestions using global trend insights.
- **Upcycler Agent**: Suggests creative upcycling ideas based on user’s clothing inputs.
- **Chatbot Interface**: Seamlessly connects users with the appropriate agent through natural queries.

---

## 🧬 System Flow

'''
![ChatGPT_Image_Apr_8,_2025,_10_13_52_PM 1](https://github.com/user-attachments/assets/cc907bce-75cb-4c6d-8c93-2a8dda3d6119)


---

## 🤖 Agent Details

### 1. Body Analyzer Agent
- Takes input via questionnaire.
- Determines body type, color palette (season), and face shape.

### 2. Stylist Agent
- Fetches real-time trends.
- Gives complete outfit recommendations using user’s wardrobe images or inputs.

### 3. Upcycler Agent
- User provides an item they want to upcycle.
- Suggests ideas and step-by-step implementation.

### 4. Chatbot Agent
- Acts as a natural language interface to route queries to the appropriate agent.

---

## 💫 Agentverse Integration

The current system is compatible with Fetch.ai’s **Agentverse**, enabling:
- Public publishing of each agent
- Inter-agent coordination across user networks
- Scaling the ecosystem with plug-and-play fashion agents

To integrate with Agentverse:
- Register each agent on Agentverse
- Add wallet and identity management
- Use Discovery Service for matchmaking between fashion advisors and users

---


---

## 🚀 Running the Application

### Step 1: Clone the Repository
```bash
git clone https://github.com/Ananya102005/ava-style-assistant.git
cd ava-style-assistant
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Setup Environment
Create a `.env` file:
```
GOOGLE_API_KEY=your_google_api_key_here
```

### Step 4: Run Bureau
```bash
python bureau.py
```

This will launch:
- All agents via Fetch’s uAgents framework
- FastAPI backend on `http://localhost:8000`
- Web UI on `http://localhost:8080`

---

## Innovation Lab Badge Eligibility

AVA qualifies for the **Innovation Lab badge** by:
- Demonstrating real-world application in sustainable fashion
- Using autonomous multi-agent systems
- Promoting decentralized ecosystems (via Agentverse support)

---

## 🔮 Future Improvements

- Add multilingual and voice-based chatbot interface
- Integration with fashion retailers and e-commerce APIs
- Upgrade Gemini logic with emotional context handling
- Gamified rewards for upcycling behavior
- Native mobile app with AR try-ons

---

## 📜 License

MIT License - see `LICENSE` file for details.

---

## 🙌 Acknowledgements

- [Fetch.ai](https://fetch.ai/) for the uAgents framework
- [Google Generative AI](https://ai.google/discover/gemini/) for powerful NLP
- Fashion and sustainability communities for inspiration

