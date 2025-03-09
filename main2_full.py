import math
import random
import datetime
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.shaders import lit_with_shadows_shader

# Import modular components
from LivingThings import LivingThing, Tree, Animal
from SkyShaders import sky_shader_full

app = Ursina()

WORLD_SIZE = 500
height_scale = 3

LivingThing.entity_grid = {}
LivingThing.time_scale = 1.0
LivingThing.default_shader = lit_with_shadows_shader

game_start_time = 9000  # Start time: ex. 10 AM (36,000 seconds)

player = FirstPersonController(model=Cone())
player.cursor.model = None
player.shader = lit_with_shadows_shader

# Terrain generation function with smooth height and secondary noise
def generate_terrain(size, subdivisions, height_scale):
    vertices = []
    triangles = []
    uvs = []

    # Generate vertices with two layers of height variation
    for x in range(subdivisions + 1):
        for z in range(subdivisions + 1):
            pos_x = (x / subdivisions - 0.5) * size
            pos_z = (z / subdivisions - 0.5) * size

            # Primary smooth height (low frequency)
            height1 = math.sin(pos_x * 0.01) * math.cos(pos_z * 0.01) * height_scale
            # Secondary noise (higher frequency, phase-shifted)
            height2 = math.sin(pos_x * 0.03 + 1.0) * math.cos(pos_z * 0.03 + 2.0) * height_scale * 0.3
            pos_y = height1 + height2

            vertices.append(Vec3(pos_x, pos_y, pos_z))
            uvs.append(Vec2(x / subdivisions, z / subdivisions))

    # Generate triangles (two per quad)
    for x in range(subdivisions):
        for z in range(subdivisions):
            i = x * (subdivisions + 1) + z
            triangles.extend([
                i, i + subdivisions + 1, i + 1,
                i + 1, i + subdivisions + 2, i + subdivisions + 1
            ])

    # Compute vertex normals manually.
    normals = [Vec3(0, 0, 0) for _ in vertices]

    # Loop over each triangle and accumulate face normals.
    for i in range(0, len(triangles), 3):
        i1 = triangles[i]
        i2 = triangles[i + 1]
        i3 = triangles[i + 2]

        v1 = vertices[i1]
        v2 = vertices[i2]
        v3 = vertices[i3]

        # Calculate edge vectors.
        edge1 = v2 - v1
        edge2 = v3 - v1

        # Compute the face normal using the cross product.
        face_normal = Vec3(
            edge1.y * edge2.z - edge1.z * edge2.y,
            edge1.z * edge2.x - edge1.x * edge2.z,
            edge1.x * edge2.y - edge1.y * edge2.x
        )

        # Normalize the face normal (using math.sqrt).
        mag = math.sqrt(face_normal.x**2 + face_normal.y**2 + face_normal.z**2)
        if mag != 0:
            face_normal = Vec3(face_normal.x/mag, face_normal.y/mag, face_normal.z/mag)
        else:
            face_normal = Vec3(0, 0, 0)

        # Add the face normal to each vertex of the triangle.
        normals[i1] += face_normal
        normals[i2] += face_normal
        normals[i3] += face_normal

    # Normalize all vertex normals.
    for i, n in enumerate(normals):
        mag = math.sqrt(n.x**2 + n.y**2 + n.z**2)
        if mag != 0:
            normals[i] = Vec3(n.x/mag, n.y/mag, n.z/mag)
        else:
            normals[i] = Vec3(0, 1, 0)  # Fallback normal

    # Create and return the mesh with computed normals.
    terrain_mesh = Mesh(vertices=vertices, triangles=triangles, uvs=uvs, normals=normals, mode='triangle')
    return terrain_mesh

# Create the terrain
ground = Entity(
    model=generate_terrain(WORLD_SIZE, subdivisions=50, height_scale=height_scale),
    collider='mesh',
    texture='grass',
    double_sided=True,  # Render both sides of each triangle.
    texture_scale=(10, 10),
    shader=lit_with_shadows_shader
)

# Set player starting position above terrain
player.position = Vec3(0, 30, 0)

# Precompute terrain heights using a 2D list
terrain_heights = [[0] * WORLD_SIZE for _ in range(WORLD_SIZE)]

# Align noise with world coordinates (-250 to 250)
for x in range(WORLD_SIZE):
    for z in range(WORLD_SIZE):
        world_x = x - 250  # Map 0-499 to -250 to 249
        world_z = z - 250
        height1 = math.sin(world_x * 0.01) * math.cos(world_z * 0.01) * height_scale
        height2 = math.sin(world_x * 0.03 + 1.0) * math.cos(world_z * 0.03 + 2.0) * height_scale * 0.3
        terrain_heights[x][z] = height1 + height2

# Function to get terrain height at any point (matches generate_terrain)
def get_terrain_height(x, z, height_scale):
    # Convert world coordinates to array indices
    ix = int(x + 250)
    iz = int(z + 250)
    # Clamp indices to valid range
    ix = max(0, min(ix, 499))
    iz = max(0, min(iz, 499))
    return terrain_heights[ix][iz]

# Spawn entities on terrain surface
trees = [Tree(position=Vec3(
                x := random.uniform(-250, 250 - 1e-6),  # Avoid edge case at 250
                get_terrain_height(x, z := random.uniform(-250, 250 - 1e-6), height_scale),
                z),
              shader=lit_with_shadows_shader) for _ in range(18)]

# Corrected animal spawning
animals = (
    [Animal(position=Vec3(random.uniform(-250, 250 - 1e-6),
                         get_terrain_height(random.uniform(-250, 250 - 1e-6),
                                           random.uniform(-250, 250 - 1e-6), height_scale),
                         random.uniform(-250, 250 - 1e-6)),
             animal_type='prey', shader=lit_with_shadows_shader) for _ in range(16)] +
    [Animal(position=Vec3(random.uniform(-250, 250 - 1e-6),
                         get_terrain_height(random.uniform(-250, 250 - 1e-6),
                                           random.uniform(-250, 250 - 1e-6), height_scale),
                         random.uniform(-250, 250 - 1e-6)),
             animal_type='predator', shader=lit_with_shadows_shader) for _ in range(12)]
)

sun = DirectionalLight(
    shadows=True,
    shadow_map_resolution=(4096, 4096),
    shadow_area=WORLD_SIZE
)
sun.position = Vec3(50, 100, 50)
sun.look_at(Vec3(0, 0, 0))
sun_scale = 0.1
sun.shadow_area = WORLD_SIZE * 2  # Double the shadow area

sky = Sky(shader=sky_shader_full)
sky.set_shader_input('resolution', Vec2(window.fullscreen_size[0], window.fullscreen_size[1]))
sky.set_shader_input('sun_size', sun_scale * 0.1)

time_scale_text = Text(text=f'Time Scale: {LivingThing.time_scale:.1f}', position=(0.45, -0.45), origin=(0.5, -0.5),
                       scale=1)
game_time_text = Text(text='Game Time: d:00:00:00', position=(-0.45, -0.45), origin=(-0.5, -0.5), scale=1)


def input(key):
    global LivingThing
    if key == 'p':
        LivingThing.time_scale = 0
    elif key == 'up arrow':
        LivingThing.time_scale = min(LivingThing.time_scale + 1, 100)
    elif key == 'down arrow':
        LivingThing.time_scale = max(LivingThing.time_scale - 1, 0)
    elif key == 'right arrow':
        LivingThing.time_scale = min(LivingThing.time_scale + 0.1, 100.0)
    elif key == 'left arrow':
        LivingThing.time_scale = max(LivingThing.time_scale - 0.1, 0.0)
    elif key == '0':
        LivingThing.time_scale = 1
    elif key in '123456789':
        increment = int(key) * 100
        LivingThing.time_scale = min(LivingThing.time_scale + increment, 100000)
    elif key == 'escape':
        application.quit()


def spawn_new():
    global trees, animals
    trees = [t for t in trees if not t.destroyed]
    animals = [a for a in animals if not a.destroyed]
    if random.random() < 0.1:  # Tree spawn chance
        x = random.uniform(-250, 250 - 1e-6)
        z = random.uniform(-250, 250 - 1e-6)
        y = get_terrain_height(x, z, height_scale)
        new_tree = Tree(position=Vec3(x, y, z), shader=lit_with_shadows_shader)
        trees.append(new_tree)
    if random.random() < 0.07:
        x = random.uniform(-250, 250 - 1e-6)
        z = random.uniform(-250, 250 - 1e-6)
        y = get_terrain_height(x, z, height_scale)
        new_prey = Animal(position=Vec3(x, y, z), animal_type='prey',
                          shader=lit_with_shadows_shader)
        animals.append(new_prey)
    if random.random() < 0.01:
        x = random.uniform(-250, 250 - 1e-6)
        z = random.uniform(-250, 250 - 1e-6)
        y = get_terrain_height(x, z, height_scale)
        new_predator = Animal(position=Vec3(x, y, z), animal_type='predator',
                              shader=lit_with_shadows_shader)
        animals.append(new_predator)


def update_entity_grid():
    LivingThing.entity_grid = {k: v for k, v in LivingThing.entity_grid.items() if v[2]}


def update():
    global game_start_time, sun, sky
    time_scale_text.text = f'Time Scale: {LivingThing.time_scale:.1f}'
    spawn_new()
    update_entity_grid()

    game_start_time += time.dt * LivingThing.time_scale
    normalized_time = (game_start_time % 86400) / 86400.0
    angle_degrees = normalized_time * 360 - 90
    angle_radians = math.radians((game_start_time % 86400) / 86400.0 * 360 - 90)
    cos_a, sin_a = math.cos(angle_radians), math.sin(angle_radians)

    day_progress = game_start_time / 86400.0
    radius = 50
    sun_z = math.sin(day_progress * 2 * math.pi / 365) * 30
    sun.position = Vec3(radius * cos_a, radius * sin_a, sun_z)

    sun.look_at(Vec3(0, 0, 0))

    current_angle = math.atan2(sun.position.y, sun.position.x)
    if current_angle < 0:
        current_angle += 2 * math.pi
    time_in_hours = (current_angle / (2 * math.pi)) * 24
    time_in_hours = (time_in_hours + 6) % 24
    hours = int(time_in_hours)
    minutes = int((time_in_hours - hours) * 60)
    seconds = int((((time_in_hours - hours) * 60) - minutes) * 60)
    days = int(game_start_time // 86400)
    game_time_text.text = f'Game Time: {days:02d}d:{hours:02d}:{minutes:02d}:{seconds:02d}'

    sky.set_shader_input('sun_position', sun.position)
    sky.set_shader_input('time', game_start_time % 86400)
    sky.set_shader_input('sun_size', sun_scale * 0.1)

    # Update animal positions to stick to the terrain
    for animal in animals:
        animal.y = get_terrain_height(animal.x, animal.z, height_scale)

app.run()