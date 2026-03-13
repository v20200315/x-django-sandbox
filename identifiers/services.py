"""
GS1 UDI-DI-PI code generation.
Format: (AI)(value) concatenated. No separator between elements.
"""


def generate_udidipi_code(di_values, ai_value_pairs):
    """
    Generate UDI-DI-PI code per GS1 rules.

    Args:
        di_values: List of DI value strings (e.g. ["(01)01234567890123"])
        ai_value_pairs: List of (ai_code, value) tuples (e.g. [("17", "250101"), ("10", "BATCH")])

    Returns:
        Concatenated UDI-DI-PI string.
    """
    parts = []

    # DI part: concatenate DI values (each may already be (AI)(value) format)
    for v in di_values:
        v = (v or '').strip()
        if v:
            parts.append(v)

    # PI part: (AI)(value) for each AI
    for ai_code, value in ai_value_pairs:
        ai_code = (ai_code or '').strip()
        value = (value or '').strip()
        if ai_code and value:
            parts.append(f'({ai_code}){value}')

    return ''.join(parts)
