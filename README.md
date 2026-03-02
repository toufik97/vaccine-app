# Vaccine Management Application

A comprehensive desktop application designed to manage clinic patient records, track childhood vaccinations, and generate insightful health reports. Built with Python and PyQt6 for a modern and responsive user experience. 

## Key Features

- **Patient Management**: Robust patient demographic tracking including flexible tracking of names, unified sex fields ('M'/'F'), and dynamic age representation.
- **Smart Vaccine Scheduling**: Complex scheduling engine that handles standard WHO protocols, flexible initial dates (e.g., newborn vaccines or first month allowance), and external historical records with unknown precise dates.
- **UI & Interaction**: Polished interface powered by PyQt6, with dynamic patient tables, interactive calendars, well-distinguished milestone groups using intuitive color coding.
- **Reporting & Exporting**: Highly customizable reporting module capable of exporting clinical statistics, daily logs, and monthly reports to both PDF and Excel (`.xlsx`) formats.
- **Database**: Complete SQLite backing allowing for easy migration, backing up, and robust data persistence.

## Installation

You can get up and running easily:

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd vaccine
```

### 2. Set Up a Virtual Environment (Recommended)
A virtual environment ensures dependencies don't conflict with your system Python packages.

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

To start the app, verify you have your environment activated and run:

```bash
python main.py
```

## Technologies Used

- **Python 3**
- **PyQt6** (Frontend GUI)
- **SQLite3** (Database Engine)
- **openpyxl** (Excel Report Engine)

## Contributing

Contributions, bug reports, and features requests are welcome. Please refer to issues and pull requests to get involved!
