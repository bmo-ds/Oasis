import json
import numpy as np
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.shaders import lit_with_shadows_shader
from Shaders.shaders import sky_shader, water_shader, underwater_shader, hologram  # Assuming this is defined elsewhere
from sim_init import *

class Oasis:
    def __init__(self, terrain_subdivisions=10, world_size=2000, height_scale=80, game_start_time=42000):

        # Load species data
        with open("species_config.json", "r") as f:
            config = json.load(f)

        config = generate_species_grid(config)  # Auto-generate species if missing

        # Predefine variables
        self.terrain_subdivisions = terrain_subdivisions
        self.world_size = world_size
        self.height_scale = height_scale
        self.terrain_heights = np.zeros((world_size, world_size))  # Placeholder for actual heightmap data
        self.game_start_time = game_start_time

        self.HOLOGRAM_RADIUS = 100
        max_entities = 10000  # or whatever maximum you expect

        self.entity_positions = np.zeros((max_entities, 3), dtype=np.float32)
        self.entity_model_types = np.zeros((max_entities,), dtype=np.int32)
        self.entity_colors = np.zeros((max_entities, 3), dtype=np.float32)

        self.species_array, self.categorical_mappings, self.model_data = convert_species_config_with_categorical(config)
        # Initialize EcoSim with the real terrain height function
        self.eco_sim = EcoSim(self.get_terrain_height, self.species_array)

        self.time_scale = 1
        self.temp_val = 0
        self.normal_speed = 5
        self.sprint_speed = 20

        # Create player
        self.player = FirstPersonController(model=Cone(), collider='capsule')
        self.player.cursor.model = None
        self.player.shader = lit_with_shadows_shader
        self.player.position = Vec3(400, 30, 0)
        self.player.speed = self.normal_speed

        # Precompute terrain heights
        self.terrain_heights = self.precompute_terrain_heights()

        # Create terrain
        self.ground = Entity(
            model=self.generate_terrain(),
            collider='mesh',
            texture='grass',
            double_sided=True,
            texture_scale=(10, 10),
            shadows=True,
            shader=lit_with_shadows_shader
        )

        # Create hologram quad for entity visualization
        self.hologram_shader = Entity(
            model='quad',
            position=(0, 0, 1),
            scale=(2, 2),  # Fullscreen overlay
            parent=camera.ui,
            shader=hologram,  # The new shader to visualize entities
            enabled=True
        )

        # Determine dynamic water level
        min_height = np.min(self.terrain_heights)
        self.water_level = min_height + (self.height_scale * 3 / 4)  # Adjust as needed
        # Create terrain
        self.water = Entity(
            model='plane',
            color=color.blue,
            double_sided=True,
            position=Vec3(0, self.water_level, 0),
            scale=self.world_size,
            shader=water_shader
        )

        self.water_weight = 0.012
        self.water.set_shader_input('time', 0)
        self.water.set_shader_input('colorR', 0.1)
        self.water.set_shader_input('colorG', 0.51)
        self.water.set_shader_input('colorB', 0.95)
        self.water.set_shader_input('alpha', 0.7)
        self.water.set_shader_input('weight', self.water_weight)

        self.underwater_overlay = Entity(
            model='quad',
            position=(0, 0, 1),
            scale=(2, 2),  # Cover the screen
            parent=camera.ui,
            shader=underwater_shader,
            enabled=False
        )
        self.underwater_filter = [0.3, 0.7, 6.0]  # wave intensity, speed, frequency, in that order
        self.underwater_overlay.set_shader_input('colorR', 0.0)
        self.underwater_overlay.set_shader_input('colorG', 0.2)
        self.underwater_overlay.set_shader_input('colorB', 0.8)
        self.underwater_overlay.set_shader_input('waveIntensity', self.underwater_filter[0])
        self.underwater_overlay.set_shader_input('speed', self.underwater_filter[1])
        self.underwater_overlay.set_shader_input('frequency', self.underwater_filter[2])
        self.underwater_overlay.set_shader_input('alpha', 0.5)  # Semi-transparent
        self.underwater_overlay.set_shader_input('depth', self.player.y)

        # Create sun
        self.sun = DirectionalLight(
            shadows=True,
            shadow_map_resolution=(2048, 2048),
            shadow_area=self.world_size
        )

        # Create sky
        self.sky = Sky(shader=sky_shader)
        self.sky.set_shader_input('resolution', Vec2(window.fullscreen_size[0], window.fullscreen_size[1]))
        self.sky.set_shader_input('sun_size', 0.1 * 0.1)

        # UI elements
        self.time_scale_text = Text(
            text=f'Time Scale: {self.time_scale:.1f}',
            position=(0.45, -0.45),
            origin=(0.5, -0.5),
            scale=1
        )
        self.game_time_text = Text(
            text='Game Time: d:00:00:00',
            position=(-0.45, -0.45),
            origin=(-0.5, -0.5),
            scale=1
        )

        # # Additional entities
        # self.test_cube = Entity(
        #     model='cube',
        #     scale=2,
        #     shadows=True,
        #     color=color.orange,
        #     shader=lit_with_shadows_shader
        # )

    def precompute_terrain_heights(self):
        x = np.arange(-self.world_size // 2, self.world_size // 2)
        X, Z = np.meshgrid(x, x)
        height1 = np.sin(X * 0.01) * np.cos(Z * 0.01) * self.height_scale
        height2 = np.sin(X * 0.03 + 1.0) * np.cos(Z * 0.03 + 2.0) * self.height_scale * 0.3
        return height1 + height2

    def generate_terrain(self):
        size = self.world_size
        subdivisions = 20
        height_scale = self.height_scale

        # Create grid coordinates
        x = np.linspace(-size / 2, size / 2, self.terrain_subdivisions + 1)
        z = np.linspace(-size / 2, size / 2, self.terrain_subdivisions + 1)
        X, Z = np.meshgrid(x, z)

        # Calculate heights
        height1 = np.sin(X * 0.01) * np.cos(Z * 0.01) * height_scale
        height2 = np.sin(X * 0.03 + 1.0) * np.cos(Z * 0.03 + 2.0) * height_scale * 0.3
        Y = height1 + height2

        # Create vertices array
        vertices = np.column_stack((X.ravel(), Y.ravel(), Z.ravel()))

        # Generate UV coordinates
        uvs = np.column_stack((
            np.linspace(0, 1, self.terrain_subdivisions + 1).repeat(self.terrain_subdivisions + 1),
            np.tile(np.linspace(0, 1, self.terrain_subdivisions + 1), self.terrain_subdivisions + 1)
        ))

        # Vectorized triangle indices generation
        idx = np.arange((self.terrain_subdivisions + 1) * (self.terrain_subdivisions + 1)).reshape(self.terrain_subdivisions + 1, self.terrain_subdivisions + 1)
        triangles = np.vstack((
            np.column_stack([idx[:-1, :-1].ravel(), idx[1:, :-1].ravel(), idx[:-1, 1:].ravel()]),
            np.column_stack([idx[1:, :-1].ravel(), idx[1:, 1:].ravel(), idx[:-1, 1:].ravel()])
        ))

        # Calculate normals
        v1 = vertices[triangles[:, 1]] - vertices[triangles[:, 0]]
        v2 = vertices[triangles[:, 2]] - vertices[triangles[:, 0]]
        face_normals = np.cross(v1, v2)
        face_normals /= np.linalg.norm(face_normals, axis=1)[:, np.newaxis] + 1e-10

        normals = np.zeros_like(vertices)
        np.add.at(normals, triangles[:, 0], face_normals)
        np.add.at(normals, triangles[:, 1], face_normals)
        np.add.at(normals, triangles[:, 2], face_normals)
        normals /= np.linalg.norm(normals, axis=1)[:, np.newaxis] + 1e-10

        # Return the terrain mesh
        return Mesh(
            vertices=vertices.tolist(),
            triangles=triangles.tolist(),
            uvs=uvs.tolist(),
            normals=normals.tolist(),
            mode='triangle'
        )

    def get_terrain_height(self, x, z):
        idx = (x + self.world_size // 2).astype(int)
        idz = (z + self.world_size // 2).astype(int)

        if np.all((0 <= idx) & (idx < self.world_size) & (0 <= idz) & (idz < self.world_size)):
            return self.terrain_heights[idx, idz]

        height1 = np.sin(x * 0.01) * np.cos(z * 0.01) * self.height_scale
        height2 = np.sin(x * 0.03 + 1.0) * np.cos(z * 0.03 + 2.0) * self.height_scale * 0.3
        return height1 + height2

    def smooth_slope_climbing(self):
        # Raycast down from the player's position to find the terrain's surface
        raycast_distance = 3  # Adjust this value as needed
        ray = raycast(self.player.world_position + Vec3(0, 1, 0), Vec3(0, -1, 0), distance=raycast_distance, ignore=[self.player, ])  # Added ignore=[self.player] to prevent self-collision
        if ray.hit:
            # If the ray hits the terrain, adjust the player's y position
            self.player.y = ray.world_point.y

    def calculate_underwater_color(self):
        """Scales RGB values based on depth to simulate underwater light absorption."""
        # Relative depth between the player and the water line
        rel_depth = abs(round(self.water_level - self.player.y))

        # Define the depths at which colors are absorbed (in meters)
        red_absorption = 5
        green_absorption = 20
        blue_absorption = 200
        max_depth = blue_absorption  # Depth where light is nearly gone

        # Calculate the intensity drop-off using an exponential decay
        r_depth = max(0, 1 - (rel_depth / red_absorption))  # Red fades fast
        g_depth = max(0, 1 - (rel_depth / green_absorption))  # Green fades slower
        b_depth = max(0.1, 1 - (rel_depth / blue_absorption))  # Blue persists the longest

        # Alpha fades from 1.0 (surface) to 0.0 (deepest point)
        depth_alpha = min(1.0, max(0.0, rel_depth / max_depth))  # Since max_depth = 200
        return depth_alpha, r_depth, g_depth, b_depth

    def input(self, key):
        if key == 'p':
            self.time_scale = 0
        elif key == 'up arrow':
            self.time_scale = min(self.time_scale + 1, 100)
        elif key == 'down arrow':
            self.time_scale = max(self.time_scale - 1, 0)
        elif key == 'right arrow':
            self.time_scale = min(self.time_scale + 0.1, 100.0)
        elif key == 'left arrow':
            self.time_scale = max(self.time_scale - 0.1, 0.0)
        elif key == '0':
            self.time_scale = 1
        elif key in '123456789':
            increment = int(key) * 100
            self.time_scale = min(self.time_scale + increment, 100000)
        elif key == '+':
            self.water.y += 1
        elif key == '-':
            self.water.y -= 1
        elif key == 'escape':
            application.quit()
        if held_keys['shift']:
            self.player.speed = self.sprint_speed
        else:
            self.player.speed = self.normal_speed

    def update(self):
        global entity_positions

        self.time_scale_text.text = f'Time Scale: {self.time_scale:.1f}'
        self.game_start_time += time.dt * self.time_scale
        normalized_time = (self.game_start_time % 86400) / 86400.0
        angle_degrees = normalized_time * 360 - 90
        angle_radians = math.radians(angle_degrees)
        cos_a, sin_a = math.cos(angle_radians), math.sin(angle_radians)

        day_progress = self.game_start_time / 86400.0
        radius = 100
        sun_z = math.sin(day_progress * 2 * math.pi / 365) * 30
        self.sun.position = Vec3(radius * cos_a, radius * sin_a, sun_z)
        self.sun.look_at(Vec3(0, 0, 0))

        self.sun.enabled = self.sun.y > -10
        self.sun.shadows = self.sun.y > 0

        current_angle = math.atan2(self.sun.position.y, self.sun.position.x)
        if current_angle < 0:
            current_angle += 2 * math.pi

        time_in_hours = (current_angle / (2 * math.pi)) * 24
        time_in_hours = (time_in_hours + 6) % 24
        hours = int(time_in_hours)
        minutes = int((time_in_hours - hours) * 60)
        seconds = int((((time_in_hours - hours) * 60) - minutes) * 60)
        days = int(self.game_start_time // 86400)
        self.game_time_text.text = f'Game Time: {days:02d}d:{hours:02d}:{minutes:02d}:{seconds:02d}'

        self.sky.set_shader_input('sun_size', 0.1 * 0.1)
        self.sky.set_shader_input('sun_position', self.sun.position)
        self.sky.set_shader_input('time', self.game_start_time % 86400)

        self.smooth_slope_climbing()
        if self.player.y < self.terrain_heights.min():
            self.player.y = 100

        # set water shader
        self.temp_val += 0.005
        if self.temp_val > 100:
            self.temp_val = 0

        self.water.set_shader_input('time', self.temp_val/2)
        self.water.set_shader_input('weight', self.water_weight)

        if camera.world_position.y < self.water_level:  # Camera is underwater
            self.underwater_overlay.enabled = True
            self.underwater_overlay.set_shader_input('time', self.temp_val/2)
            depth_alpha, r_depth, g_depth, b_depth = self.calculate_underwater_color()
            self.underwater_overlay.set_shader_input('alpha', depth_alpha)
            self.underwater_overlay.set_shader_input('colorR', r_depth)
            self.underwater_overlay.set_shader_input('colorG', g_depth)
            self.underwater_overlay.set_shader_input('colorB', b_depth)
            self.underwater_overlay.set_shader_input('waveIntensity', self.underwater_filter[0] * (1 - depth_alpha))
            self.underwater_overlay.set_shader_input('speed', self.underwater_filter[1] * (1 - depth_alpha))
            self.underwater_overlay.set_shader_input('frequency', self.underwater_filter[2] * (1 - depth_alpha))
        else:
            self.underwater_overlay.enabled = False

        # Gather entities' data (positions, traits, etc.)
        entities_data = []
        # for entity in self.eco_sim.entities:  # Assuming this is how you access the simulation entities
        #     # Get normalized screen position of each entity (could use camera.project)
        #     screen_pos = camera.world_to_screen(entity.position)
        #     # Append entity data (positions, traits like type, color, etc.)
        #     entities_data.append({
        #         'position': screen_pos,
        #         'type': entity.type,
        #         'size': entity.size,  # example trait
        #         'color': entity.color  # example trait
        #     })

        # Pass the entity data to the hologram shader
        # self.hologram_overlay.set_shader_input('entities', entities_data)
        oasis.eco_sim.step(self.game_start_time)  # Step the simulation

        if round(minutes) % 2:
            summarize_simulation(sim, categorical_mappings)

        # Collect positions, model types, and colors
        visible_entities = [e for e in self.eco_sim.entities if
                            distance((e['x'], e['y'], e['z']), self.player.position) < self.HOLOGRAM_RADIUS]

        positions = np.array([(e['x'], e['y'], e['z']) for e in visible_entities], dtype=np.float32)
        positions = positions.reshape(-1, 3)  # Ensures that even an empty array has shape (0,3)
        self.entity_positions[:len(visible_entities)] = positions

        model_map = {'cube': 0, 'sphere': 1, 'cone': 2, 'cylinder': 3}
        self.entity_model_types[:len(visible_entities)] = np.array(
            [model_map.get(e['geometry']['part1']['model'], 0) for e in visible_entities],
            dtype=np.int32
        )

        # For positions:
        positions = np.array([(e['x'], e['y'], e['z']) for e in visible_entities], dtype=np.float32)
        positions = positions.reshape(-1, 3)  # Ensures an empty array has shape (0,3)
        self.entity_positions[:len(visible_entities)] = positions

        # For colors:
        colors = np.array([getattr(color, e['geometry']['part1']['color'], color.white).rgb
                           for e in visible_entities], dtype=np.float32)
        colors = colors.reshape(-1, 3)  # Ensures an empty array has shape (0,3)
        self.entity_colors[:len(visible_entities)] = colors

        # Send to shader
        self.hologram_shader.set_shader_input("player_position", self.player.position)
        self.hologram_shader.set_shader_input("hologram_radius", self.HOLOGRAM_RADIUS)
        self.hologram_shader.set_shader_input("time", time.time())  # For animated effects

        self.hologram_shader.set_shader_input("instance_offset", self.entity_positions.tolist())
        self.hologram_shader.set_shader_input("instance_model_type", self.entity_model_types.tolist())
        self.hologram_shader.set_shader_input("instance_color", self.entity_colors.tolist())


# Main script
app = Ursina()
oasis = Oasis()

def input(key):
    oasis.input(key)

def update():
    oasis.update()

app.run()