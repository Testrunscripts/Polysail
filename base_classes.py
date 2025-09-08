
import math
import pygame
import random

import settings as sett


class Object:
	def __init__(self, x = None, y = None):
		self.cached_offset_x = None
		self.cached_offset_y = None
		self.color = [0, 0, 0]
		self.interval = 0
		self.last_cam_x = None
		self.last_cam_y = None
		self.last_x = 0 if x is None else x
		self.last_y = 0 if y is None else y
		self.last_change = 0
		self.size = 0
		self.surface = None
		self.x = 0 if x is None else x
		self.y = 0 if y is None else y
		
	def draw(self, cam_x, cam_y):
		if (cam_x != self.last_cam_x or cam_y != self.last_cam_y or self.x != self.last_x or self.y != self.last_y):
			self.cached_offset_x = self.x - cam_x
			self.cached_offset_y = self.y - cam_y
			self.last_cam_x, self.last_cam_y = cam_x, cam_y
			self.last_x, self.last_y = self.x, self.y
		return self.cached_offset_x, self.cached_offset_y
			
	def draw_self(self):
   	 if self.surface:
 	       pygame.draw.circle(self.surface, self.color, (self.size, self.size), self.size)
		
	def get_surface(self):
		if not self.surface or self.surface.get_size() != (self.size * 2, self.size * 2):
			self.surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)


class MovingObject(Object):
	def __init__(self, x = None, y = None):
		super().__init__(x, y)
		self.orientation = 0
		self.speed = 0
	
	def draw(self, screen, cam_x, cam_y):
		offset_x, offset_y = super().draw(cam_x, cam_y)
		if (offset_x + self.size >= -sett.WIDTH * 2 and offset_x <= sett.WIDTH * 3) and (offset_y + self.size >= -sett.HEIGHT * 2 and offset_y <= sett.HEIGHT * 3):
			self.draw_surface()
			screen.blit(self.surface, (int(offset_x - self.size), int(offset_y - self.size)))
		return offset_x, offset_y
			
	def draw_surface(self):
		if not self.surface:
			self.get_surface()
			self.draw_self()
		
	def move(self, dt = 1):
		rad_direction = math.radians(self.orientation)
		forward_vel = (self.speed * 1.5) * math.cos(rad_direction)
		lateral_vel = (self.speed * 1.5) * math.sin(rad_direction)
		self.x += forward_vel
		self.y += lateral_vel
		self.wrap()
		
	def wrap(self):
		if self.x < -sett.WORLD_WIDTH:
			self.x = sett.WORLD_WIDTH
		elif self.x > sett.WORLD_WIDTH:
			self.x = -sett.WORLD_WIDTH
		if self.y < -sett.WORLD_HEIGHT:
			self.y = sett.WORLD_HEIGHT
		elif self.y > sett.WORLD_HEIGHT:
			self.y = -sett.WORLD_HEIGHT
		
			
class StationaryObject(Object):
	def __init__(self, x = None, y = None):
		super().__init__(x, y)
		self.collision_radius_sq = (self.size * 1.01) ** 2
		
	def check_collision(self, collider):
		return math.hypot(collider.x - self.x, collider.y - self.y) <= self.size * 1.05
		
	def draw(self, screen, cam_x, cam_y, **kwargs):
		offset_x, offset_y = super().draw(cam_x, cam_y)
		if (offset_x + self.size >= -sett.WIDTH * 2 and offset_x <= sett.WIDTH * 3) and (offset_y + self.size >= -sett.HEIGHT * 2 and offset_y <= sett.HEIGHT * 3):
			if not self.surface:
				self.get_surface()
				self.draw_self()
			blit_x = int(offset_x - self.size)
			blit_y = int(offset_y - self.size)
			screen.blit(self.surface, (blit_x, blit_y))
