from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

# Initialize Ursina app
app = Ursina()

# Create terrain and player
terrain = Entity(
    model='plane',
    scale=100,
    texture='white_cube',
    collider='box',
    texture_scale=(100, 100)
)
player = FirstPersonController(position=Vec3(0, 25, 0))

# Define the custom shader that only outputs 3D cubes.
shader2 = Shader(
    language=Shader.GLSL,
    vertex='''#version 330 core
uniform mat4 p3d_ModelViewProjectionMatrix;
in vec4 p3d_Vertex;
out vec4 obj_position;
void main() {
    obj_position = p3d_Vertex;
}''',
    geometry='''#version 330 core
layout (triangles) in;
layout (triangle_strip, max_vertices = 256) out;

uniform vec3 offsets_3d[100];
uniform int instance_count;
uniform mat4 p3d_ModelViewProjectionMatrix;
in vec4 obj_position[];

void main() {
    // Render only the 3D cubes using the 3D positions (offsets_3d)
    for (int i = 0; i < instance_count; i++) {
        // Front face (normal winding order)
        for (int j = 0; j < 3; j++) {
            vec4 translated_pos = obj_position[j] + vec4(offsets_3d[i], 0.0);
            gl_Position = p3d_ModelViewProjectionMatrix * translated_pos;
            EmitVertex();
        }
        EndPrimitive();

        // Back face (reversed winding order for proper visibility)
        for (int j = 2; j >= 0; j--) {
            vec4 translated_pos = obj_position[j] + vec4(offsets_3d[i], 0.0);
            gl_Position = p3d_ModelViewProjectionMatrix * translated_pos;
            EmitVertex();
        }
        EndPrimitive();
    }
}''',
    fragment='''#version 330 core
out vec4 fragColor;
void main() {
    fragColor = vec4(0.2, 0.6, 0.9, 0.6);  // Light blue color
}'''
)

# Create a cube entity using the custom shader.
entity = Entity(model='cube', shader=shader2, double_sided=True)

# Define initial positions for the cubes in 3D space.
num_cubes = 10
positions_3d = [Vec3(x * 3, 5, 0) for x in range(num_cubes)]

# Pass the 3D positions and instance count to the shader.
entity.set_shader_input('offsets_3d', positions_3d)
entity.set_shader_input('instance_count', num_cubes)

# Run the application
app.run()
