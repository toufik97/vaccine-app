# Vaccine Management Application (Django + PyQt6)

A comprehensive desktop application designed to manage clinic patient records, track childhood vaccinations, and generate insightful health reports. 

The application has recently been upgraded to a **Decentralized API Architecture**, featuring a PyQt6 desktop frontend powered by a robust Python Django REST backend!

## Key Features

- **Decentralized Architecture**: The entire application's data is managed via a headless Django API backend (`http://127.0.0.1:8000/api/`), allowing multiple PyQt6 desktop instances to fetch, sync, and mutate clinic data simultaneously!
- **Patient Management**: Robust patient demographic tracking including flexible tracking of names, unified sex fields, and dynamic age representation smoothly serialized over network protocols.
- **Smart Vaccine Scheduling**: Complex scheduling engine that handles standard WHO protocols, flexible initial dates (e.g., newborn vaccines or first month allowance), and historical records via `VaxEngine`.
- **UI & Interaction**: Polished interface powered by PyQt6, with dynamic patient tables, interactive calendars, and distinct milestone groupings using intuitive color coding.
- **Reporting & Exporting**: Highly customizable reporting module capable of exporting clinical statistics, daily logs, and monthly reports to both PDF and Excel (`.xlsx`) formats.

## Architecture

1. **Backend** (`/backend`): A Django + Django REST Framework API holding the core database schemas (`vax_pro.db`). It natively manages `VaccineFamilies`, `Milestones`, and `Patient` logs through standard JSON HTTP endpoints.
2. **Frontend** (`/ui`, `/core`): A pure PyQt6 and Requests-based UI that interacts dynamically with the backend.

## Installation

You can get up and running easily:

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd vaccine
```

### 2. Set Up a Virtual Environment 
A virtual environment ensures dependencies don't conflict.

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## Running the Application

Because this is a distributed application, you must start the backend server before launching the frontend GUI.

### Step 1: Start the Django API Backend
Open a terminal, activate your virtual environment, and run:
```bash
cd backend
python manage.py runserver
```

*(Leave this terminal window open/running silently in the background)*

### Step 2: Start the PyQt6 Desktop App
Open a *second* terminal, activate your virtual environment, and run:
```bash
python main.py
```

## Technologies Used

- **Python 3**
- **Django REST Framework** (Backend API)
- **PyQt6** (Frontend GUI)
- **SQLite3** (Database Engine)
- **Requests** (HTTP Networking)
- **openpyxl** (Excel Report Engine)

## Contributing

Contributions, bug reports, and features requests are welcome. Please refer to issues and pull requests to get involved!
