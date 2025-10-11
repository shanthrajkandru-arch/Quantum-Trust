# backend/qrng/generator.py

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import math

class QuantumRNG:
    """
    A class to generate random numbers using quantum circuits simulated with Qiskit.
    This version is optimized to generate long bitstrings by running smaller,
    safe-sized quantum circuits multiple times to avoid simulator memory limits.
    """

    def __init__(self):
        """
        Initializes the QuantumRNG by setting up the AerSimulator.
        """
        self.simulator = AerSimulator()
        # Set a safe limit for the number of qubits to simulate in a single run.
        # This prevents memory errors on most standard computers.
        self.max_qubits_per_run = 24 

    def generate_random_bitstring(self, num_bits: int) -> str:
        """
        Generates a random bitstring of a specified length. If the requested
        number of bits exceeds the safe limit, it generates the bits in chunks.
        """
        if not isinstance(num_bits, int) or num_bits <= 0:
            print("Error: Number of bits must be a positive integer.")
            return ""

        # If the request is small enough, generate it in one single, efficient run.
        if num_bits <= self.max_qubits_per_run:
            return self._generate_chunk(num_bits)
        
        # If the request is large, generate the bits in multiple, safe-sized chunks.
        else:
            bit_chunks = []
            remaining_bits = num_bits
            
            while remaining_bits > 0:
                bits_to_generate = min(remaining_bits, self.max_qubits_per_run)
                bit_chunks.append(self._generate_chunk(bits_to_generate))
                remaining_bits -= bits_to_generate
                
            return "".join(bit_chunks)

    def _generate_chunk(self, num_bits_in_chunk: int) -> str:
        """
        Private helper method to generate a single chunk of random bits by
        running one quantum circuit simulation.
        """
        # Create a quantum circuit with the specified number of qubits.
        circuit = QuantumCircuit(num_bits_in_chunk, num_bits_in_chunk)
        # Apply Hadamard gates to all qubits to create superposition.
        circuit.h(range(num_bits_in_chunk))
        # Measure all qubits to collapse them to a random classical state.
        circuit.measure(range(num_bits_in_chunk), range(num_bits_in_chunk))

        # Transpile the circuit for the simulator and run the job.
        compiled_circuit = transpile(circuit, self.simulator)
        job = self.simulator.run(compiled_circuit, shots=1, memory=True)
        result = job.result()
        
        # The 'memory' contains the outcome, e.g., ['10110']. We take the first element.
        random_chunk = result.get_memory(compiled_circuit)[0]
        
        return random_chunk

# Example usage for direct testing of this file
if __name__ == '__main__':
    qrng = QuantumRNG()
    print("--- Quantum Random Number Generator (Chunked) ---")
    
    # Test a small generation (will use one run)
    bits_small = 8
    random_byte = qrng.generate_random_bitstring(bits_small)
    print(f"Generated {bits_small}-bit random string: {random_byte} (Length: {len(random_byte)})")

    # Test a large generation (will require multiple chunked runs)
    bits_large = 264
    random_key = qrng.generate_random_bitstring(bits_large)
    print(f"Generated {bits_large}-bit random string: {random_key} (Length: {len(random_key)})")
