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

WORLD_SIZE = 100

LivingThing.entity_grid = {}
LivingThing.time_scale = 1.0
LivingThing.default_shader = lit_with_shadows_shader

current_time = datetime.datetime.now()
game_time = (current_time.hour * 3600) + (current_time.minute * 60) + current_time.second
game_start_time = game_time

player = FirstPersonController(model=Cone())
player.cursor.model = None
player.shader = lit_with_shadows_shader  # Fix: Add shadow casting to player

ground = Entity(
    model='plane',
    scale=Vec3(WORLD_SIZE*2, 1, WORLD_SIZE*2),
    collider='box',
    texture='grass',
    texture_scale=(10, 10),
    shader=lit_with_shadows_shader
)

trees = [Tree(position=Vec3(random.uniform(-WORLD_SIZE, WORLD_SIZE), 0, random.uniform(-WORLD_SIZE, WORLD_SIZE)), shader=lit_with_shadows_shader) for _ in range(8)]
animals = ([Animal(position=Vec3(random.uniform(-WORLD_SIZE, WORLD_SIZE), 0, random.uniform(-WORLD_SIZE, WORLD_SIZE)), animal_type='prey', shader=lit_with_shadows_shader) for _ in range(6)] +
           [Animal(position=Vec3(random.uniform(-WORLD_SIZE, WORLD_SIZE), 0, random.uniform(-WORLD_SIZE, WORLD_SIZE)), animal_type='predator', shader=lit_with_shadows_shader) for _ in range(2)])

sun = DirectionalLight(
    shadows=True,
    shadow_map_resolution=(4096, 4096),
    shadow_area=WORLD_SIZE
)
sun.position = Vec3(50, 100, 50)  # Temporary static position for testing
sun.look_at(Vec3(0, 0, 0))  # Ensure it points at origin

sun_model = Entity(model='sphere', scale=1, color=color.yellow)
sun_model.unlit = True

sun_scale = 0.5
sky = Sky(shader=sky_shader_full)
sky.set_shader_input('resolution', Vec2(window.fullscreen_size[0], window.fullscreen_size[1]))
sky.set_shader_input('sun_size', sun_scale * 0.1)

time_scale_text = Text(text=f'Time Scale: {LivingThing.time_scale:.1f}', position=(0.01, -0.02), scale=0.05)
game_time_text = Text(text='Game Time: d:00:00:00', position=(0.01, -0.021), scale=0.05)

def input(key):
    global LivingThing
    if key == 'up arrow':
        LivingThing.time_scale = min(LivingThing.time_scale + 0.1, 10.0)
    elif key == 'down arrow':
        LivingThing.time_scale = max(LivingThing.time_scale - 0.1, 0.1)
    elif key == 'o':
        LivingThing.time_scale += 10
    elif key == 'p':
        LivingThing.time_scale = max(LivingThing.time_scale - 10, 1)
    elif key == 'k':
        LivingThing.time_scale += 100
    elif key == 'l':
        LivingThing.time_scale += 100
    elif key == 'escape':
        application.quit()

def spawn_new():
    global trees, animals
    trees = [t for t in trees if not t.destroyed]
    animals = [a for a in animals if not a.destroyed]
    if random.random() < 0.05:
        new_tree = Tree(Vec3(random.uniform(-WORLD_SIZE, WORLD_SIZE), 0, random.uniform(-WORLD_SIZE, WORLD_SIZE)), shader=lit_with_shadows_shader)
        trees.append(new_tree)
    if random.random() < 0.03:
        new_prey = Animal(position=Vec3(random.uniform(-WORLD_SIZE, WORLD_SIZE), 0, random.uniform(-WORLD_SIZE, WORLD_SIZE)), animal_type='prey', shader=lit_with_shadows_shader)
        animals.append(new_prey)
    if random.random() < 0.005:
        new_predator = Animal(position=Vec3(random.uniform(-WORLD_SIZE, WORLD_SIZE), 0, random.uniform(-WORLD_SIZE, WORLD_SIZE)), animal_type='predator', shader=lit_with_shadows_shader)
        animals.append(new_predator)

def update_entity_grid():
    LivingThing.entity_grid = {k: v for k, v in LivingThing.entity_grid.items() if v[2]}

def update():
    global game_start_time, sun, sun_model, sky
    time_scale_text.text = f'Time Scale: {LivingThing.time_scale:.1f}'
    spawn_new()
    update_entity_grid()

    PHYSICS_STEP = 1 / 120
    remaining_dt = time.dt * LivingThing.time_scale
    while remaining_dt > 0:
        step_dt = min(remaining_dt, PHYSICS_STEP)
        game_start_time += step_dt
        remaining_dt -= step_dt

    total_seconds = int(game_start_time)
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    game_time_text.text = f'Game Time: {days:02d}d:{hours:02d}:{minutes:02d}:{seconds:02d}'

    sky.set_shader_input('sun_position', sun.position)
    sky.set_shader_input('time', game_start_time)
    sky.set_shader_input('sun_size', sun_scale * 0.1)

app.run()