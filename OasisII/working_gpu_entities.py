from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

# Define the custom shader
shader2 = Shader(
    language=Shader.GLSL,
    vertex='''
    #version 330 core
    uniform mat4 p3d_ModelViewProjectionMatrix;
    in vec4 p3d_Vertex;
    out vec4 obj_position;

    void main(){
        obj_position = p3d_Vertex;
    }
    ''',
    geometry='''
    #version 330 core
    layout (triangles) in;
    layout (triangle_strip, max_vertices = 256) out;

    uniform vec3 offsets_3d[100];      // Positions for 3D cubes
    uniform vec3 offsets_proj[100];    // Positions for projected cubes
    uniform int instance_count;
    uniform mat4 p3d_ModelViewProjectionMatrix;

    in vec4 obj_position[];

    void main() {
        // Emit 3D cubes above the plane
        for (int i = 0; i < instance_count; i++) {
            for (int j = 0; j < gl_in.length(); j++) {
                vec4 translated_pos = obj_position[j] + vec4(offsets_3d[i], 0.0);
                gl_Position = p3d_ModelViewProjectionMatrix * translated_pos;
                EmitVertex();
            }
            EndPrimitive();
        }
        // Emit flattened projected cubes on the plane
        for (int i = 0; i < instance_count; i++) {
            for (int j = 0; j < gl_in.length(); j++) {
                vec4 proj_pos = obj_position[j];
                proj_pos.y = 0.0;  // Flatten to the plane (y=0)
                vec4 translated_pos = proj_pos + vec4(offsets_proj[i], 0.0);
                gl_Position = p3d_ModelViewProjectionMatrix * translated_pos;
                EmitVertex();
            }
            EndPrimitive();
        }
    }
    ''',
    fragment='''
    #version 330 core
    out vec4 fragColor;

    void main(){
        fragColor = vec4(0.2, 0.6, 0.9, 1.0);  // Light blue color
    }
    '''
)

# Initialize Ursina app
app = Ursina()

# Add an editor camera for navigation
# EditorCamera()

# Create a plane as the terrain
terrain = Entity(model='plane', scale=100, texture='white_cube', collider='box', texture_scale=(100, 100))

# Create player
player = FirstPersonController(position=Vec3(0,25,0))

# Create a single entity for the cubes, which the shader will instance
entity = Entity(model='cube', shader=shader2)  # Default scale=1

# Define positions for 3D cubes and their projections
positions_3d = [Vec3(x * 3, 5, 0) for x in range(10)]        # Cubes 5 units above the plane
positions_proj = [Vec3(x * 3 + 10, 0, 0) for x in range(10)] # Projections shifted 10 units right

# Pass positions to the shader
entity.set_shader_input('offsets_3d', positions_3d)
entity.set_shader_input('offsets_proj', positions_proj)
entity.set_shader_input('instance_count', len(positions_3d))

# Run the application
app.run()