import time
import random
import numpy as np

# Constants
WORLD_SIZE = 500
GRID_SIZE = 10  # Smaller grid to keep it manageable
TIME_STEP = 0.1  # Time step for simulation
REPRODUCTION_DISTANCE = 1  # Distance within which reproduction can occur
MIN_REPRODUCTION_AGE = 10
MAX_REPRODUCTION_AGE = 90  # Entities can reproduce until near the end of their lifespan

# LivingEntity with 3D coordinates and additional traits
class LivingEntity:
    def __init__(self, x, y, z, type, health=100, hunger=100, thirst=100, energy=100, age=0, injury=0):
        self.x = x
        self.y = y
        self.z = z
        self.type = type
        self.health = health
        self.hunger = hunger
        self.thirst = thirst
        self.energy = energy
        self.age = age
        self.injury = injury
        self.alive = True

    def move_towards(self, target_x, target_y, target_z):
        if self.x < target_x:
            self.x += 1
        elif self.x > target_x:
            self.x -= 1
        if self.y < target_y:
            self.y += 1
        elif self.y > target_y:
            self.y -= 1
        if self.z < target_z:
            self.z += 1
        elif self.z > target_z:
            self.z -= 1
        # Movement costs energy
        self.energy -= 0.5

    def update(self):
        # Increase age
        self.age += TIME_STEP

        # Basic simulation of needs
        if self.hunger > 0:
            self.hunger -= 0.1
        if self.thirst > 0:
            self.thirst -= 0.1
        if self.energy > 0:
            self.energy -= 0.2

        # Random injury event (1% chance per update)
        if random.random() < 0.01:
            injury_amount = random.uniform(0, 5)
            self.injury += injury_amount
            print(f"{self.type} incurred an injury of {injury_amount:.2f} points!")

        # Gradual healing from injuries
        if self.injury > 0:
            self.injury -= 0.05
            if self.injury < 0:
                self.injury = 0

        # Entity dies if any critical need runs out or if injury is too severe
        if self.hunger <= 0 or self.thirst <= 0 or self.energy <= 0 or self.injury > 20:
            self.alive = False

        if self.injury > 10:
            self.health -= 0.5

    def seek_resource(self, resource):
        if resource.type == 'water' and self.thirst < 50:
            print(f"{self.type} is moving towards water")
            self.move_towards(resource.x, resource.y, resource.z)
        elif resource.type == 'food' and self.hunger < 50:
            print(f"{self.type} is moving towards food")
            self.move_towards(resource.x, resource.y, resource.z)

    def distance_to(self, other):
        return np.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2 + (self.z - other.z) ** 2)

    def attempt_reproduction(self, partner):
        if (self.alive and partner.alive and self.type == partner.type and
            MIN_REPRODUCTION_AGE < self.age < MAX_REPRODUCTION_AGE and
            MIN_REPRODUCTION_AGE < partner.age < MAX_REPRODUCTION_AGE and
            self.distance_to(partner) <= REPRODUCTION_DISTANCE and
            self.health > 80 and partner.health > 80):

            # 5% chance of successful reproduction
            if random.random() < 0.05:
                child = LivingEntity(self.x, self.y, self.z, self.type, health=100, hunger=100, thirst=100, energy=100)
                print(f"{self.type} reproduced, new offspring created at ({self.x}, {self.y}, {self.z})")
                return child
        return None

# Resource now exists in 3D space as well
class Resource:
    def __init__(self, x, y, z, resource_type):
        self.x = x
        self.y = y
        self.z = z
        self.type = resource_type

# Initialize a 3D grid (for potential future use)
grid = np.zeros((GRID_SIZE, GRID_SIZE, GRID_SIZE), dtype=object)

# Initialize resources in 3D
resources = (
    [Resource(random.randint(0, GRID_SIZE - 1),
              random.randint(0, GRID_SIZE - 1),
              random.randint(0, GRID_SIZE - 1),
              'water') for _ in range(5)] +
    [Resource(random.randint(0, GRID_SIZE - 1),
              random.randint(0, GRID_SIZE - 1),
              random.randint(0, GRID_SIZE - 1),
              'food') for _ in range(5)]
)

# Initialize some animals in 3D space
animals = [
    LivingEntity(random.randint(0, GRID_SIZE - 1),
                 random.randint(0, GRID_SIZE - 1),
                 random.randint(0, GRID_SIZE - 1),
                 'herbivore')
    for _ in range(10)
]

def run_simulation():
    global animals
    while True:
        new_animals = []
        # Update all entities
        for animal in animals:
            if animal.alive:
                animal.update()
                # Seek nearest resource if needed
                for resource in resources:
                    if resource.type == 'water' and animal.thirst < 50:
                        animal.seek_resource(resource)
                        break
                    elif resource.type == 'food' and animal.hunger < 50:
                        animal.seek_resource(resource)
                        break

        # Reproduction phase: check each pair for possible reproduction
        for i in range(len(animals)):
            for j in range(i + 1, len(animals)):
                if animals[i].alive and animals[j].alive:
                    offspring = animals[i].attempt_reproduction(animals[j])
                    if offspring:
                        new_animals.append(offspring)

        animals.extend(new_animals)

        # Print status for debugging
        for animal in animals:
            if animal.alive:
                print(f"{animal.type} at ({animal.x}, {animal.y}, {animal.z}) - Health: {animal.health:.2f}, "
                      f"Hunger: {animal.hunger:.2f}, Thirst: {animal.thirst:.2f}, Energy: {animal.energy:.2f}, "
                      f"Age: {animal.age:.2f}, Injury: {animal.injury:.2f}")

        print("\nSimulation step complete\n")
        time.sleep(TIME_STEP)

run_simulation()
