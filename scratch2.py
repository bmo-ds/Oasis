from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.shaders import lit_with_shadows_shader

app = Ursina()

ground = Entity(
    model='plane',
    scale=Vec3(50, 1, 50),
    texture='grass',
    texture_scale=(5, 5),
    shader=lit_with_shadows_shader,
    collider='box'
)

cube = Entity(
    model='cube',
    scale=Vec3(2, 2, 2),
    position=Vec3(5, 1, 5),
    color=color.white,
    shader=lit_with_shadows_shader,
    collider='box'
)

player = FirstPersonController(position=Vec3(0, 2, 0), model=Cylinder())
player.cursor.model = None
player.shader = lit_with_shadows_shader  # Explicitly set shader on the player’s model

sun = DirectionalLight(
    shadows=True,
    shadow_map_resolution=(2048, 2048),
    position=Vec3(10, 20, 10),
    rotation=Vec3(45, -45, 0)
)

sky = Sky()

app.run()