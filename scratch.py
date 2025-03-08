from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.shaders import lit_with_shadows_shader
import math

app = Ursina()

WORLD_SIZE = 100
game_start_time = 0
time_scale = 1000.0

# Sky shader (unchanged)
sky_shader = Shader(
    vertex='''
    #version 430
    uniform mat4 p3d_ModelViewProjectionMatrix;
    uniform mat4 p3d_ModelMatrix;
    in vec4 p3d_Vertex;
    out vec3 world_pos;

    void main() {
        gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
        world_pos = (p3d_ModelMatrix * p3d_Vertex).xyz;
    }
    ''',
    fragment='''
    #version 430
    in vec3 world_pos;
    out vec4 fragColor;

    uniform vec2 resolution;
    uniform float time;
    uniform vec3 sun_position;
    uniform float sun_size;

    void main() {
        vec3 norm_world_pos = normalize(world_pos);
        vec3 norm_sun_pos = normalize(sun_position);

        float sun_angle = dot(norm_world_pos, norm_sun_pos);
        float sun_intensity = 3.0;

        float sun_core = smoothstep(sun_size, 1.0, sun_angle);
        float sun_halo = smoothstep(sun_size - 0.005, sun_size, sun_angle) * 0.3;
        vec3 sun_color = vec3(1.0, 0.9, 0.6) * sun_intensity * (sun_core + sun_halo);

        vec3 night_low     = vec3(0.0, 0.0, 0.05);
        vec3 night_high    = vec3(0.05, 0.05, 0.2);
        vec3 dawn_dusk_low = vec3(0.8, 0.2, 0.1);
        vec3 dawn_dusk_high= vec3(1.0, 0.6, 0.3);
        vec3 day_low       = vec3(0.4, 0.7, 1.0);
        vec3 day_high      = vec3(0.6, 0.8, 1.0);

        float elevation = norm_world_pos.y * 0.5 + 0.5;
        vec3 night_color    = mix(night_low,     night_high,    elevation);
        vec3 dawn_dusk_color= mix(dawn_dusk_low, dawn_dusk_high, elevation);
        vec3 day_color      = mix(day_low,       day_high,      elevation);

        float sun_elevation = norm_sun_pos.y;
        float day_factor = smoothstep(-0.1, 0.3, sun_elevation);

        vec3 sky_color;
        if(day_factor < 0.5){
            sky_color = mix(night_color, dawn_dusk_color, day_factor * 2.0);
        } else {
            sky_color = mix(dawn_dusk_color, day_color, (day_factor - 0.5) * 2.0);
        }

        vec3 color = sky_color + sun_color;
        color = clamp(color, 0.0, 1.0);
        fragColor = vec4(color, 1.0);
    }
    '''
)

sky = Entity(
    model='sphere',
    scale=500,
    double_sided=True,
    shader=sky_shader
)
sky.set_shader_input('resolution', Vec2(window.fullscreen_size[0], window.fullscreen_size[1]))
sky.set_shader_input('sun_size', 0.995)  # Much smaller sun disc

sun = DirectionalLight(shadows=True)
sun.shadow_map_resolution = Vec2(2048, 2048)
sun.shadow_distance = 200

sun_model = Entity(
    model='sphere',
    scale=0.2,
    color=color.yellow,
    unlit=True
)

ambient_light = AmbientLight(color=color.rgb(50, 50, 50))

player = FirstPersonController()
player.cursor.model = None
player.model = Entity(
    model='cube',
    scale_y=2,
    shader=lit_with_shadows_shader,
    cast_shadows=True,
    receive_shadows=True
)
player.collider = 'box'

ground = Entity(
    model='plane',
    scale=(WORLD_SIZE * 2, 1, WORLD_SIZE * 2),
    collider='box',
    texture='grass',
    texture_scale=(10, 10),
    shader=lit_with_shadows_shader,
    cast_shadows=True,
    receive_shadows=True
)

test_cube = Entity(
    model='cube',
    position=(0, 1, 0),
    scale=1,
    color=color.white,
    shader=lit_with_shadows_shader,
    cast_shadows=True,
    receive_shadows=True
)

def input(key):
    if key == 'escape':
        application.quit()

def update():
    global game_start_time, sun, sun_model, sky
    game_start_time += time.dt * time_scale
    normalized_time = (game_start_time % 86400) / 86400

    sun_x = 0
    sun_y = math.sin(normalized_time * math.pi * 2) * 50
    sun_z = math.cos(normalized_time * math.pi * 2) * 50

    sun.position = Vec3(sun_x, sun_y, sun_z)
    sun.look_at(Vec3(0, 0, 0))
    sun_model.position = sun.position

    light_intensity = max(0.1, sun_y / 50)
    ambient_light.color = color.rgb(
        int(50 + light_intensity * 100),
        int(50 + light_intensity * 75),
        int(100 + light_intensity * 50)
    )

    sky.set_shader_input('sun_position', sun.position)
    sky.set_shader_input('time', game_start_time)

app.run()