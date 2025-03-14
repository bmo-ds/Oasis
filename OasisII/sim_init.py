import json
import numpy as np

def generate_species_grid(json_data, num_per_species=10):
    """
    Generates species instances from species_templates if species_grid is missing.
    Places entities randomly in the world.
    """
    species_templates = json_data.get("species_templates", {})
    if "species_grid" in json_data:
        return json_data  # If already defined, return as is

    species_grid = []
    for species_name, template in species_templates.items():
        for _ in range(num_per_species):
            species_grid.append({
                "species": species_name,
                "position": {
                    "x": np.random.uniform(-50, 50),
                    "y": 0,
                    "z": np.random.uniform(-50, 50)
                },
                "class": template.get("class", "Unknown"),
                "hunger": template.get("base_hunger", 0.5),
                "water": template.get("base_water", 0.5),
                "sleep": template.get("base_sleep", 0.5),
                "energy": template.get("base_energy", 5.0),
                "aggression": template.get("base_aggression", 0.1),
                "mutation_rate": template.get("base_mutation_rate", 0.01),
                "reproduction_rate": template.get("base_reproduction_rate", 0.5),
                "geometry": template.get("geometry", {})
            })

    json_data["species_grid"] = species_grid  # Inject into JSON
    return json_data


def convert_species_config_with_categorical(json_data):
    """
    Converts species JSON into a structured NumPy array while optimizing categorical fields.
    Extracts and stores geometry data separately.

    Returns:
        tuple: (NumPy structured array, categorical mappings, geometry model data)
    """
    species_list = json_data.get("species_grid", [])

    # Define categorical mappings
    string_fields = ['class', 'species']
    mappings = {field: {val: idx for idx, val in enumerate(sorted({entry.get(field, "") for entry in species_list}))}
                for field in string_fields}

    # Define model type mapping
    model_types = {'cube': 0, 'sphere': 1, 'cone': 2, 'cylinder': 3}  # Expand as needed

    dtype = np.dtype([
        ('class', 'i4'), ('species', 'i4'),
        ('x', 'f4'), ('y', 'f4'), ('z', 'f4'),
        ('hunger', 'f4'), ('water', 'f4'), ('sleep', 'f4'),
        ('energy', 'f4'),
        ('reproduction_rate', 'f4'),
        ('aggression', 'f4'),
        ('mutation_rate', 'f4'),
        ('model_type', 'i4'),  # Model type (cube, sphere, etc.)
        ('color', 'f4', (3,))  # RGB color
    ])

    model_data = {}  # Store geometry separately
    data = []

    for entry in species_list:
        species_name = entry.get("species", "Unknown")
        geometry = entry.get("geometry", {})

        # Default to cube if no model is provided
        model_name = next(iter(geometry.values()), {}).get("model", "cube")
        model_type = model_types.get(model_name, 0)

        # Default color to white if not specified
        color = next(iter(geometry.values()), {}).get("color", "white")
        color_map = {"red": (1, 0, 0), "green": (0, 1, 0), "blue": (0, 0, 1), "white": (1, 1, 1)}
        color_rgb = color_map.get(color, (1, 1, 1))

        data.append((
            mappings['class'].get(entry.get("class", ""), 0),
            mappings['species'].get(species_name, 0),
            entry.get("position", {}).get("x", 0.0),
            entry.get("position", {}).get("y", 0.0),
            entry.get("position", {}).get("z", 0.0),
            entry.get("hunger", 0.0),
            entry.get("water", 0.0),
            entry.get("sleep", 0.0),
            entry.get("energy", 0.0),
            entry.get("reproduction_rate", 0.0),
            entry.get("aggression", 0.0),
            entry.get("mutation_rate", 0.0),
            model_type,
            color_rgb
        ))

    return np.array(data, dtype=dtype), mappings, model_data


class EcoSim:
    """
    Optimized ecosystem simulation using vectorized NumPy operations.
    Entities are initialized from a structured array instead of being randomly generated.
    """

    def __init__(self, heightmap_func, species_array):
        """
        Initializes the ecosystem simulation using the provided species data.

        Parameters:
            heightmap_func (callable): Function returning terrain height for given (x, z).
            species_array (np.ndarray): Structured array containing species attributes.
        """
        self.heightmap_func = heightmap_func
        self.entities = species_array.copy()  # Use structured NumPy array directly

        # Ensure y-position aligns with terrain height
        self.entities['y'] = heightmap_func(self.entities['x'], self.entities['z'])

    def step(self, dt):
        """
        Advances the simulation by a time step 'dt'. Updates positions of mobile entities.

        Parameters:
            dt (float): Time step increment.
        """
        # Determine moving species (assuming class index 1+ are animals)
        is_animal = self.entities['class'] > 0

        # Random movement for now (replace with AI behavior later)
        self.entities['x'][is_animal] += (np.random.rand(np.sum(is_animal)) - 0.5) * dt
        self.entities['z'][is_animal] += (np.random.rand(np.sum(is_animal)) - 0.5) * dt

        # Update heightmap adjustment
        self.entities['y'] = self.heightmap_func(self.entities['x'], self.entities['z'])

def summarize_simulation(sim, mappings):
    """
    Prints a detailed summary of the ecosystem state, including all entities and their status.

    Parameters:
        sim (EcoSim): The simulation instance.
        mappings (dict): Categorical mappings for species/classes.
    """
    inv_species_map = {v: k for k, v in mappings["species"].items()}
    inv_class_map = {v: k for k, v in mappings["class"].items()}

    print("\n=== Simulation Summary ===")
    total_entities = len(sim.entities)
    print(f"Total Entities: {total_entities}")

    # Aggregate species counts and dead counts
    species_counts = {}
    dead_counts = {}
    for entity in sim.entities:
        species_name = inv_species_map.get(entity["species"], "Unknown")
        species_counts[species_name] = species_counts.get(species_name, 0) + 1

    for species, count in species_counts.items():
        dead_count = dead_counts.get(species, 0)
        print(f"{species}: {count} entities (Dead: {dead_count})")

    # Detailed output for all entities
    print("\n=== Detailed Entity Data ===")
    for entity in sim.entities:
        species_name = inv_species_map.get(entity["species"], "Unknown")
        class_name = inv_class_map.get(entity["class"], "Unknown")
        # Determine status; you can modify the condition based on your simulation's criteria.
        status = "Existed"
        print(
            f"Species: {species_name} ({class_name}) | Pos: ({entity['x']:.2f}, {entity['y']:.2f}, {entity['z']:.2f}) | "
            f"Energy: {entity['energy']:.2f} | Hunger: {entity['hunger']:.2f} | Aggression: {entity['aggression']:.2f} | "
            f"Status: {status}"
        )

    print("\n=========================\n")



# Load species config
with open("species_config.json", "r") as f:
    config = json.load(f)

config = generate_species_grid(config)  # Auto-generate species if needed
species_array, categorical_mappings, model_data = convert_species_config_with_categorical(config)

def heightmap_func(x, z):
    return np.sin(x) + np.cos(z)  # Example terrain function

# Initialize simulation
sim = EcoSim(heightmap_func, species_array)

# Step simulation
sim.step(1000.1)

print(species_array)
print(sim.entities)

summarize_simulation(sim, categorical_mappings)
