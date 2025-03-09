from ursina import *

vertex = '''
#version 430
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelMatrix;
in vec4 p3d_Vertex;
out vec2 uv;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    vec4 worldPosition = p3d_ModelMatrix * p3d_Vertex;
    uv = worldPosition.xy;
}
'''

fragment = '''
#version 330 core

out vec4 FragColor;
in vec2 uv;

uniform float time;
uniform float weight2;

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
    float weight = weight2;
    float sumOfValues = 0.0;
    float sumOfWeights = 0.0;
    for(int i = 0; i < iterations; i++) {
        vec2 p = vec2(sin(iter), cos(iter));
        vec2 res = wavedx(position, p, frequency, timeshift);
        position += p * res.y * weight * DRAG_MULT;
        sumOfValues += res.x * weight;
        sumOfWeights += weight;
        weight = mix(weight, 0.0, 0.2);
        frequency *= 1.5;
        timeMultiplier *= 1.2;
        iter += 1232.399963;
    }
    return sumOfValues / sumOfWeights;
}

void main() {
    vec2 position = uv * 10.0;
    float waves = getwaves(position, ITERATIONS_RAYMARCH, time * 2.0);

    // Calculate rainbow-like color with shifting hues over time
    vec3 rainbowColor = vec3(
        0.5 + 0.5 * sin(time * 0.1),
        0.5 + 0.5 * sin(time * 0.2),
        0.5 + 0.5 * sin(time * 0.3)
    );

    // Adjust color based on waves intensity
    float brightness = waves * 0.5 + 0.5;
    vec3 color = mix(vec3(0.0), rainbowColor, brightness);
    color = mix(vec3(0.0), color, brightness * 0.8);

    FragColor = vec4(color, 1.0);
}

'''

bricks = '''
#version 330 core

uniform float time;
uniform vec2 resolution;
out vec4 fragColor;

void main() {
    vec3 color;
    float f = 500.0;

    for (float x = -f; x < f; x += 20.0) {
        for (float y = -f; y < f; y += 10.0) {
            float c = 200.0 + 64.0 * noise(vec2(x, y));
            color = vec3(c, c - 140.0, 0.0);
            float zOffset = sin(time / 9.0) * sin(x / 99.0 + y / 50.0 + time);

            // Convert x, y to screen coordinates
            vec2 screenCoords = vec2((x + f) / (2.0 * f), (y + f) / (2.0 * f));

            // Mapping screen coordinates to fragment coordinates
            if (gl_FragCoord.xy == resolution * screenCoords) {
                fragColor = vec4(color, 1.0);
            }
        }
    }
}

'''

# Initialize the Ursina app
app = Ursina()

# Create the shader
water_shader = Shader(
    language=Shader.GLSL,
    vertex=vertex,
    fragment=fragment,
    default_input={
        'time': 0.0,
        'weight2': 0.01
    }
)

# Create the shader
bricks_shader = Shader(
    language=Shader.GLSL,
    vertex=vertex,
    fragment=bricks,
    default_input={
        'time': 0.0,
    }
)

# Create a plane entity, apply the shader, and rotate it to face the camera
plane = Entity(model='sphere', scale=(10, 10, 10), shader=water_shader, rotation=(90, 0, 0))
plane.double_sided = True  # Corrected attribute setting
EditorCamera()

# Variable to store the weight value
weight_value = 0.001
current_shader = 0.001  # Set the initial shader


def input(key):
    global weight_value, current_shader

    if key == 'g':
        weight_value += 0.001
    elif key == 'b':
        weight_value -= 0.001
    elif key == 'x':
        exit()


def update():
    global weight_value, current_shader

    plane.set_shader_input('time', current_shader * 2.0)
    plane.set_shader_input('weight2', weight_value)

    if held_keys['f']:
        weight_value += 0.001
    if held_keys['v']:
        weight_value -= 0.001

    current_shader += 0.005


# Run the app
app.run()
