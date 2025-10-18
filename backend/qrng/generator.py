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
        self.simulator = AerSimulator()  # Initialize Qiskit's Aer simulator
        # Set a safe limit for the number of qubits to simulate in a single run.
        # Prevents memory errors on standard computers.
        self.max_qubits_per_run = 24 

    def generate_random_bitstring(self, num_bits: int) -> str:
        """
        Generates a random bitstring of a specified length. 
        If the requested number of bits exceeds the safe limit, it generates the bits in chunks.

        Args:
            num_bits (int): Total number of random bits to generate.

        Returns:
            str: A binary string of length `num_bits`.
        """
        # Validate input
        if not isinstance(num_bits, int) or num_bits <= 0:
            print("Error: Number of bits must be a positive integer.")
            return ""

        # Case 1: Small request fits in one circuit
        if num_bits <= self.max_qubits_per_run:
            return self._generate_chunk(num_bits)
        
        # Case 2: Large request needs multiple safe-sized chunks
        else:
            bit_chunks = []  # To hold each chunk
            remaining_bits = num_bits
            
            # Generate bits in loops of max_qubits_per_run
            while remaining_bits > 0:
                bits_to_generate = min(remaining_bits, self.max_qubits_per_run)
                bit_chunks.append(self._generate_chunk(bits_to_generate))
                remaining_bits -= bits_to_generate  # Decrease remaining bits
                
            # Combine all chunks into the final bitstring
            return "".join(bit_chunks)

    def _generate_chunk(self, num_bits_in_chunk: int) -> str:
        """
        Private helper method to generate a single chunk of random bits by
        running one quantum circuit simulation.

        Args:
            num_bits_in_chunk (int): Number of bits to generate in this chunk.

        Returns:
            str: Random bitstring of length `num_bits_in_chunk`.
        """
        # 1. Create a quantum circuit with the given number of qubits and classical bits
        circuit = QuantumCircuit(num_bits_in_chunk, num_bits_in_chunk)
        
        # 2. Apply Hadamard gate to each qubit to create equal superposition
        circuit.h(range(num_bits_in_chunk))
        
        # 3. Measure all qubits to collapse them into classical bits
        circuit.measure(range(num_bits_in_chunk), range(num_bits_in_chunk))

        # 4. Compile and run the circuit on the simulator
        compiled_circuit = transpile(circuit, self.simulator)
        job = self.simulator.run(compiled_circuit, shots=1, memory=True)
        result = job.result()
        
        # 5. Retrieve the measured result from 'memory', which is a list of strings
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
