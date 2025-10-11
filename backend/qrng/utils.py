# backend/qrng/utils.py

import re

def is_valid_bitstring(bitstring: str) -> bool:
    """
    Validates if a string contains only binary digits ('0' or '1').

    This is a helper function to ensure data integrity before sending it
    to the blockchain or using it in other parts of the application. It uses
    a regular expression for an efficient and clean check.

    Args:
        bitstring (str): The string to validate.

    Returns:
        bool: True if the string is a valid bitstring, False otherwise.
    """
    if not isinstance(bitstring, str):
        return False
    # The regex pattern '^ [01]*$' matches a string that contains only 0s and 1s
    # from the beginning (^) to the end ($).
    pattern = re.compile(r'^[01]*$')
    return bool(pattern.match(bitstring)) and len(bitstring) > 0

def bitstring_to_int(bitstring: str) -> int:
    """
    Converts a valid bitstring into its integer equivalent.

    Args:
        bitstring (str): The binary string to convert.

    Returns:
        int: The integer representation of the bitstring.
             Returns -1 if the bitstring is invalid.
    """
    if not is_valid_bitstring(bitstring):
        return -1
    
    # The int() constructor with base 2 (binary) handles the conversion.
    return int(bitstring, 2)

# Example usage (for direct testing of this file)
if __name__ == '__main__':
    print("--- QRNG Utility Functions Test ---")
    
    # Test cases for is_valid_bitstring
    valid_str = "101101"
    invalid_str_chars = "101102"
    invalid_str_empty = ""
    
    print(f"Is '{valid_str}' a valid bitstring? {is_valid_bitstring(valid_str)}")
    print(f"Is '{invalid_str_chars}' a valid bitstring? {is_valid_bitstring(invalid_str_chars)}")
    print(f"Is '{invalid_str_empty}' a valid bitstring? {is_valid_bitstring(invalid_str_empty)}")

    # Test cases for bitstring_to_int
    print(f"Integer value of '{valid_str}': {bitstring_to_int(valid_str)}")
    print(f"Integer value of '{invalid_str_chars}': {bitstring_to_int(invalid_str_chars)}")
 
