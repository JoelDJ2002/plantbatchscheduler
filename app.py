#!/usr/bin/env python3
"""
FastAPI server for Batch Plant Scheduling Simulator
Serves the UI and handles simulation requests
"""

import os
import json
import subprocess
import sys
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn

# Create FastAPI app
app = FastAPI(title="Batch Plant Scheduling Simulator", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="ui"), name="static")

# Configuration models
class PlantConfig(BaseModel):
    equipment: list
    products: list
    changeovers: list
    orders: list
    hours_per_day: int = 24
    simulation_time_days: int = 30

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serve the main UI"""
    ui_path = Path("ui/index.html")
    if ui_path.exists():
        with open(ui_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        raise HTTPException(status_code=404, detail="UI not found")

@app.post("/run-simulation")
async def run_simulation(config: PlantConfig):
    """
    Run the simulation with the provided configuration
    """
    try:
        # Save the configuration to plant_config.json
        config_path = Path("plant_config.json")
        with open(config_path, "w") as f:
            json.dump(config.dict(), f, indent=2)

        # Import and run the simulation
        # We need to capture stdout to return the results
        from io import StringIO
        import contextlib

        # Import the main function from simulator.py
        sys.path.insert(0, '.')  # Add current directory to path

        # Capture stdout
        output_buffer = StringIO()
        with contextlib.redirect_stdout(output_buffer):
            try:
                # Import and run the main function with our config
                import simulator
                simulator.main(config.dict())
            except Exception as e:
                return JSONResponse(
                    status_code=500,
                    content={"error": f"Simulation error: {str(e)}"}
                )

        # Get the captured output
        simulation_output = output_buffer.getvalue()

        return {
            "success": True,
            "output": simulation_output
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Server error: {str(e)}"}
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Batch Plant Scheduling Simulator is running"}

@app.post("/analyze-results")
async def analyze_results():
    """
    Analyze the simulation results using LLM (Groq)
    """
    try:
        results_path = Path("simulation_results.json")
        
        if not results_path.exists():
            return JSONResponse(
                status_code=404,
                content={"error": "No simulation results found. Please run a simulation first."}
            )
        
        # Read the simulation results
        with open(results_path, 'r') as f:
            simulation_data = json.load(f)
        
        # Import and call the LLM analysis function
        from ai_analyzer import analyze_scheduling_results_data
        
        analysis = analyze_scheduling_results_data(simulation_data)
        
        return {
            "success": True,
            "analysis": analysis
        }
        
    except ValueError as ve:
        return JSONResponse(
            status_code=400,
            content={"error": f"Configuration error: {str(ve)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Analysis error: {str(e)}"}
        )

if __name__ == "__main__":
    # Ensure UI directory exists
    if not Path("ui").exists():
        print("Error: UI directory not found. Please run this script from the project root.")
        sys.exit(1)

    # Ensure simulator.py exists
    if not Path("simulator.py").exists():
        print("Error: simulator.py not found in current directory.")
        sys.exit(1)

    print("🚀 Starting Batch Plant Scheduling Simulator...")
    print("📱 UI will be available at: http://localhost:8000")
    print("🔧 API endpoints:")
    print("   GET  /              - Main UI")
    print("   POST /run-simulation - Run simulation")
    print("   POST /analyze-results - Analyze with AI (Groq LLM)")
    print("   GET  /health        - Health check")

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

