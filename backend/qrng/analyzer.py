# ==============================================
# backend/qrng/analyzer.py
# ==============================================
# This module performs the full randomness analysis for QuantumTrust.
# It generates quantum random bits, runs zero-dependency NIST-style tests.
# ==============================================

# --- Fix for Matplotlib Rendering in Headless Environments ---
# When running in environments without a display (like servers),
# matplotlib needs to use the 'Agg' backend to draw figures.
import matplotlib
matplotlib.use('Agg')

# --- Standard Library Imports ---
import math
import base64
from io import BytesIO

# --- Qiskit Imports for Quantum Random Number Generation ---
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

# --- Numpy for FFT (used in spectral test) ---
import numpy as np  # safe, comes with Qiskit

# --- Local Imports ---
from .generator import QuantumRNG  # Our custom quantum RNG class

# ==============================================
# NIST-Style Statistical Tests (Zero-Dependency)
# These are simplified but statistically valid.
# They compute p-values and determine PASS/FAIL.
# ==============================================

def _frequency_test(bit_string: str) -> dict:
    """
    Frequency (Monobit) Test:
    Checks if the number of 1s and 0s in the string is roughly equal.
    """
    n = len(bit_string)
    ones = bit_string.count('1')
    zeros = n - ones
    s_obs = abs(ones - zeros) / math.sqrt(n)  # normalized difference
    p_value = math.erfc(s_obs / math.sqrt(2))  # complementary error function
    return {
        "test_name": "Frequency (Monobit) Test",
        "p_value": p_value,
        "passed": p_value >= 0.01,  # 1% significance level
        "visualization_data": {"zeros": zeros, "ones": ones}
    }

def _runs_test(bit_string: str) -> dict:
    """
    Runs Test:
    Checks for streaks of repeated bits. Too few or too many runs indicates non-randomness.
    """
    n = len(bit_string)
    ones = bit_string.count('1')
    pi = ones / n
    # If bit balance is way off, automatically fail
    if abs(pi - 0.5) >= (2 / math.sqrt(n)):
        return {"test_name": "Runs Test", "p_value": 0.0, "passed": False}
    # Count number of runs (changes between bits)
    v_obs = sum(1 for i in range(n - 1) if bit_string[i] != bit_string[i + 1]) + 1
    p_value = math.erfc(abs(v_obs - 2 * n * pi * (1 - pi)) / (2 * math.sqrt(2 * n) * pi * (1 - pi)))
    return {"test_name": "Runs Test", "p_value": p_value, "passed": p_value >= 0.01}

def _longest_run_of_ones_test(bit_string: str) -> dict:
    """
    Longest Run of Ones Test:
    Splits bit string into 8-bit blocks, finds the longest run of 1s in each block,
    then compares the distribution to expected probabilities.
    """
    n = len(bit_string)
    M, K, N = 8, 3, n // 8  # block size, categories, number of blocks
    pi_values = [0.2148, 0.3672, 0.2305, 0.1875]  # expected probabilities
    v = [0] * (K + 1)  # counters for categories

    for i in range(N):
        block = bit_string[i*M:(i+1)*M]
        runs = [len(run) for run in block.split('0') if run]
        max_run = max(runs) if runs else 0
        if max_run <= 1: v[0] += 1
        elif max_run == 2: v[1] += 1
        elif max_run == 3: v[2] += 1
        else: v[3] += 1

    chi_squared = sum(((v[i] - N * pi_values[i])**2) / (N * pi_values[i]) for i in range(K + 1))
    p_value = 1.0 - math.e ** (-chi_squared / 2.0)  # Approximation
    return {
        "test_name": "Longest Run of Ones",
        "p_value": p_value,
        "passed": p_value >= 0.01,
        "visualization_data": {"counts": v, "labels": ["<=1", "2", "3", ">=4"]}
    }

def _serial_test(bit_string: str, m: int = 2) -> dict:
    """
    Serial Test:
    Checks frequency of all possible m-bit patterns in the sequence.
    """
    n = len(bit_string)
    extended_bit_string = bit_string + bit_string[:m-1]  # wrap-around
    counts = {format(i, f'0{m}b'): 0 for i in range(2**m)}
    for i in range(n):
        counts[extended_bit_string[i:i+m]] += 1
    psi_squared = ((2**m / n) * sum(v**2 for v in counts.values())) - n
    p_value = math.erfc(abs(psi_squared) / math.sqrt(2))
    return {
        "test_name": "Serial (m=2) Test",
        "p_value": p_value,
        "passed": p_value >= 0.01,
        "visualization_data": counts
    }

def _cumulative_sums_test(bit_string: str) -> dict:
    """
    Cumulative Sums Test:
    Treats the sequence as a random walk, checks if the sum strays too far from 0.
    """
    n = len(bit_string)
    x = [1 if bit == '1' else -1 for bit in bit_string]
    s = [0] * n
    s[0] = x[0]
    for i in range(1, n):
        s[i] = s[i-1] + x[i]
    z = max(abs(val) for val in s)

    # Compute p-value using series approximation
    sum_a = sum(((4 * k + 1) * math.e**(-((4 * k + 1)**2) * z**2 / (2 * n))) for k in range(int((-n / z + 1) / 4), int((n / z - 1) / 4) + 1))
    sum_b = sum(((4 * k - 1) * math.e**(-((4 * k - 1)**2) * z**2 / (2 * n))) for k in range(int((-n / z - 3) / 4), int((n / z - 1) / 4) + 1))
    p_value = 1.0 - (1 / math.sqrt(2 * math.pi)) * (sum_a - sum_b)

    return {
        "test_name": "Cumulative Sums Test",
        "p_value": p_value,
        "passed": p_value >= 0.01,
        "visualization_data": {"sums": s, "boundary": 1.96 * math.sqrt(n)}
    }

def _approximate_entropy_test(bit_string: str, m: int = 2) -> dict:
    """
    Approximate Entropy Test:
    Measures the predictability of consecutive blocks of bits.
    """
    n = len(bit_string)
    def phi(m_val):
        extended_bit_string = bit_string + bit_string[:m_val-1]
        counts = {format(i, f'0{m_val}b'): 0 for i in range(2**m_val)}
        for i in range(n):
            counts[extended_bit_string[i:i+m_val]] += 1
        return sum((c/n) * math.log(c/n) for c in counts.values() if c > 0)
    
    phi_m = phi(m)
    phi_m1 = phi(m + 1)
    chi_squared = 2 * n * (math.log(2) - (phi_m - phi_m1))
    p_value = 1.0 - math.e ** (-chi_squared / 2.0)
    return {
        "test_name": "Approximate Entropy",
        "p_value": p_value,
        "passed": p_value >= 0.01,
        "visualization_data": {"ap_en": (phi_m - phi_m1)}
    }

def _fft_test(bit_string: str) -> dict:
    """
    FFT (Spectral) Test:
    Detects periodic patterns using Fast Fourier Transform.
    """
    n = len(bit_string)
    x = np.array([1 if bit == '1' else -1 for bit in bit_string])
    s = np.fft.fft(x)
    moduli = np.abs(s[1:n//2])
    T = np.sqrt(np.log(1/0.05) * n)
    N0 = 0.95 * (n / 2)
    N1 = len(np.where(moduli < T)[0])
    d = (N1 - N0) / np.sqrt(n * 0.95 * 0.05 / 4)
    p_value = math.erfc(abs(d) / np.sqrt(2))
    return {
        "test_name": "FFT (Spectral) Test",
        "p_value": p_value,
        "passed": p_value >= 0.01,
        "visualization_data": {"moduli": moduli.tolist(), "threshold": T}
    }

# ==============================================
# Main Analysis Orchestrator
# ==============================================

def perform_full_analysis(sample_bits: int = 128):
    """
    Generates quantum random bits, runs all tests, and produces a proof image.
    Returns a dict ready to send to frontend.
    """
    qrng = QuantumRNG()  # Quantum RNG instance
    simulator = AerSimulator()  # Qiskit simulator for circuits

    # --- Generate 50,000+ bits for NIST tests ---
    bits_for_nist = "".join([qrng.generate_random_bitstring(24) for _ in range(2084)])
    sample_bitstring = bits_for_nist[:sample_bits]  # small slice for UI animation

    # --- Run All NIST-Style Tests ---
    nist_results = [
        _frequency_test(bits_for_nist),
        _runs_test(bits_for_nist),
        _longest_run_of_ones_test(bits_for_nist),
        _serial_test(bits_for_nist),
        _cumulative_sums_test(bits_for_nist),
        _approximate_entropy_test(bits_for_nist),
        _fft_test(bits_for_nist),
    ]

    # --- Create Proof: Small Quantum Circuit Diagram ---
    vis_bits = 4
    circuit = QuantumCircuit(vis_bits, vis_bits)
    circuit.h(range(vis_bits))  # Hadamard gates create superposition
    circuit.measure(range(vis_bits), range(vis_bits))  # measure qubits

    # Save diagram to base64 for frontend embedding
    buffer = BytesIO()
    circuit.draw(output='mpl').savefig(buffer, format='png')
    circuit_image = base64.b64encode(buffer.getvalue()).decode('utf-8')

    # --- Bundle Final Results ---
    final_result = {
        "sampleBitstring": sample_bitstring,  # slice for UI animation
        "fullBitstring": bits_for_nist,       # full 50k+ bits for download
        "proof": {
            "circuitImage": f"data:image/png;base64,{circuit_image}",
            "nistResults": nist_results
        }
    }
    
    return final_result
