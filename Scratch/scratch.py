from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.shaders import lit_with_shadows_shader
import math

app = Ursina()

WORLD_SIZE = 100
game_start_time = 0
time_scale = 1000.0
sun_scale = 0.05  # Adjust sun size (lower value = smaller sun)
paused = False    # Global flag to control whether time is paused

# Updated sky shader with improved stars
sky_shader = Shader(
    vertex=''' 
    #version 430
    uniform mat4 p3d_ModelViewProjectionMatrix;
    uniform mat4 p3d_ModelMatrix;
    in vec4 p3d_Vertex;
    out vec3 world_pos;
    out vec3 star_dir;

    void main() {
        gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
        world_pos = (p3d_ModelMatrix * p3d_Vertex).xyz;
        star_dir = normalize(mat3(p3d_ModelMatrix) * p3d_Vertex.xyz);
    }
    ''',
    fragment=''' 
    #version 430
    in vec3 world_pos;
    in vec3 star_dir;
    out vec4 fragColor;

    uniform vec2 resolution;
    uniform float time;
    uniform vec3 sun_position;
    uniform float sun_size;

    void main() {
        // Normalize directions.
        vec3 norm_world_pos = normalize(world_pos);
        vec3 norm_sun_pos = normalize(sun_position);
        float sun_angle = dot(norm_world_pos, norm_sun_pos);
        float sun_intensity = 1.0;

        // Core and corona of the sun
        float sun_core = smoothstep(1.0 - sun_size * 0.01, 1.0, sun_angle);
        float corona = smoothstep(1.0 - sun_size * 0.05, 1.0 - sun_size * 0.01, sun_angle) * 0.5;
        corona += pow(smoothstep(1.0 - sun_size * 0.1, 1.0 - sun_size * 0.05, sun_angle), 2.0) * 0.03;

        // God rays effect
        float angle_to_sun = acos(sun_angle);
        float ray_falloff = smoothstep(0.2, 0.0, angle_to_sun);

        vec3 proj = norm_world_pos - sun_angle * norm_sun_pos;
        float proj_len = length(proj);
        float ray_intensity = 0.0;

        if (proj_len > 0.001) {
            proj = normalize(proj);
            vec3 up = vec3(0, 1, 0);
            if (abs(dot(norm_sun_pos, up)) > 0.999) {
                up = vec3(1, 0, 0);
            }
            vec3 right = normalize(cross(up, norm_sun_pos));
            vec3 up_perp = cross(norm_sun_pos, right);
            float phi = atan(dot(proj, up_perp), dot(proj, right));
            float ray_pattern = abs(sin(5.0 * phi + time/2 * 0.001));
            ray_intensity = pow(ray_pattern, 4.0) * ray_falloff * 0.05;
        }

        // Sun and ray colors
        vec3 sun_color = vec3(1.0, 0.9, 0.6) * sun_intensity * (sun_core + corona);
        vec3 ray_color = vec3(1.0, 0.95, 0.8) * ray_intensity;

        // Sky colors
        vec3 night_low      = vec3(0.0, 0.0, 0.05);
        vec3 night_high     = vec3(0.05, 0.05, 0.2);
        vec3 dawn_dusk_low  = vec3(0.8, 0.2, 0.1);
        vec3 dawn_dusk_high = vec3(1.0, 0.6, 0.3);
        vec3 day_low        = vec3(0.4, 0.7, 1.0);
        vec3 day_high       = vec3(0.6, 0.8, 1.0);

        float elevation = norm_world_pos.y * 0.5 + 0.5;
        vec3 night_color      = mix(night_low, night_high, elevation);
        vec3 dawn_dusk_color  = mix(dawn_dusk_low, dawn_dusk_high, elevation);
        vec3 day_color        = mix(day_low, day_high, elevation);

        float sun_elevation = norm_sun_pos.y;
        float day_factor = smoothstep(-0.1, 0.3, sun_elevation);

        vec3 sky_color;
        if (day_factor < 0.5) {
            sky_color = mix(night_color, dawn_dusk_color, day_factor * 2.0);
        } else {
            sky_color = mix(dawn_dusk_color, day_color, (day_factor - 0.5) * 2.0);
        }

        // Combine sky, sun, and rays.
        vec3 color = sky_color + sun_color + ray_color;

        // ---- STAR FIELD ----
        const float PI = 3.14159;
        float theta = atan(star_dir.z, star_dir.x);
        float phi = acos(clamp(star_dir.y, -1.0, 1.0));
        float u_coord = (theta + PI) / (2.0 * PI);
        float v_coord = phi / PI;
        
        // Use a 100x10 grid for ~1000 stars
        vec2 gridSize = vec2(100.0, 100.0);
        vec2 cell = floor(vec2(u_coord * gridSize.x, v_coord * gridSize.y));
        vec2 cellSize = vec2(1.0 / gridSize.x, 1.0 / gridSize.y);
        
        vec2 randVal = vec2(
            fract(sin(dot(cell, vec2(12.9898,78.233))) * 43758.5453),
            fract(sin(dot(cell, vec2(93.9898,67.345))) * 43758.5453)
        );
        vec2 cellCenter = (cell + randVal) * cellSize;
        
        float star_theta = cellCenter.x * 2.0 * PI - PI;
        float star_phi = cellCenter.y * PI;
        vec3 starCenterDir = vec3(sin(star_phi)*cos(star_theta), cos(star_phi), sin(star_phi)*sin(star_theta));
        
        float angleDiff = acos(clamp(dot(normalize(star_dir), starCenterDir), -1.0, 1.0));
        
        // Smaller stars
        float star_radius = 0.002;
        float starIntensity = smoothstep(star_radius, 0.0, angleDiff);
        
        // Random brightness per star
        float star_brightness = 0.75 + 0.5 * fract(sin(dot(cell, vec2(45.67,89.01))) * 23456.789);
        
        // Realistic twinkling with varying frequency
        float twinkle_freq = 0.5 + 1.5 * fract(sin(dot(cell, vec2(34.56,78.90))) * 12345.6789);
        float twinkle = 0.5 + 0.5 * sin(time/500.0 * twinkle_freq + dot(cell, vec2(12.34,56.78)) * 10.0);
        
        // Fade stars during day
        float starVisibility = (1.0 - day_factor);
        
        // Random color logic for 5% of stars
        float colorChance = fract(sin(dot(cell, vec2(23.456, 45.678))) * 56789.1234);
        vec3 starBaseColor = vec3(1.0); // Default white
        if (colorChance < 0.05) { // 5% of stars
            float colorSelect = fract(sin(dot(cell, vec2(67.89, 12.34))) * 34567.8901) * 6.0;
            if (colorSelect < 1.0) starBaseColor = vec3(1.0, 0.41, 0.71);      // Pink
            else if (colorSelect < 2.0) starBaseColor = vec3(0.58, 0.0, 0.83); // Purple
            else if (colorSelect < 3.0) starBaseColor = vec3(1.0, 0.65, 0.0);  // Orange
            else if (colorSelect < 4.0) starBaseColor = vec3(1.0, 0.0, 0.0);   // Red
            else if (colorSelect < 5.0) starBaseColor = vec3(0.0, 0.0, 1.0);   // Blue
            else starBaseColor = vec3(0.0, 1.0, 0.0);                          // Green
        }
        
        vec3 starColor = starBaseColor * star_brightness * starIntensity * twinkle * starVisibility;
        
        color += starColor;
        // ----------------------

        color = clamp(color, 0.0, 1.0);
        fragColor = vec4(color, 1.0);
    }
    '''
)

# Sky setup
sky = Entity(
    model='sphere',
    scale=1000,
    double_sided=True,
    shader=sky_shader
)
sky.set_shader_input('resolution', Vec2(window.fullscreen_size[0], window.fullscreen_size[1]))
sky.set_shader_input('sun_size', sun_scale * 0.1)

# Sun and lighting
sun = DirectionalLight(shadows=True)
sun.shadow_map_resolution = Vec2(2048, 2048)
sun.shadow_distance = 1000

sun_model = Entity(
    model='sphere',
    scale=0.2,
    color=color.yellow,
    unlit=True
)

ambient_light = AmbientLight(color=color.rgb(50, 50, 50))

# Player setup
player = FirstPersonController()
player.cursor.model = None
player.model = Entity(
    model=Cone(),
    scale_y=2,
    shader=lit_with_shadows_shader,
)
player.collider = 'box'

# Ground and test cube
ground = Entity(
    model='plane',
    scale=(WORLD_SIZE * 2, 1, WORLD_SIZE * 2),
    collider='box',
    texture='grass',
    texture_scale=(10, 10),
    shader=lit_with_shadows_shader,
)

test_cube = Entity(
    model='cube',
    position=(0, 1, 0),
    scale=1,
    color=color.white,
    shader=lit_with_shadows_shader,
)

# Input handling
def input(key):
    global paused, game_start_time
    if key == 'escape':
        application.quit()
    if key == 'p':
        paused = not paused
    if key == 'n':
        game_start_time = 86400 * 0.25
    if key == 'm':
        game_start_time = 86400 * 0.75

# Update function
def update():
    global game_start_time, sun, sun_model, sky
    if not paused:
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
    sky.set_shader_input('sun_size', sun_scale * 0.1)

app.run()