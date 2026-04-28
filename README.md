# Global Disaster Map

A dynamic, interactive web application that visualizes historical natural hazards—Earthquakes, Tsunamis, and Volcanoes—across the globe. 

When, where, and why did disaster strike? What can we learn about it? What was the media coverage? The Global Disaster Map aims to answer these questions by providing an immersive 3D globe visualization alongside deep analytical insights and integrated historical media context.

## 🌟 Key Features

### 🗺️ Interactive Map View
- **3D Globe Visualization**: Powered by DeckGL and MapLibre, offering smooth navigation and a beautiful dark-mode aesthetic.
- **Timeline Animation**: Watch historical disasters unfold over time (1900 - Present) using the interactive playback timeline.
- **Advanced Filtering**: A sleek, glassmorphism sidebar to filter hazards by type, magnitude, and depth in real-time.
- **Contextual Insights**: Click on any disaster data point to fetch rich, contextual media coverage and historical records directly from the Wikipedia API.

### 📊 Analytics Dashboard
- **Data Visualizations**: Deep analytical insights powered by Recharts.
- **Top Affected Regions**: Horizontal bar charts highlighting the countries most frequently impacted by disasters.
- **Historical Trends**: Multi-line charts tracking the frequency of different disaster types across the last century.
- **Distribution Analysis**: Pie charts breaking down the global distribution of hazard types.

## 🛠️ Technology Stack

- **Frontend**: React (Vite), Deck.gl, React Map GL (MapLibre), Recharts, React Router Dom, vanilla CSS (Glassmorphism & Dark Mode).
- **Backend**: Python, FastAPI, SQLite (Local database).
- **External Integrations**: Wikipedia API (for fetching historical details and media).

---

## 🚀 Getting Started

Follow these instructions to run the application locally on your machine.

### Prerequisites
- [Python 3.8+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/)

### 1. Backend Setup

The backend serves the disaster data from an SQLite database and fetches external details from Wikipedia.

1. Open a terminal and navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. (Optional but recommended) Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install the required Python dependencies (FastAPI, Uvicorn, Requests):
   ```bash
   pip install fastapi uvicorn requests
   ```
4. Start the FastAPI development server:
   ```bash
   uvicorn main:app --reload
   ```
   *The backend API will now be running at `http://127.0.0.1:8000`.*

### 2. Frontend Setup

The frontend is a React application built with Vite.

1. Open a **new** terminal window and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install the necessary Node.js packages:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
4. Open your web browser and navigate to the local URL provided by Vite (usually `http://localhost:5173`).

Enjoy exploring the Global Disaster Map!
