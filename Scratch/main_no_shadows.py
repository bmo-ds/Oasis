import math
import random
import datetime
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

# Import modular components
from LivingThings import LivingThing, Tree, Animal
from SkyShaders import sky_shader_full

app = Ursina()

WORLD_SIZE = 100
player_radius = 50

LivingThing.entity_grid = {}
LivingThing.time_scale = 1.0

game_start_time = 48000  # Start time: ex. 10 AM (36,000 seconds)

player = FirstPersonController(model=Cone())
player.cursor.model = None

ground = Entity(
    model='plane',
    scale=Vec3(WORLD_SIZE, 1, WORLD_SIZE),
    collider='box',
    texture='grass',
    texture_scale=(10, 10),
)

# trees = [Tree(position=Vec3(random.uniform(-WORLD_SIZE, WORLD_SIZE), 0, random.uniform(-WORLD_SIZE, WORLD_SIZE)), shader=lit_with_shadows_shader) for _ in range(8)]
# animals = ([Animal(position=Vec3(random.uniform(-WORLD_SIZE, WORLD_SIZE), 0, random.uniform(-WORLD_SIZE, WORLD_SIZE)), animal_type='prey', shader=lit_with_shadows_shader) for _ in range(6)] +
#            [Animal(position=Vec3(random.uniform(-WORLD_SIZE, WORLD_SIZE), 0, random.uniform(-WORLD_SIZE, WORLD_SIZE)), animal_type='predator', shader=lit_with_shadows_shader) for _ in range(2)])


trees = [Tree(position=Vec3(random.uniform(-player_radius, player_radius), 0, random.uniform(-player_radius, player_radius))) for _ in range(8)]
animals = ([Animal(position=Vec3(random.uniform(-player_radius, player_radius), 0, random.uniform(-player_radius, player_radius)), animal_type='prey') for _ in range(6)] +
           [Animal(position=Vec3(random.uniform(-player_radius, player_radius), 0, random.uniform(-player_radius, player_radius)), animal_type='predator') for _ in range(2)])


sun = DirectionalLight(
    shadows=True,
    shadow_map_resolution=(4096, 4096),
    shadow_area=WORLD_SIZE
)
sun.position = Vec3(50, 100, 50)
sun.look_at(Vec3(0, 0, 0))

sun_scale = 0.1
sky = Sky(shader=sky_shader_full)
sky.set_shader_input('resolution', Vec2(window.fullscreen_size[0], window.fullscreen_size[1]))
sky.set_shader_input('sun_size', sun_scale * 0.1)

time_scale_text = Text(text=f'Time Scale: {LivingThing.time_scale:.1f}', position=(0.45, -0.45), origin=(0.5, -0.5), scale=1)
game_time_text = Text(text='Game Time: d:00:00:00', position=(-0.45, -0.45), origin=(-0.5, -0.5), scale=1)

def input(key):
    global LivingThing

    if key == 'p':
        LivingThing.time_scale = 0  # Pause
    elif key == 'up arrow':
        LivingThing.time_scale = min(LivingThing.time_scale + 1, 100)
    elif key == 'down arrow':
        LivingThing.time_scale = max(LivingThing.time_scale - 1, 0)
    elif key == 'right arrow':
        LivingThing.time_scale = min(LivingThing.time_scale + 0.1, 100.0)
    elif key == 'left arrow':
        LivingThing.time_scale = max(LivingThing.time_scale - 0.1, 0.0)
    elif key == '0':
        LivingThing.time_scale = 1  # Pause
    elif key in '123456789':
        increment = int(key) * 100  # Convert key to int and multiply by 100
        LivingThing.time_scale = min(LivingThing.time_scale + increment, 100000)
    elif key == 'escape':
        application.quit()

def spawn_new():
    global trees, animals
    trees = [t for t in trees if not t.destroyed]
    animals = [a for a in animals if not a.destroyed]

    spawn_radius = 50  # Define spawn area around the player
    px, pz = player.x, player.z  # Get player position (y is ignored)

    if random.random() < 0.1:
        new_tree = Tree(
            Vec3(px + random.uniform(-spawn_radius, spawn_radius), 0, pz + random.uniform(-spawn_radius, spawn_radius)),
        )
        trees.append(new_tree)

    if random.random() < 0.05:
        new_prey = Animal(
            position=Vec3(px + random.uniform(-spawn_radius, spawn_radius), 0, pz + random.uniform(-spawn_radius, spawn_radius)),
            animal_type='prey',
        )
        animals.append(new_prey)

    if random.random() < 0.02:
        new_predator = Animal(
            position=Vec3(px + random.uniform(-spawn_radius, spawn_radius), 0, pz + random.uniform(-spawn_radius, spawn_radius)),
            animal_type='predator',
        )
        animals.append(new_predator)


def update_entity_grid():
    LivingThing.entity_grid = {k: v for k, v in LivingThing.entity_grid.items() if v[2]}

def update():
    global game_start_time, sun, sky
    time_scale_text.text = f'Time Scale: {LivingThing.time_scale:.1f}'
    spawn_new()
    update_entity_grid()

    # Update game time based on time scaling.
    game_start_time += time.dt * LivingThing.time_scale

    # Calculate normalized time (0 to 1 over 24 hours) based on game_start_time.
    normalized_time = (game_start_time % 86400) / 86400.0

    # Compute the sun's angle in degrees.
    # An offset of -90° makes the initial position (normalized_time=0) correspond to -90°.
    angle_degrees = normalized_time * 360 - 90
    radians = math.radians(angle_degrees)
    radius = 50  # Distance from the center along the sun's path.

    # Optional seasonal variation on the z-axis.
    day_progress = game_start_time / 86400.0  # Total days elapsed.
    sun_z = math.sin(day_progress * 2 * math.pi / 365) * 30

    # Update sun's position based on the computed angle.
    sun.position = Vec3(radius * math.cos(radians),
                        radius * math.sin(radians),
                        sun_z)
    sun.look_at(Vec3(0, 0, 0))

    # Disable shadows when the sun is below the horizon
    sun.shadows = sun.position.y > 10

    # Now derive the displayed time directly from the sun's horizontal angle.
    # Calculate the angle of the sun's position in the x-y plane relative to the origin.
    current_angle = math.atan2(sun.position.y, sun.position.x)
    if current_angle < 0:
        current_angle += 2 * math.pi  # Normalize to 0 - 2π

    # For example, 0 rad -> 0 hours, 2π rad -> 24 hours.
    time_in_hours = (current_angle / (2 * math.pi)) * 24
    # Optional: apply an offset so that the displayed time matches desired events (e.g. sunrise at 6AM).
    time_in_hours = (time_in_hours + 6) % 24

    # Break the fractional hours into hours, minutes, and seconds.
    hours = int(time_in_hours)
    minutes = int((time_in_hours - hours) * 60)
    seconds = int((((time_in_hours - hours) * 60) - minutes) * 60)

    # Calculate the day count from the total game time.
    # Each complete cycle (86400 seconds) is considered one day.
    days = int(game_start_time // 86400)

    game_time_text.text = f'Game Time: {days:02d}d:{hours:02d}:{minutes:02d}:{seconds:02d}'

    # Pass updated sun position and time to the sky shader.
    sky.set_shader_input('sun_position', sun.position)
    sky.set_shader_input('time', game_start_time % 86400)
    sky.set_shader_input('sun_size', sun_scale * 0.1)



app.run()