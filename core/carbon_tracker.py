"""
Carbon Tracker - Measures LLM inference energy consumption and CO2 emissions.
Inspired by Code Carbon (https://github.com/mlco2/codecarbon).

Tracks: LLM call duration, energy estimation from hardware TDP,
CO2eq calculation from country grid intensity, session-level aggregation.
"""

import time
import json
import platform
import subprocess
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

import config

# --- Hardware power estimates (TDP in Watts) ---
# Conservative estimates for common consumer hardware
GPU_TDP = {
    "RTX 4060 Laptop": 115,     # NVIDIA RTX 4060 Laptop GPU
    "RTX 4060": 170,
    "RTX 4070 Laptop": 140,
    "RTX 4070": 200,
    "RTX 3060": 170,
    "RTX 3070": 220,
    "RTX 3080": 320,
    "RTX 4080": 320,
    "RTX 4090": 450,
    "GTX 1660": 125,
    "GTX 1080": 180,
    "M1": 30,
    "M2": 35,
    "M3": 40,
    "Default": 100,
}

CPU_TDP = {
    "Intel i7-12700H": 45,
    "Intel i9-13900H": 45,
    "Intel i5-12400": 65,
    "Intel i7-13700K": 125,
    "AMD Ryzen 7 6800H": 45,
    "AMD Ryzen 9 7945HX": 55,
    "Default": 45,
}

# RAM power estimate: ~3W per 8GB
RAM_POWER_PER_8GB = 3.0  # Watts

# Country grid carbon intensity (gCO2/kWh)
# Source: IEA 2023, Ember Climate, Our World in Data
GRID_INTENSITY = {
    "France": 56, "Sweden": 41, "Norway": 26, "Switzerland": 54,
    "Finland": 132, "Denmark": 166, "United Kingdom": 231,
    "Germany": 350, "Netherlands": 339, "Belgium": 179,
    "Spain": 207, "Italy": 263, "Portugal": 198,
    "Austria": 143, "Poland": 680, "Greece": 398,
    "Czech Republic": 497, "Ireland": 294, "Romania": 255,
    "Morocco": 621, "Tunisia": 476, "Algeria": 437,
    "Egypt": 433, "Nigeria": 286, "South Africa": 751,
    "Kenya": 245, "Ethiopia": 109, "Senegal": 475,
    "United States": 379, "Canada": 127, "Mexico": 368,
    "Brazil": 86, "Argentina": 329, "Colombia": 167,
    "Peru": 213, "Chile": 422,
    "China": 537, "Japan": 449, "South Korea": 416,
    "India": 632, "Thailand": 457, "Vietnam": 487,
    "Indonesia": 610, "Philippines": 542, "Malaysia": 503,
    "Turkey": 430, "Israel": 452, "Lebanon": 588,
    "Australia": 527, "New Zealand": 142,
    "Russia": 424, "Ukraine": 343,
}

# GPT-4 reference: ~2.5g CO2eq per request (estimated from various studies)
GPT4_EMISSIONS_PER_REQUEST_G = 2.5


def detect_hardware() -> Dict:
    """Auto-detect system hardware (CPU, GPU, RAM). Works on Windows/Linux/Mac."""
    import shutil

    cpu_name = "Unknown CPU"
    gpu_name = "Unknown GPU"
    ram_gb = 16

    # Detect CPU
    try:
        if platform.system() == "Windows":
            # Use PowerShell (more reliable than wmic on newer Windows)
            result = subprocess.run(
                ["powershell.exe", "-Command",
                 "Get-CimInstance Win32_Processor | Select-Object -ExpandProperty Name"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0 and result.stdout.strip():
                cpu_name = result.stdout.strip().split("\n")[0].strip()
        elif platform.system() == "Linux":
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line:
                        cpu_name = line.split(":")[1].strip()
                        break
        elif platform.system() == "Darwin":
            result = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"],
                                    capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                cpu_name = result.stdout.strip()
    except Exception:
        pass

    # Detect GPU
    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ["powershell.exe", "-Command",
                 "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0 and result.stdout.strip():
                lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
                if lines:
                    gpu_name = lines[0]
                    # Handle multiple GPUs - prefer discrete
                    for line in lines:
                        if any(x in line for x in ["NVIDIA", "AMD", "Radeon"]):
                            gpu_name = line
                            break
    except Exception:
        pass

    # Detect RAM
    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ["powershell.exe", "-Command",
                 "(Get-CimInstance Win32_OperatingSystem).TotalVisibleMemorySize"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                ram_kb = int(result.stdout.strip())
                ram_gb = round(ram_kb / 1024 / 1024)
        elif platform.system() == "Linux":
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        ram_kb = int(line.split()[1])
                        ram_gb = round(ram_kb / 1024 / 1024)
                        break
    except Exception:
        pass

    # ARM64 specific adjustments (Snapdragon, Apple Silicon)
    cpu_tdp = 45  # default
    gpu_tdp = 100  # default

    cpu_lower = cpu_name.lower()
    gpu_lower = gpu_name.lower()

    # Snapdragon X Elite / ARM detection
    if "snapdragon" in cpu_lower or "x1p" in cpu_lower or platform.machine().lower() in ("aarch64", "arm64"):
        cpu_tdp = 30  # Snapdragon X Elite efficient cores
        if "adreno" in gpu_lower or "x1-85" in gpu_lower:
            gpu_tdp = 25  # Adreno iGPU

    # Apple Silicon
    if "apple" in cpu_lower or "m1" in cpu_lower or "m2" in cpu_lower or "m3" in cpu_lower:
        cpu_tdp = 30
        gpu_tdp = 35

    # NVIDIA GPUs
    if "rtx 4060" in gpu_lower:
        gpu_tdp = 115 if "laptop" in gpu_lower else 170
    elif "rtx 4070" in gpu_lower:
        gpu_tdp = 140 if "laptop" in gpu_lower else 200
    elif "rtx 3060" in gpu_lower:
        gpu_tdp = 170
    elif "rtx 3070" in gpu_lower:
        gpu_tdp = 220

    return {
        "cpu": cpu_name,
        "gpu": gpu_name,
        "ram_gb": ram_gb,
        "cpu_tdp": cpu_tdp,
        "gpu_tdp": gpu_tdp,
    }


class CarbonTracker:
    """Track energy consumption and CO2 emissions for LLM inference calls."""

    def __init__(self, country: str = "France", hardware: Optional[str] = None,
                 ram_gb: Optional[int] = None):
        self.country = country
        self.session_start = datetime.now()
        self.calls: List[Dict] = []

        # Auto-detect hardware if not provided
        detected = detect_hardware()
        self.hardware = hardware or detected["gpu"]
        self.ram_gb = ram_gb or detected["ram_gb"]
        self.cpu_name = detected["cpu"]

        # Pre-compute hardware power
        self.gpu_power_w = detected["gpu_tdp"] if not hardware else self._get_gpu_power(hardware)
        self.cpu_power_w = detected["cpu_tdp"]
        self.ram_power_w = (self.ram_gb / 8) * RAM_POWER_PER_8GB
        # Total system power during inference (GPU full load + CPU partial + RAM)
        # GPU inference typically uses 60-80% TDP, CPU 30-50%
        self.total_inference_power_w = (
            self.gpu_power_w * 0.7 +  # GPU at 70% TDP during inference
            self.cpu_power_w * 0.3 +   # CPU at 30% (feeding GPU)
            self.ram_power_w
        )

        # Grid intensity
        self.grid_intensity = GRID_INTENSITY.get(country, 350)  # default: world avg ~350

    def _get_gpu_power(self, hardware: str) -> float:
        for key, power in GPU_TDP.items():
            if key.lower() in hardware.lower():
                return power
        return GPU_TDP["Default"]

    def start_call(self) -> float:
        """Start timing an LLM call. Returns start timestamp."""
        return time.time()

    def end_call(self, start_time: float, tokens_generated: int = 0,
                 call_type: str = "inference") -> Dict:
        """End timing and record the call's energy/emissions."""
        duration_s = time.time() - start_time

        # Energy = Power x Time
        energy_wh = (self.total_inference_power_w * duration_s) / 3600
        energy_kwh = energy_wh / 1000

        # CO2eq = Energy x Grid Intensity
        co2_g = energy_kwh * self.grid_intensity * 1000  # gCO2eq
        co2_kg = co2_g / 1000

        call_record = {
            "timestamp": datetime.now().isoformat(),
            "duration_s": round(duration_s, 3),
            "energy_kwh": round(energy_kwh, 8),
            "co2_kg": round(co2_kg, 8),
            "co2_g": round(co2_g, 4),
            "tokens_generated": tokens_generated,
            "call_type": call_type,
            "hardware": self.hardware,
            "country": self.country,
            "grid_intensity": self.grid_intensity,
            "power_w": round(self.total_inference_power_w, 1),
        }

        self.calls.append(call_record)
        return call_record

    def get_session_summary(self) -> Dict:
        """Get aggregated session statistics."""
        if not self.calls:
            return self._empty_summary()

        total_duration = sum(c["duration_s"] for c in self.calls)
        total_energy = sum(c["energy_kwh"] for c in self.calls)
        total_co2_kg = sum(c["co2_kg"] for c in self.calls)
        total_co2_g = sum(c["co2_g"] for c in self.calls)
        total_tokens = sum(c["tokens_generated"] for c in self.calls)

        avg_duration = total_duration / len(self.calls)
        avg_co2_per_call_g = total_co2_g / len(self.calls)

        # Compare to GPT-4
        gpt4_total = GPT4_EMISSIONS_PER_REQUEST_G * len(self.calls)

        session_duration = (datetime.now() - self.session_start).total_seconds()

        return {
            "total_calls": len(self.calls),
            "total_duration_s": round(total_duration, 2),
            "total_energy_kwh": round(total_energy, 8),
            "total_co2_kg": round(total_co2_kg, 8),
            "total_co2_g": round(total_co2_g, 4),
            "avg_duration_s": round(avg_duration, 3),
            "avg_co2_per_call_g": round(avg_co2_per_call_g, 4),
            "total_tokens": total_tokens,
            "session_duration_s": round(session_duration, 1),
            "gpt4_comparison": {
                "gpt4_total_g": round(gpt4_total, 2),
                "local_total_g": round(total_co2_g, 4),
                "savings_pct": round((1 - total_co2_g / gpt4_total) * 100, 1) if gpt4_total > 0 else 0,
            },
            "hardware": {
                "gpu": self.hardware,
                "cpu": self.cpu_name,
                "gpu_tdp_w": self.gpu_power_w,
                "cpu_tdp_w": self.cpu_power_w,
                "ram_gb": self.ram_gb,
                "inference_power_w": round(self.total_inference_power_w, 1),
            },
            "grid": {
                "country": self.country,
                "intensity_gco2_kwh": self.grid_intensity,
            },
        }

    def _empty_summary(self) -> Dict:
        return {
            "total_calls": 0,
            "total_duration_s": 0,
            "total_energy_kwh": 0,
            "total_co2_kg": 0,
            "total_co2_g": 0,
            "avg_duration_s": 0,
            "avg_co2_per_call_g": 0,
            "total_tokens": 0,
            "session_duration_s": round(
                (datetime.now() - self.session_start).total_seconds(), 1
            ),
            "gpt4_comparison": {
                "gpt4_total_g": 0,
                "local_total_g": 0,
                "savings_pct": 0,
            },
            "hardware": {
                "gpu": self.hardware,
                "cpu": self.cpu_name,
                "gpu_tdp_w": self.gpu_power_w,
                "cpu_tdp_w": self.cpu_power_w,
                "ram_gb": self.ram_gb,
                "inference_power_w": round(self.total_inference_power_w, 1),
            },
            "grid": {
                "country": self.country,
                "intensity_gco2_kwh": self.grid_intensity,
            },
        }

    def save_to_file(self, filepath: Path):
        """Save session data to JSON."""
        data = {
            "session_start": self.session_start.isoformat(),
            "summary": self.get_session_summary(),
            "calls": self.calls,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def update_country(self, country: str):
        """Update country and recalculate grid intensity."""
        self.country = country
        self.grid_intensity = GRID_INTENSITY.get(country, 350)
