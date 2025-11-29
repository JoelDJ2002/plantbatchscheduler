# Batch Plant Scheduling Simulator

A web-based interface for configuring and running batch plant production scheduling simulations using Salabim.

## Features

- **Interactive Web UI** for configuring plant parameters
- **Equipment Management**: Add, edit, and remove reactors, dryers, and packagers
- **Order Management**: Configure customer orders with products, quantities, due dates, and priorities
- **Changeover Times**: Set sequence-dependent changeover times between products
- **Simulation Control**: Adjust simulation duration and run multiple scheduling algorithms
- **Real-time Results**: View detailed simulation results and performance metrics

## Project Structure

```
├── ui/                    # Web interface files
│   ├── index.html        # Main HTML page
│   ├── styles.css        # CSS styling
│   └── script.js         # JavaScript logic
├── server.py             # FastAPI server
├── car_dict_input.py     # Core simulation logic
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the Server**
   ```bash
   python server.py
   ```

3. **Open Your Browser**
   Navigate to `http://localhost:8000`

## Usage

### Equipment Configuration
- Add reactors (R-xxx), dryers (D-xxx), or packagers (P-xxx)
- Set capacity for each equipment unit
- IDs are auto-generated based on equipment type

### Orders Configuration
- Add customer orders with auto-incrementing IDs
- Select from products A, B, or C
- Set quantity, due date, and priority (1-4)
- Priority defaults to random if not specified

### Changeover Times
- Define sequence-dependent changeover times between products
- Set time in hours for transitions between different products
- Same product transitions are automatically 0 hours

### Simulation Settings
- Set simulation duration in days
- Click "Run Simulation" to execute all scheduling algorithms
- View results comparing FIFO, EDD, and Critical Ratio methods

## Supported Scheduling Algorithms

1. **FIFO (First In, First Out)**: Process orders in priority order, then by due date
2. **EDD (Earliest Due Date)**: Process orders by due date only
3. **Critical Ratio**: Priority based on (due_date - now) / processing_time

## API Endpoints

- `GET /` - Main web interface
- `POST /run-simulation` - Run simulation with configuration
- `GET /health` - Health check

## Configuration File

The system generates a `plant_config.json` file with the following structure:

```json
{
  "equipment": [
    {"id": "R-101", "type": "Reactor", "capacity": 500}
  ],
  "products": [...],
  "changeovers": [...],
  "orders": [...],
  "hours_per_day": 24,
  "simulation_time_days": 30
}
```

## Requirements

- Python 3.8+
- FastAPI
- Uvicorn
- Salabim
- Modern web browser with JavaScript enabled

## Development

The UI is built with vanilla HTML, CSS, and JavaScript for maximum compatibility. The backend uses FastAPI for high performance and automatic API documentation.

## Troubleshooting

- Ensure all files are in the correct directory structure
- Check that `car_dict_input.py` is in the same directory as `server.py`
- Verify all Python dependencies are installed
- Check browser console for JavaScript errors

