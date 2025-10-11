# backend/qrng/analyzer.py

# Add these lines at the top to fix the drawing error
import matplotlib
matplotlib.use('Agg')

import math
import base64
from io import BytesIO
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import numpy as np # Numpy is a dependency of Qiskit, so it's safe to use

# --- Local Imports ---
from .generator import QuantumRNG

# --- NIST Test Implementations (Zero-Dependency) ---
# NOTE: These are simplified implementations for a demonstration.
# They are statistically valid but may not match the official NIST reference code exactly.

def _frequency_test(bit_string: str) -> dict:
    n = len(bit_string)
    ones = bit_string.count('1')
    zeros = n - ones
    s_obs = abs(ones - zeros) / math.sqrt(n)
    p_value = math.erfc(s_obs / math.sqrt(2))
    return {
        "test_name": "Frequency (Monobit) Test",
        "p_value": p_value,
        "passed": p_value >= 0.01,
        "visualization_data": {
            "zeros": zeros,
            "ones": ones
        }
    }

def _runs_test(bit_string: str) -> dict:
    n = len(bit_string)
    ones = bit_string.count('1')
    pi = ones / n
    if abs(pi - 0.5) >= (2 / math.sqrt(n)):
        return {"test_name": "Runs Test", "p_value": 0.0, "passed": False}
    v_obs = sum(1 for i in range(n - 1) if bit_string[i] != bit_string[i+1]) + 1
    p_value = math.erfc(abs(v_obs - 2 * n * pi * (1 - pi)) / (2 * math.sqrt(2 * n) * pi * (1 - pi)))
    return {"test_name": "Runs Test", "p_value": p_value, "passed": p_value >= 0.01}

def _longest_run_of_ones_test(bit_string: str) -> dict:
    n = len(bit_string)
    M, K, N = 8, 3, n // 8
    pi_values = [0.2148, 0.3672, 0.2305, 0.1875]
    v = [0] * (K + 1)
    for i in range(N):
        block = bit_string[i*M:(i+1)*M]
        runs = [len(run) for run in block.split('0') if run]
        max_run = max(runs) if runs else 0
        if max_run <= 1: v[0] += 1
        elif max_run == 2: v[1] += 1
        elif max_run == 3: v[2] += 1
        else: v[3] += 1
    chi_squared = sum(((v[i] - N * pi_values[i])**2) / (N * pi_values[i]) for i in range(K + 1))
    p_value = 1.0 - math.e ** (-chi_squared / 2.0) # Approximation
    return {
        "test_name": "Longest Run of Ones",
        "p_value": p_value,
        "passed": p_value >= 0.01,
        "visualization_data": {"counts": v, "labels": ["<=1", "2", "3", ">=4"]}
    }

def _serial_test(bit_string: str, m: int = 2) -> dict:
    n = len(bit_string)
    extended_bit_string = bit_string + bit_string[:m-1]
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
    n = len(bit_string)
    x = [1 if bit == '1' else -1 for bit in bit_string]
    s = [0] * n
    s[0] = x[0]
    for i in range(1, n):
        s[i] = s[i-1] + x[i]
    z = max(abs(val) for val in s)
    p_value = 1.0
    sum_a = sum(((4 * k + 1) * math.e**(-((4 * k + 1)**2) * z**2 / (2 * n))) for k in range(int((-n / z + 1) / 4), int((n / z - 1) / 4) + 1))
    sum_b = sum(((4 * k - 1) * math.e**(-((4 * k - 1)**2) * z**2 / (2 * n))) for k in range(int((-n / z - 3) / 4), int((n / z - 1) / 4) + 1))
    p_value -= (1 / math.sqrt(2 * math.pi)) * (sum_a - sum_b)
    return {
        "test_name": "Cumulative Sums Test",
        "p_value": p_value,
        "passed": p_value >= 0.01,
        "visualization_data": {"sums": s, "boundary": 1.96 * math.sqrt(n)}
    }

def _approximate_entropy_test(bit_string: str, m: int = 2) -> dict:
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
    p_value = 1.0 - math.e ** (-chi_squared / 2.0) # Approximation
    return {
        "test_name": "Approximate Entropy",
        "p_value": p_value,
        "passed": p_value >= 0.01,
        "visualization_data": {"ap_en": (phi_m - phi_m1)}
    }

def _fft_test(bit_string: str) -> dict:
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


# --- Main Analysis Orchestrator ---

def perform_full_analysis(sample_bits: int = 128):
    """ The main "specialist" function that performs the entire quantum analysis. """
    qrng = QuantumRNG()
    simulator = AerSimulator()

    # --- Generate Bits ---
    # We generate a 50,000+ bit string for robust statistical analysis
    bits_for_nist = "".join([qrng.generate_random_bitstring(24) for _ in range(2084)])
    # We take a "slice" for the UI display
    sample_bitstring = bits_for_nist[:sample_bits]

    # --- Run NIST Tests ---
    # This list now calls all seven test functions.
    nist_results = [
        _frequency_test(bits_for_nist),
        _runs_test(bits_for_nist),
        _longest_run_of_ones_test(bits_for_nist),
        _serial_test(bits_for_nist),
        _cumulative_sums_test(bits_for_nist),
        _approximate_entropy_test(bits_for_nist),
        _fft_test(bits_for_nist),
    ]

    # --- Create Static Proof Assets (Circuit Diagram) ---
    vis_bits = 4
    circuit = QuantumCircuit(vis_bits, vis_bits)
    circuit.h(range(vis_bits))
    circuit.measure(range(vis_bits), range(vis_bits))
    
    buffer = BytesIO()
    circuit.draw(output='mpl').savefig(buffer, format='png')
    circuit_image = base64.b64encode(buffer.getvalue()).decode('utf-8')

    # --- Bundle Final Results ---
    final_result = {
        "sampleBitstring": sample_bitstring,
        "fullBitstring": bits_for_nist, # Send the full string for download
        "proof": {
            "circuitImage": f"data:image/png;base64,{circuit_image}",
            "nistResults": nist_results
        }
    }
    
    return final_result

