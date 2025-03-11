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


class EcoSim:
    """
    A framework for an ecosystem simulation that updates LivingEntities (plants or animals)
    in a 3D space based on a terrain heightmap. Uses NumPy for optimized calculations.
    """

    def __init__(self, heightmap_func, num_entities, world_size):
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

        # Define a structured array to hold entity data:
        # Fields: x, y, z for position; vx, vy, vz for velocity; species (0: plant, 1: animal)
        dtype = [('x', 'f4'), ('y', 'f4'), ('z', 'f4'),
                 ('vx', 'f4'), ('vy', 'f4'), ('vz', 'f4'),
                 ('species', 'i4')]
        self.entities = np.zeros(num_entities, dtype=dtype)

        # Randomly initialize x and z positions
        half_size = world_size / 2
        xs = np.random.uniform(-half_size, half_size, num_entities)
        zs = np.random.uniform(-half_size, half_size, num_entities)
        ys = self.heightmap_func(xs, zs)  # Ensure correct alignment with the terrain

        self.entities['x'] = xs
        self.entities['y'] = ys
        self.entities['z'] = zs

        # Randomly assign species: for instance, 0 = plant (static) and 1 = animal (mobile)
        species = np.random.randint(0, 2, num_entities)
        self.entities['species'] = species

        # Initialize velocities: animals get random initial velocities; plants remain static
        self.entities['vx'] = np.where(species == 1, np.random.uniform(-1, 1, num_entities), 0)
        self.entities['vy'] = np.where(species == 1, np.random.uniform(-1, 1, num_entities), 0)
        self.entities['vz'] = np.where(species == 1, np.random.uniform(-1, 1, num_entities), 0)

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
