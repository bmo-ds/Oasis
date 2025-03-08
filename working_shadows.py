from ursina import *

# Initialize the Ursina app
app = Ursina()

# Create a directional light
light = DirectionalLight()
light.look_at(Vec3(1, -1, -1))  # Adjust the light's direction

# Create a plane to receive the shadow
plane = Entity(
    model='plane',
    scale=(10, 1, 10),
    color=color.gray,
    position=(0, -0.5, 0),
    shader=None,  # Using Ursina's default lighting
)

# Create a cube that casts a shadow
cube = Entity(
    model='cube',
    scale=(1, 1, 1),
    position=(0, 0.5, 0),
    color=color.orange,
    shader=None
)


EditorCamera()  # Enable camera controls

# Run the app
app.run()
