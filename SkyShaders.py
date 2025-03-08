from ursina import *

# === SHADER SETUP ===
sky_shader = Shader(
    vertex='''
    #version 430
    uniform mat4 p3d_ModelViewProjectionMatrix;
    uniform mat4 p3d_ModelMatrix;
    in vec4 p3d_Vertex;
    out vec3 world_pos;

    void main() {
        gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
        world_pos = (p3d_ModelMatrix * p3d_Vertex).xyz;  // World position for fragment shader
    }
    ''',
    fragment='''
    #version 430
    in vec3 world_pos;
    out vec4 fragColor;

    uniform vec2 resolution;
    uniform float time;
    uniform vec3 sun_position;  // Sun's position in world space

    void main() {
        vec3 norm_world_pos = normalize(world_pos);
        vec3 norm_sun_pos = normalize(sun_position);

        // Sun calculation - reduced sun size and maintained brightness
        float sun_angle = dot(norm_world_pos, norm_sun_pos);
        float sun_size = 0.995;  // Increase threshold to shrink the sun disc
        float sun_intensity = 3.0;  // Brightness remains the same

        // Narrower core and halo for a smaller, crisper sun
        float sun_core = smoothstep(sun_size, 1.0, sun_angle);
        float sun_halo = smoothstep(sun_size - 0.005, sun_size, sun_angle) * 0.3;
        vec3 sun_color = vec3(1.0, 0.9, 0.6) * sun_intensity * (sun_core + sun_halo);

        // Sky colors with updated values for realism
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

        // Adjust transition based on sun's elevation (normalized y component)
        float sun_elevation = norm_sun_pos.y;
        // Shifted range so the sun remains visible slightly longer
        float day_factor = smoothstep(-0.1, 0.3, sun_elevation);

        // Blend sky colors for a smooth transition through night, dawn/dusk, and day
        vec3 sky_color;
        if(day_factor < 0.5){
            sky_color = mix(night_color, dawn_dusk_color, day_factor * 2.0);
        } else {
            sky_color = mix(dawn_dusk_color, day_color, (day_factor - 0.5) * 2.0);
        }

        // Combine sky and sun
        vec3 color = sky_color + sun_color;
        color = clamp(color, 0.0, 1.0);
        fragColor = vec4(color, 1.0);
    }
    '''
)
