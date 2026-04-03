#!/bin/bash
echo "================================"
echo "  EcoMeal Bot - Starting..."
echo "================================"
echo

# Check Python
if ! command -v python &> /dev/null; then
    echo "ERROR: Python not found. Please install Python 3.10+"
    exit 1
fi

# Check if LM Studio is running
if ! curl -s http://localhost:1234/v1/models &> /dev/null; then
    echo "WARNING: LM Studio not detected on port 1234"
    echo "Starting without LLM - using database recipes only"
    echo
fi

# Run Streamlit
echo "Starting Streamlit on http://localhost:8501"
echo
python -m streamlit run app.py --server.port 8501
