from ursina import *

underwater_shader = Shader(
    vertex='''
    #version 430
    uniform mat4 p3d_ModelViewProjectionMatrix;
    in vec4 p3d_Vertex;
    in vec2 p3d_MultiTexCoord0; 
    out vec2 uv;

    void main() {
        gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
        uv = p3d_MultiTexCoord0; 
    }
    ''',

    fragment='''
    #version 430 core

    out vec4 FragColor;
    in vec2 uv;
    
    uniform float time;
    uniform float colorR;
    uniform float colorG;
    uniform float colorB;
    uniform float alpha;
    uniform float waveIntensity = 0.3;  // Strength of the wave effect
    uniform float speed = 0.7;          // Speed of wave movement
    uniform float frequency = 6.0;      // Number of waves

    void main() {
        // Compute a wave pattern using both UV coordinates and time
        float wave = sin(uv.x * frequency + time * speed) * cos(uv.y * frequency + time * speed) * waveIntensity;
        
        // Define the base color from uniforms
        vec3 baseColor = vec3(colorR, colorG, colorB);
        
        // Add the wave effect
        vec3 finalColor = baseColor + vec3(wave);
        
        // Output final color with depth-based transparency
        FragColor = vec4(finalColor, alpha);
    }

    '''
)


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
        float theta = atan((star_dir.z), (star_dir.x));
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

water_shader = Shader(
    vertex='''
    #version 430
    uniform mat4 p3d_ModelViewProjectionMatrix;
    in vec4 p3d_Vertex;
    in vec2 p3d_MultiTexCoord0; // Get default UV
    out vec2 uv;

    void main() {
        gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
        uv = p3d_MultiTexCoord0; // Pass UVs to fragment shader
    }
    ''',

    fragment='''
        #version 430 core

    out vec4 FragColor;
    in vec2 uv; // Receive UVs from vertex shader

    uniform float time;
    uniform float weight;
    uniform float colorR;
    uniform float colorG;
    uniform float colorB;
    uniform float alpha; // Add an alpha uniform

    #define DRAG_MULT 10.38
    #define WATER_DEPTH 1.0
    #define ITERATIONS_RAYMARCH 12
    #define ITERATIONS_NORMAL 37

    vec2 wavedx(vec2 position, vec2 direction, float frequency, float timeshift) {
        float x = dot(direction, position) * frequency + timeshift;
        float wave = exp(sin(x) - 1.0);
        float dx = wave * cos(x);
        return vec2(wave, -dx);
    }

    float getwaves(vec2 position, int iterations, float timeshift) {
        float iter = 0.0;
        float frequency = 2.0;
        float timeMultiplier = 5.0;
        float waveWeight = weight;
        float sumOfValues = 0.0;
        float sumOfWeights = 0.0;
        for(int i = 0; i < iterations; i++) {
            vec2 p = vec2(sin(iter), cos(iter));
            vec2 res = wavedx(position, p, frequency, timeshift);
            position += p * res.y * waveWeight * DRAG_MULT;
            sumOfValues += res.x * waveWeight;
            sumOfWeights += waveWeight;
            waveWeight = mix(waveWeight, 0.0, 0.2);
            frequency *= 1.5;
            timeMultiplier *= 1.2;
            iter += 1232.399963;
        }
        return sumOfValues / sumOfWeights;
    }

    void main() {
        vec2 position = uv * 50.0; // Use the passed UVs!  Adjust the scaling factor.
        float waves = getwaves(position, ITERATIONS_RAYMARCH, time * 2.0);

        // Adjust color based on uniform values and waves intensity
        vec3 color = vec3(colorR, colorG, colorB);

        // Calculate brightness based on waves intensity
        float brightness = waves * 0.5 + 0.5;
        color = mix(vec3(0.0), color, brightness);
        color = mix(vec3(0.0), color, brightness * 0.8);

        FragColor = vec4(color, alpha); // Set the alpha value
    }
    '''
)