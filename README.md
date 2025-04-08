---

## AVA Style Assistant 👗🤖

**AVA (Agent-based Virtual Assistant)** is an innovative AI-powered personal stylist designed for the **Global AI Agents League Hackathon**. By leveraging the [Fetch.ai](https://fetch.ai/) `uAgents` framework and integrating with [Agentverse](https://agentverse.ai/), AVA delivers personalized fashion advice and promotes sustainable upcycling practices.

---

## 🌟 Features

- **Personalized Assistant Agent**: Dynamically connects with relevant agents via Agentverse to fulfill user queries efficiently.
- **Body Analysis Agent**: Determines body shape, face shape, and color palette through user interactions.
- **Trend Analyzer & Stylist Agent**: Provides outfit recommendations by analyzing user preferences and current fashion trends.
- **Upcycler Agent**: Suggests creative upcycling ideas to promote sustainable fashion choices.

---

## 🏗️ Architecture Overview

The system comprises multiple specialized AI agents:

1. **Assistant Agent**: Coordinates user interactions and delegates tasks to other agents.
2. **Body Analysis Agent**: Assesses body type, face shape, and color season.
3. **Recommendation Agent**: Generates personalized style advice.
4. **Upcycler Agent**: Offers innovative upcycling suggestions.

These agents are developed using the `uAgents` framework and registered on Agentverse, enabling seamless interaction within the agent ecosystem.

---

## 🛠️ Getting Started

### Prerequisites

- Python 3.8 or higher
- [uAgents](https://pypi.org/project/uagents/) library
- Access to [Agentverse](https://agentverse.ai/)
- Google Generative AI SDK (for advanced recommendations)
- `.env` file with your **Google API Key**

### Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/your-username/ava-style-assistant.git
   cd ava-style-assistant
   ```

2. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environment Variables**:

   Create a `.env` file in the project root:

   ```env
   GOOGLE_API_KEY=your_google_api_key_here
   ```

---

## 🚀 Running the Application

Start the system using the bureau:

```bash
python bureau.py
```

This will initiate:

- **Bureau Server**: Runs on `http://localhost:8000`
- **Web Frontend**: Accessible at `http://localhost:8080`
- **Agents**: Assistant, Body Analysis, Recommendation, and Upcycler Agents

---

## 🔗 Integration with Agentverse

To comply with the hackathon's requirements:

1. **Register Agents on Agentverse**: Ensure all agents are registered on [Agentverse](https://agentverse.ai/), facilitating discovery and interaction with other agents.

2. **Utilize Search and Discovery**: The Assistant Agent employs Agentverse's Search and Discovery feature to dynamically connect with the most relevant agents, whether created by your team or other participants, to fulfill user queries and coordinate tasks efficiently.



---

## 🙌 Acknowledgements

- **Fetch.ai**: For providing the `uAgents` framework and hosting the hackathon.
- **Agentverse**: For enabling seamless agent registration and discovery.
- **Google Generative AI**: For powering advanced style recommendations.
- **Open-Source Community**: For continuous support and inspiration.

---

