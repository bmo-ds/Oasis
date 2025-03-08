import math
import uuid
import random
from ursina import *

class LivingThing(Entity):
    entity_grid = {}  # Shared across all living things
    time_scale = 1.0  # Class-level timescale

    def __init__(self, position, lifespan, water, nutrition, **kwargs):
        super().__init__(position=position, **kwargs)
        self.collider = 'box'
        self.cast_shadows = True  # Add this!
        self.lifespan = lifespan
        self.water = water
        self.nutrition = nutrition
        self.age = 0
        self.destroyed = False
        self.unique_id = str(uuid.uuid4())
        self.grid_key = (round(position.x), round(position.z))
        self.update_grid()

    def update_grid(self):
        self.entity_grid[self.grid_key] = [self.grid_key, self.unique_id, self.enabled]

    def update(self):
        if not self.enabled or self.destroyed:
            return
        dt = time.dt * self.time_scale
        self.lifespan -= dt
        self.age += dt
        if self.lifespan <= 0:
            self.destroy()
        else:
            self.step(dt)

    def step(self, dt):
        self.grow()

    def grow(self):
        pass

    def destroy(self):
        self.destroyed = True
        self.enabled = False
        destroy(self)
        if self.grid_key in self.entity_grid:
            del self.entity_grid[self.grid_key]

class Tree(LivingThing):
    def __init__(self, position, **kwargs):
        super().__init__(
            position=position,
            lifespan=random.randint(50, 1000),
            water=100,
            nutrition=100,
            **kwargs
        )
        self.trunk = Entity(
            parent=self,
            model='cube',
            color=color.brown,
            scale=Vec3(0.1, 0.5, 0.1),
            position=Vec3(0, 0.25, 0),
            cast_shadows=True,
            receive_shadows=True
        )
        self.foliage = Entity(
            parent=self,
            model='cube',
            color=color.green,
            scale=Vec3(0.5, 0.25, 0.5),
            position=Vec3(0, 1, 0),
            cast_shadows=True,
            receive_shadows=True
        )

    def grow(self):
        max_size_foliage = Vec3(2, 5, 2)
        max_size_trunk = Vec3(0.5, 4, 0.5)
        self.foliage.scale = lerp(self.foliage.scale, max_size_foliage, time.dt * self.time_scale * 0.01)
        self.trunk.scale = lerp(self.trunk.scale, max_size_trunk, time.dt * self.time_scale * 0.01)
        self.foliage.position = Vec3(0, self.trunk.scale.y, 0)

class Animal(LivingThing):
    MAX_ALLOWED_DT = 0.1
    POSITION_LIMIT = 1000
    SAFE_ZONE = (-50, 50)

    def __init__(self, position, animal_type='prey', **kwargs):
        scale = Vec3(0.3, 0.3, 0.3) if animal_type == 'prey' else Vec3(1.7, 1.7, 1.7)
        color_val = color.red if animal_type == 'prey' else color.blue
        lifespan = random.randint(30, 90) if animal_type == 'prey' else random.randint(60, 120)

        safe_position = self.validate_position(position)
        super().__init__(
            position=safe_position,
            lifespan=lifespan,
            water=100,
            nutrition=100,
            model='cube',
            color=color_val,
            scale=scale,
            collider="box",
            cast_shadows=True,
            receive_shadows=True,
            **kwargs
        )
        self.speed_range = (2, 8)
        self.rotation_speed_range = (45, 180)
        self.target = safe_position
        self.moving = False
        self.sleeping = False
        self.sleep_time_left = 0
        self.awake_time_left = 10
        self.target_rotation_y = self.rotation_y % 360
        self.max_eye_angle = 45
        self.look_target = None
        self.update_attributes()

        # Eye initialization
        eye_scale = 0.3
        eye_y_offset = 0.6
        eye_x_offset = 0.15
        for side, x_offset in [(-1, -eye_x_offset), (1, eye_x_offset)]:
            eye_pos = self.validate_position(Vec3(x_offset, eye_y_offset, 0.5))
            eye = Entity(parent=self, model='sphere', color=color.white,
                         scale=eye_scale, position=eye_pos)
            Entity(parent=eye, model='sphere', color=color.black,
                   scale=0.5, position=Vec3(0, 0, 0.35))

    def validate_position(self, pos):
        if any(math.isnan(v) or abs(v) > self.POSITION_LIMIT for v in pos):
            new_x = random.uniform(*self.SAFE_ZONE)
            new_z = random.uniform(*self.SAFE_ZONE)
            return Vec3(new_x, 0, new_z)
        return pos

    def update_attributes(self):
        water_factor = clamp(self.water / 100, 0, 1)
        nutrition_factor = clamp(self.nutrition / 100, 0, 1)
        lifespan_factor = clamp(self.age / self.lifespan, 0, 1) if self.lifespan > 0 else 1

        self.speed = lerp(self.speed_range[0], self.speed_range[1],
                          (water_factor + nutrition_factor) / 2)
        self.rotation_speed = lerp(self.rotation_speed_range[0],
                                   self.rotation_speed_range[1], lifespan_factor)

    def step(self, dt):
        dt = min(dt, self.MAX_ALLOWED_DT)
        self.update_attributes()
        self.grow()

        if self.sleeping:
            self.sleep_time_left -= dt
            if self.sleep_time_left <= 0:
                self.sleeping = False
                self.awake_time_left = 10
        else:
            self.update_movement(dt)
            self.update_eyes(dt)
            self.awake_time_left -= dt
            if self.awake_time_left <= 0:
                self.sleeping = True
                self.sleep_time_left = 5

    def update_movement(self, dt):
        if not self.target:
            self.target = self.generate_safe_target()
            return

        direction_vector = self.target - self.position
        if direction_vector.length() < 0.001:
            self.target = self.generate_safe_target()
            return

        target_direction = direction_vector.normalized()
        target_angle = math.atan2(target_direction.x, target_direction.z) * 180 / math.pi

        if math.isnan(target_angle):
            target_angle = self.rotation_y

        angle_diff = (target_angle - self.rotation_y + 180) % 360 - 180
        max_rotation = self.rotation_speed * dt

        if abs(angle_diff) > 5:
            self.rotation_y += clamp(angle_diff, -max_rotation, max_rotation)
            self.rotation_y %= 360
            self.moving = False
        else:
            self.moving = True
            new_position = self.position + self.forward * self.speed * dt
            new_position = self.validate_position(new_position)

            new_key = (round(new_position.x), round(new_position.z))
            if new_key in self.entity_grid and self.entity_grid[new_key][1] != self.unique_id:
                self.target = self.position - self.forward * 5
            else:
                if self.grid_key in self.entity_grid:
                    del self.entity_grid[self.grid_key]
                self.position = new_position
                self.grid_key = new_key
                self.entity_grid[self.grid_key] = [self.grid_key, self.unique_id, self.enabled]

    def generate_safe_target(self):
        return Vec3(
            random.uniform(*self.SAFE_ZONE),
            0,
            random.uniform(*self.SAFE_ZONE)
        )

    def update_eyes(self, dt):
        if not self.look_target or random.random() < 0.02:
            self.look_target = self.generate_safe_target() + Vec3(0, 1, 0)

        eye_direction = self.look_target - self.position
        if eye_direction.length() < 0.001:
            self.look_target += Vec3(0.1, 0.1, 0.1)
            eye_direction = self.look_target - self.position

        local_direction = Vec3(
            eye_direction.dot(self.right),
            eye_direction.dot(self.up),
            eye_direction.dot(self.forward)
        ).normalized()

        yaw = math.degrees(math.atan2(local_direction.x, local_direction.z))
        clamped_y = clamp(local_direction.y, -1.0, 1.0)
        pitch = math.degrees(math.asin(clamped_y))

        yaw = clamp(yaw, -self.max_eye_angle, self.max_eye_angle)
        pitch = clamp(pitch, -self.max_eye_angle, self.max_eye_angle)

        for eye in self.children:
            if 'eye' in eye.name:
                eye.rotation_y = lerp(eye.rotation_y, yaw, dt * 5)
                eye.rotation_x = lerp(eye.rotation_x, -pitch, dt * 5)

    def grow(self):
        max_size = Vec3(1, 1, 1)
        growth_factor = clamp(time.dt * self.time_scale * 0.02, 0, 0.1)
        self.scale = lerp(self.scale, max_size, growth_factor)
        self.scale = self.validate_position(self.scale)