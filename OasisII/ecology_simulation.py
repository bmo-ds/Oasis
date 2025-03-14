import json
import numpy as np

"""
JSON Parameter Documentation:

species_grid (array): List of species entries.

Each species entry is an object with the following keys:
  - "class": string
      The category of the entity (e.g., "Tree", "Prey", "Rock", etc.)
  - "species": string
      Specific species name (e.g., "Conifer", "Rabbit", "Granite", etc.)
  - "position": object
      Contains:
          "x": number (float) - X-coordinate
          "y": number (float) - Y-coordinate
          "z": number (float) - Z-coordinate
  - "hunger": number (float)
      Hunger level, typically between 0.0 and 1.0.
  - "water": number (float)
      Water level, typically between 0.0 and 1.0.
  - "sleep": number (float)
      Sleep/rest level, typically between 0.0 and 1.0.
  - "gender": number (float)
      A numerical encoding of gender (could be a float between 0.0 and 1.0).
  - "mood": array
      A 4-element array representing mood values.
  - "generation": number (integer)
      The generation number.
  - "energy": number (float)
      Energy level.
  - "age": number (integer)
      Age in simulation time units.
  - "reproduction_rate": number (float)
      Rate or threshold for reproduction.
  - "aggression": number (float)
      Aggression level.
  - "mutation_rate": number (float)
      Mutation rate.
  - "music_taste": string
      A categorical descriptor (e.g., "punk", "techno", etc.).
  - "geometry": object (optional)
      Contains visual model information for the entity.
      For example, for a Tree, you might include:
          "trunk": object with keys:
              "model": string (e.g., "cube")
              "color": string (e.g., "brown")
              "initial_scale": array of 3 numbers [x, y, z]
              "max_scale": array of 3 numbers [x, y, z]
              "position": array of 3 numbers [x, y, z]
          "foliage": object with similar keys as "trunk".
      You can add additional parts as needed.
"""


def convert_species_config_with_categorical(json_data):
    """
    Converts a JSON species configuration into a NumPy structured array while
    converting categorical (string) fields into numeric codes for optimization.
    Also extracts and stores geometry data in a separate dictionary.

    Parameters:
        json_data (dict): The JSON dictionary containing the 'species_grid' key.

    Returns:
        tuple: A tuple containing:
            - np.ndarray: A NumPy structured array with the simulation data.
            - dict: A dictionary mapping each categorical field to its code mapping.
            - dict: A dictionary storing geometry/model data separately by species.
    """
    species_list = json_data.get("species_grid", [])

    # Define categorical fields
    string_fields = ['class', 'species', 'music_taste']

    # Build mappings for categorical fields
    mappings = {}
    for field in string_fields:
        unique_vals = {entry.get(field, "") for entry in species_list}
        unique_vals = sorted(unique_vals)
        mappings[field] = {val: idx for idx, val in enumerate(unique_vals)}

    # Define structured dtype
    dtype = np.dtype([
        ('class', 'i4'),
        ('species', 'i4'),
        ('x', 'f4'), ('y', 'f4'), ('z', 'f4'),
        ('hunger', 'f4'), ('water', 'f4'), ('sleep', 'f4'),
        ('gender', 'f4'),
        ('mood', 'f4', (4,)),
        ('generation', 'i4'),
        ('family_id', 'i4'),
        ('energy', 'f4'),
        ('age', 'i4'),
        ('color1', 'f4', (3,)),
        ('color2', 'f4', (3,)),
        ('reproduction_rate', 'f4'),
        ('aggression', 'f4'),
        ('mutation_rate', 'f4'),
        ('music_taste', 'i4')
    ])

    # Separate model data storage
    model_data = {}

    # Build the structured array
    data = []
    for entry in species_list:
        species_name = entry.get("species", "Unknown")

        # Store model/geometry data separately
        if "geometry" in entry:
            model_data[species_name] = entry["geometry"]

        # Append numerical data for NumPy struct array
        data.append((
            mappings['class'].get(entry.get("class", ""), 0),
            mappings['species'].get(species_name, 0),
            entry.get("position", {}).get("x", 0.0),
            entry.get("position", {}).get("y", 0.0),
            entry.get("position", {}).get("z", 0.0),
            entry.get("hunger", 0.0),
            entry.get("water", 0.0),
            entry.get("sleep", 0.0),
            entry.get("gender", 0.0),
            np.array(entry.get("mood", [0, 0, 0, 0]), dtype='f4'),
            entry.get("generation", 0),
            entry.get("family_id", 0),
            entry.get("energy", 0.0),
            entry.get("age", 0),
            np.array(entry.get("color1", [0, 0, 0]), dtype='f4'),
            np.array(entry.get("color2", [0, 0, 0]), dtype='f4'),
            entry.get("reproduction_rate", 0.0),
            entry.get("aggression", 0.0),
            entry.get("mutation_rate", 0.0),
            mappings['music_taste'].get(entry.get("music_taste", ""), 0)
        ))

    # Convert to NumPy structured array
    arr = np.array(data, dtype=dtype)

    return arr, mappings, model_data

with open("species_config.json", "r") as f:
    config = json.load(f)

species_array, categorical_mappings, model_data = convert_species_config_with_categorical(config)

print(species_array)
print("Categorical mappings:", categorical_mappings)
print("Model data:", model_data)


class EcoSim:
    """
    A framework for an ecosystem simulation that updates LivingEntities (plants or animals)
    in a 3D space based on a terrain heightmap. Uses NumPy for optimized calculations.
    """

    def __init__(self, heightmap_func, world_size):
        """
        Initializes the simulation.

        Parameters:
            heightmap_func (callable): A vectorized function that accepts numpy arrays (x, z)
                                       and returns the corresponding y (height) values.
            num_entities (int): The initial number of LivingEntities.
            world_size (float): The extent of the world; entities are spawned within [-world_size/2, world_size/2].
        """
        self.heightmap_func = heightmap_func
        self.world_size = world_size
        self.entities = []
        self.num_entities = len(self.entities)

        # Define a structured array to hold entity data:
        # Fields: x, y, z for position; vx, vy, vz for velocity; species (0: plant, 1: animal)
        dtype = [('x', 'f4'), ('y', 'f4'), ('z', 'f4'),
                 ('vx', 'f4'), ('vy', 'f4'), ('vz', 'f4'),
                 ('species', 'i4')]
        self.entities = np.zeros(self.num_entities, dtype=dtype)

        # Randomly initialize x and z positions
        half_size = world_size / 2
        xs = np.random.uniform(-half_size, half_size, self.num_entities)
        zs = np.random.uniform(-half_size, half_size, self.num_entities)
        ys = self.heightmap_func(xs, zs)  # Ensure correct alignment with the terrain

        self.entities['x'] = xs
        self.entities['y'] = ys
        self.entities['z'] = zs

        # Randomly assign species: for instance, 0 = plant (static) and 1 = animal (mobile)
        species = np.random.randint(0, 2, self.num_entities)
        self.entities['species'] = species

        # Initialize velocities: animals get random initial velocities; plants remain static
        self.entities['vx'] = np.where(species == 1, np.random.uniform(-1, 1, self.num_entities), 0)
        self.entities['vy'] = np.where(species == 1, np.random.uniform(-1, 1, self.num_entities), 0)
        self.entities['vz'] = np.where(species == 1, np.random.uniform(-1, 1, self.num_entities), 0)

    def step(self, dt):
        """
        Advances the simulation by a time step 'dt'. Updates the positions of mobile entities,
        realigns their y–position based on the terrain height, and includes a placeholder for reproduction.

        Parameters:
            dt (float): The time step increment.
        """
        # Identify animal entities (mobile) by species flag
        is_animal = self.entities['species'] == 1

        # Update positions for animals using their velocity
        self.entities['x'][is_animal] += self.entities['vx'][is_animal] * dt
        self.entities['y'][is_animal] += self.entities['vy'][is_animal] * dt
        self.entities['z'][is_animal] += self.entities['vz'][is_animal] * dt

        # Re-align y positions using the heightmap so that entities stay on the surface
        self.entities['y'] = self.heightmap_func(self.entities['x'], self.entities['z'])

        # Placeholder: Evaluate reproduction conditions and spawn new entities if needed
        # For example, if a species reproduces, add new entity entries to self.entities.
        # (Implementation to be added later.)
        # self._handle_reproduction()

    # Optional: A private method to handle reproduction could be defined here
    # def _handle_reproduction(self):
    #     # Evaluate reproduction conditions and add new entities using NumPy concatenation
    #     pass
