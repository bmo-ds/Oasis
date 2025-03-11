import numpy as np
import json


def convert_species_config_with_categorical(json_data):
    """
    Converts a JSON species configuration into a NumPy structured array while
    converting categorical (string) fields into numeric codes for optimization.

    Parameters:
        json_data (dict): The JSON dictionary containing the 'species_grid' key.

    Returns:
        tuple: A tuple containing:
            - np.ndarray: A NumPy structured array with the simulation data.
            - dict: A dictionary mapping each categorical field to its code mapping.
    """
    species_list = json_data.get("species_grid", [])

    # Define the string fields that need to be converted to categorical codes.
    string_fields = ['class', 'species', 'music_taste']
    # Build a mapping for each field: value -> integer code.
    mappings = {}
    for field in string_fields:
        unique_vals = {entry.get(field, "") for entry in species_list}
        unique_vals = sorted(unique_vals)
        mappings[field] = {val: idx for idx, val in enumerate(unique_vals)}

    # Define the structured dtype.
    # For categorical fields, we now store as 32-bit integers.
    dtype = np.dtype([
        ('class', 'i4'),
        ('species', 'i4'),
        ('x', 'f4'), ('y', 'f4'), ('z', 'f4'),
        ('hunger', 'f4'), ('water', 'f4'), ('sleep', 'f4'),
        ('gender', 'f4'),
        ('mood', 'f4', (4,)),
        ('generation', 'i4'),
        ('energy', 'f4'),
        ('age', 'i4'),
        ('reproduction_rate', 'f4'),
        ('aggression', 'f4'),
        ('mutation_rate', 'f4'),
        ('music_taste', 'i4')
    ])

    # Build the data using a list comprehension and the mappings.
    data = [
        (
            mappings['class'].get(entry.get("class", ""), 0),
            mappings['species'].get(entry.get("species", ""), 0),
            entry.get("position", {}).get("x", 0.0),
            entry.get("position", {}).get("y", 0.0),
            entry.get("position", {}).get("z", 0.0),
            entry.get("hunger", 0.0),
            entry.get("water", 0.0),
            entry.get("sleep", 0.0),
            entry.get("gender", 0.0),
            np.array(entry.get("mood", [0, 0, 0, 0]), dtype='f4'),
            entry.get("generation", 0),
            entry.get("energy", 0.0),
            entry.get("age", 0),
            entry.get("reproduction_rate", 0.0),
            entry.get("aggression", 0.0),
            entry.get("mutation_rate", 0.0),
            mappings['music_taste'].get(entry.get("music_taste", ""), 0)
        )
        for entry in species_list
    ]

    # Create the structured array in one go.
    arr = np.array(data, dtype=dtype)
    return arr, mappings


# Example usage:
if __name__ == "__main__":
    # Load the JSON configuration from a file.
    with open("species_config.json", "r") as f:
        config = json.load(f)

    species_array, categorical_mappings = convert_species_config_with_categorical(config)
    print(species_array)
    print("Categorical mappings:")
    print(categorical_mappings)
