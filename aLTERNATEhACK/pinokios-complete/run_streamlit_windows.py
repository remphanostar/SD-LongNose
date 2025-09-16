
import streamlit as st
import sys
import os
from pathlib import Path

# Set paths for Windows
repo_path = Path(r"A:\Tools n Programs\PinokioNotebook\aLTERNATEhACK\pinokios-complete")
sys.path.insert(0, str(repo_path))
os.chdir(repo_path)

# Import and run the FIXED Streamlit app
from ui.streamlit_app_fixed import main

if __name__ == "__main__":
    main()
