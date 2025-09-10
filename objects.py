
import math
import pygame
import random

import settings as sett

from base_classes import MovingObject, StationaryObject
from syllables import Syllables


class Boat(MovingObject):
	def __init__(self, x=None, y=None):
		super().__init__(x, y)
		self.color = sett.colors["WHITE"]
		self.orientation = 90
		self.last_orientation = self.orientation
		self.size = 20
		self.stopped = False
		
		#Sailing controls
		self.reef = 0.0
		self.rudder = 0
		self.sail = 45
		
		#Physics
		self.speed = 0
		self.acceleration = 0
		self.angular_velocity = 0
		
		self.island = None
		self.wakes = []
		self.wake_timer = 0

	#Controls
	def adjust_reef(self, factor):
		self.reef = max(0.0, min(1.0, self.reef + factor * 0.1))

	def adjust_sail(self, delta):
		self.sail = max(min(self.sail + delta, 90), 0)

	def adjust_rudder(self, delta):
		self.rudder = max(-30, min(30, self.rudder + delta))

	#Physics / Wind
	def apply_wind(self, wind, dt):
		if self.stopped:
			return

		#Compute relative wind angle
		relative_wind = (wind.current_direction - self.orientation + 360) % 360

		#Ideal sail angle (0-360)
		ideal_sail_raw = relative_wind
		#Normalize to 0-90°
		ideal_sail = ideal_sail_raw % 180
		if ideal_sail > 90:
			ideal_sail = 180 - ideal_sail

		#Compute effectiveness
		effective_angle = abs(ideal_sail - self.sail)
		if effective_angle > 90:
			effective_angle = 180 - effective_angle

		if 45 < relative_wind < 135 or 225 < relative_wind < 315:
			sail_effectiveness = max(0, math.cos(math.radians(effective_angle)))
		else:
			sail_effectiveness = max(0, math.cos(math.radians(effective_angle)) * 0.2)

		#Target speed
		raw_speed = (wind.current_speed * 0.2) * sail_effectiveness * self.reef
		max_speed = 10 * self.reef + 2
		speed_multiplier = 2
		target_speed = min(raw_speed, max_speed) * speed_multiplier

		#Smoothly adjust
		accel_up = 0.5
		accel_down = 0.2

		if self.speed < target_speed:
			self.speed += accel_up * dt
			if self.speed > target_speed:
				self.speed = target_speed
		elif self.speed > target_speed:
			self.speed -= accel_down * dt
			if self.speed < target_speed:
				self.speed = target_speed

		#Drag
		self.speed *= (1 - 0.005 * dt)
		self.speed = max(0, self.speed)

		#Rudder
		turn_rate = 2 / (1 + self.speed)
		desired_angular_velocity = self.rudder * turn_rate
		self.angular_velocity += (desired_angular_velocity - self.angular_velocity) * 0.05
		self.orientation += self.angular_velocity * dt
		self.orientation %= 360

		#Wind drift
		angle_diff = (wind.current_direction - self.orientation + 360) % 360
		if angle_diff > 180:
			angle_diff -= 360
		self.orientation += (angle_diff * 0.001) * dt

		#Drawing
	def draw(self, screen, cam_x, cam_y):
		#Draw wakes first
		for wake in self.wakes:
			wake.draw(screen, cam_x, cam_y)

		#Draw the boat on top
		offset_x, offset_y = super(MovingObject, self).draw(cam_x, cam_y)
		if not self.surface:
			self.get_surface()
			self.draw_self()
		rotated_surface = pygame.transform.rotate(self.surface, -self.orientation)
		rotated_rect = rotated_surface.get_rect(center=(int(offset_x), int(offset_y)))
		screen.blit(rotated_surface, rotated_rect.topleft)

	def draw_self(self):
		self.surface = pygame.Surface((self.size*4, self.size*4), pygame.SRCALPHA)
		self.surface.fill((0,0,0,0))
		center = self.size*2  #Center of the surface
		#Define triangle relative to center
		front = (center, center - self.size)
		left = (center - self.size/2, center + self.size/2)
		right = (center + self.size/2, center + self.size/2)
		pygame.draw.polygon(self.surface, self.color, [front, left, right])

	#Movement
	def move(self, dt):
		#Update wakes
		for wake in self.wakes:
			wake.update(dt)
		if self.stopped:
			return

		#Move the boat
		rad = math.radians(self.orientation)
		speed_multiplier = 10
		self.x += math.sin(rad) * self.speed * dt * speed_multiplier #X is sin
		self.y -= math.cos(rad) * self.speed * dt * speed_multiplier #Y is -cos because Pygame Y-axis

		self.wrap()

		#Spawn wakes behind boat
		self.wake_timer += dt
		if self.speed > 0.1 and self.wake_timer > 0.1:
			spawn_distance = self.size * 0.5
			wake_x = self.x - math.sin(rad) * spawn_distance
			wake_y = self.y + math.cos(rad) * spawn_distance
			self.wakes.append(Wake(self.speed, wake_x, wake_y))
			self.wake_timer = 0

		#Remove expired wakes
		self.wakes = [w for w in self.wakes if w.lifetime > 0]
		
	def release(self):
		self.island = None
		self.stopped = False
		self.orientation += 180
		self.speed = 1
		
	def stop_at_obstacle(self, island):
		self.island = island
		self.last_orientation = self.orientation
		self.rudder = 0
		self.speed = 0
		self.stopped = True
		
		
class Cloud(MovingObject):
	def __init__(self, x=None, y=None):
		super().__init__(x, y)
		self.color = sett.colors["WHITE"]
		self.size = 50
		self.speed = 0
		self.orientation = random.randint(0, 360)
		self.x = x if x is not None else random.uniform(-sett.WORLD_WIDTH, sett.WORLD_WIDTH)
		self.y = y if y is not None else random.uniform(-sett.WORLD_HEIGHT, sett.WORLD_HEIGHT)
		
		#Pre-render cloud surface
		self.surface = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
		self._generate_circles()

	def _generate_circles(self):
		max_radius = self.size // 2
		for _ in range(25):
			radius = random.randint(max_radius // 2, max_radius)
			alpha = random.randint(200, 250)
			offset_x = random.randint(-max_radius, max_radius)
			offset_y = random.randint(-max_radius, max_radius)
			circle_color = (*self.color[:3], alpha)
			pygame.draw.circle(self.surface, circle_color, (self.size + offset_x, self.size + offset_y), radius)

	def apply_wind(self, wind):
		#Convert compass direction (0° = north/up) to Pygame radians (0 = right)
		rad = math.radians((wind.current_direction - 90) % 360)
		speed_factor = 0.05
		self.x += math.cos(rad) * wind.current_speed * speed_factor
		self.y += math.sin(rad) * wind.current_speed * speed_factor

		#Tiny random sway
		self.x += random.uniform(-0.2, 0.2)
		self.y += random.uniform(-0.2, 0.2)
		
		self.wrap()

	def draw(self, screen, cam_x, cam_y):
		offset_x = int(self.x - cam_x - self.size)
		offset_y = int(self.y - cam_y - self.size)
		screen.blit(self.surface, (offset_x, offset_y))
		
		
class Island(StationaryObject):
	def __init__(self, name=None, x=None, y=None, size=None):
		super().__init__(x, y)
		self.color = sett.colors["GREEN"]
		self.name = name or random.choice(Syllables) + random.choice(Syllables)
		self.size = size or random.randint(200, 600)
		
		self.island_name_surface = None

	def check_docking(self, boat):
		dist_sq = (boat.x - self.x) ** 2 + (boat.y - self.y) ** 2
		return dist_sq <= self.size ** 2 and boat.speed < 2 and not boat.island
		
	def draw(self, screen, cam_x, cam_y):
		offset_x = self.x - cam_x
		offset_y = self.y - cam_y
		if (offset_x + self.size < 0 or offset_x - self.size > sett.WIDTH or offset_y + self.size < 0 or offset_y - self.size > sett.HEIGHT):
			return  #Off-screen
		pygame.draw.circle(screen, self.color, (int(self.x - cam_x), int(self.y - cam_y)), self.size)
		
		
class Rock(StationaryObject):
	def __init__(self, x = None, y = None):
		super().__init__(x, y)
		self.color = sett.colors["GREY"]
		self.size = random.randint(10, 150)
		self.x, self.y = random.uniform(-sett.WORLD_WIDTH, sett.WORLD_WIDTH), random.uniform(-sett.WORLD_HEIGHT, sett.WORLD_HEIGHT)
		self.create_surface()
		
	def create_surface(self):
		self.surface = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
		pygame.draw.circle(self.surface, self.color, (self.size, self.size), self.size)
		
	def draw(self, screen, cam_x, cam_y):
		offset_x = self.x - cam_x
		offset_y = self.y - cam_y
		if (offset_x + self.size < 0 or offset_x - self.size > sett.WIDTH or offset_y + self.size < 0 or offset_y - self.size > sett.HEIGHT):
			return  #Off-screen
		pygame.draw.circle(screen, self.color, (int(self.x - cam_x), int(self.y - cam_y)), self.size)
		
		
class Seagull(MovingObject):
	def __init__(self, home_x, home_y, max_radius=500):
		self.speed = random.uniform(1.5, 3.0)
		self.flap_phase = random.uniform(0, 2 * math.pi)
		self.interval = random.randint(1500, 2500)
		self.last_change = 0
		self.n = 0
		self.orientation = random.randint(0, 360)
		self.size = 20
		self.surface = None

		# anchor point island/rock
		self.home_x, self.home_y = home_x, home_y
		self.max_radius = max_radius

		#Start near home
		self.x = home_x + random.randint(-max_radius//2, max_radius//2)
		self.y = home_y + random.randint(-max_radius//2, max_radius//2)
		
	def draw(self, screen, cam_x, cam_y):
		offset_x = self.x - cam_x
		offset_y = self.y - cam_y
		if (offset_x + self.size >= -sett.WIDTH * 2 and offset_x <= sett.WIDTH * 3) and (offset_y + self.size >= -sett.HEIGHT * 2 and offset_y <= sett.HEIGHT * 3):
			self.draw_surface()
			screen.blit(self.surface, (int(offset_x - self.size), int(offset_y - self.size)))
		
	def draw_self(self):
		flap_angle = 15 * math.sin(self.flap_phase)
		left_x = self.size - self.size * math.cos(math.radians(30 + flap_angle))
		left_y = self.size - self.size * math.sin(math.radians(30 + flap_angle))
		pygame.draw.line(self.surface, sett.colors["WHITE"], (self.size, self.size), (left_x, left_y), 2)
		right_x = self.size + self.size * math.cos(math.radians(30 + flap_angle))
		right_y = self.size - self.size * math.sin(math.radians(30 + flap_angle))
		pygame.draw.line(self.surface, sett.colors["WHITE"], (self.size, self.size), (right_x, right_y), 2)
		
	def draw_surface(self):
		if not self.surface:
			self.get_surface()
		self.surface.fill((0, 0, 0, 0))
		self.draw_self()
		
	def move(self, time):
		self.flap_phase += self.speed * 0.05
		self.flap_phase %= 2 * math.pi
		if self.n >= 1:
			self.n = 0
			super().move()

			#Check distance from home
			dx = self.x - self.home_x
			dy = self.y - self.home_y
			dist_sq = dx*dx + dy*dy

			if dist_sq > self.max_radius**2:
				#Force orientation back toward home
				self.orientation = math.degrees(math.atan2(-dy, -dx))
			elif time - self.last_change > self.interval:
				self.last_change = time
				self.orientation = random.randint(0, 360)
		else:
			self.n += 1
		
		
class Wake:
	def __init__(self, speed, x, y):
		self.x = x
		self.y = y
		self.size = 10
		self.lifetime = max(10, speed * 0.75)
		self.max_lifetime = self.lifetime
		self.color_start = (180, 220, 255)   #Bright light blue
		self.color_end = (100, 200, 255)     #Softer blue fade-out


	def update(self, dt):
		self.lifetime -= dt * 5
		if self.lifetime < 0:
			self.lifetime = 0
		self.size += 5 * dt
		

	def draw(self, screen, cam_x, cam_y):
		if self.lifetime <= 0:
			return
		offset_x = int(self.x - cam_x)
		offset_y = int(self.y - cam_y)
		t = 1 - (self.lifetime / self.max_lifetime)
		color = (int(self.color_start[0] * (1 - t) + self.color_end[0] * t), int(self.color_start[1] * (1 - t) + self.color_end[1] * t), int(self.color_start[2] * (1 - t) + self.color_end[2] * t),)
		pygame.draw.circle(screen, color, (int(offset_x), int(offset_y)), int(self.size))
		
		
class Wind:
	def __init__(self):
		self.base_direction = random.randint(0, 360)
		self.base_speed = random.randint(5, 35)
		self.current_direction = self.base_direction
		self.current_speed = self.base_speed
		self.interval = 5000  #Ms
		self.last_change = 0
		
	def update_wind(self, time):
		#Only update if enough time has passed
		if (time - self.last_change) > self.interval:
			#Direction jitter
			self.current_direction = (self.current_direction + random.uniform(-5, 5)) % 360

			#Gentle speed drift with central bias
			drift = random.uniform(-1, 1)
			bias = (20 - self.current_speed) * 0.05  #Pulls toward 20
			self.current_speed = max(0, min(self.current_speed + drift + bias, 35))

			self.last_change = time

	def get_vector(self):
		#Returns (dx, dy) unit vector * speed
		radians = math.radians(self.current_direction)
		return math.cos(radians) * self.current_speed, math.sin(radians) * self.current_speed
