
import math
import pickle
import pygame

import settings as sett
	
	
def bounce_back(entity, obstacle):
	if entity.stopped:
		return

	#Push out so no phasing
	dx = entity.x - obstacle.x
	dy = entity.y - obstacle.y
	dist = math.hypot(dx, dy)
	if dist == 0:
		return
	nx, ny = dx / dist, dy / dist
	overlap = (obstacle.size + entity.size) - dist

	#Flip and stop
	entity.orientation = (entity.orientation + 180) % 360
	
	
def display_info(screen, boat):
	font = pygame.font.Font(None, 40)
	info_text = [
		f"Position: ({int(math.ceil(boat.x / 1000))}, {int(math.ceil(boat.y / 1000))})",
		" ",
		f"Direction: {int(boat.orientation)}°",
		" ",
		f"Speed: {round(boat.speed * 3, 1)}",
		" ",
		f"Sail: {int(boat.sail)}°",
		" ",
		f"Rudder: {int(boat.rudder)}°",
		" ",
		f"Reef: {round(boat.reef, 2)}"
	]
	for i, text in enumerate(info_text):
		rendered_text = font.render(text, True, sett.colors["WHITE"])
		screen.blit(rendered_text, (10, 10 + i * 20))
			
			
def draw_touch_controls(screen):
	font = pygame.font.Font(None, 24)
	screen.blit(font.render("Sail Angle", True, sett.colors["WHITE"]), (0.05 * sett.WIDTH, sett.HEIGHT - 0.15 * sett.HEIGHT - 20))
	screen.blit(font.render("Rudder", True, sett.colors["WHITE"]), (0.35 * sett.WIDTH, sett.HEIGHT - 0.15 * sett.HEIGHT - 20))
	screen.blit(font.render("Reef", True, sett.colors["WHITE"]), (0.65 * sett.WIDTH, sett.HEIGHT - 0.15 * sett.HEIGHT - 20))
	
	
def draw_wind_rose(surface, center, size, direction_angle, speed, font_small, font_large):
	directions = ["N", "E", "S", "W"]
	angle_offset = math.pi / 2

	#Draw cardinal lines and labels
	for i, direction in enumerate(directions):
		angle = i * (math.pi / 2) - math.pi / 2  #N = 0°
		dx = int(math.cos(angle) * size)
		dy = int(math.sin(angle) * size)
		end_pos = (center[0] + dx, center[1] + dy)
		pygame.draw.line(surface, sett.colors["WHITE"], center, end_pos, 2)

		label = font_small.render(direction, True, sett.colors["WHITE"])
		label_rect = label.get_rect(center=(center[0] + dx * 1.2, center[1] + dy * 1.2))
		surface.blit(label, label_rect)

	#Draw speed beside rose
	speed_text = font_large.render(str(round(speed * 1.5)), True, sett.colors["WHITE"])
	speed_rect = speed_text.get_rect(center=(center[0] + size * 3, center[1]))
	surface.blit(speed_text, speed_rect)

	#Center marker
	pygame.draw.circle(surface, sett.colors["RED"], center, 5)

	#Draw wind arrow
	angle_radians = math.radians(direction_angle) - math.pi / 2
	arrow_length = size * 1.5
	arrow_dx = int(math.cos(angle_radians) * arrow_length)
	arrow_dy = int(math.sin(angle_radians) * arrow_length)
	arrow_tip = (center[0] + arrow_dx, center[1] + arrow_dy)

	pygame.draw.line(surface, sett.colors["RED"], center, arrow_tip, 3)

	#Arrowhead
	head_size = 10
	for offset in (math.pi / 6, -math.pi / 6):
		hx = int(math.cos(angle_radians + offset) * head_size)
		hy = int(math.sin(angle_radians + offset) * head_size)
		pygame.draw.line(surface, sett.colors["RED"], arrow_tip, (arrow_tip[0] - hx, arrow_tip[1] - hy), 3)
	
	
def get_stop_btns():
	buttons = [
	Button("Set Sail", (sett.WIDTH // 2 - 100, sett.HEIGHT // 2 + (sett.HEIGHT // 5)), sett.WIDTH // 5, sett.HEIGHT // 35, sett.HEIGHT, color = sett.colors["RED"]),
	Button("Save", (sett.WIDTH // 1.5, sett.HEIGHT // 2 + (sett.HEIGHT // 5)), sett.WIDTH // 5, sett.HEIGHT // 35, sett.HEIGHT, color = sett.colors["RED"]),
	Button("Exit", (sett.WIDTH // 1.5, sett.HEIGHT // 2 + (sett.HEIGHT // 4)), sett.WIDTH // 5, sett.HEIGHT // 35, sett.HEIGHT, color = sett.colors["RED"]),
	]
	return buttons
	
	
def load_game():
	with open("save_main.pkl", "rb") as f:
		state = pickle.load(f)
		return state
	
	
def render_multiline(screen, text, font, color):
	width = screen.get_width()
	lines = text.splitlines()
	for i, line in enumerate(lines):
		text_surface = font.render(line, True, color)
		offset_x = int(width // 2) - (text_surface.get_width() // 2)
		offset_y = int((sett.HEIGHT // 4) + (i * font.get_height()))
		screen.blit(text_surface, (offset_x, offset_y))
		
		
def save_game(file = "save_main.pkl", **kwargs):
	for obj in kwargs.values():
		if hasattr(obj, "surface"):
			obj.surface = None
		if hasattr(obj, "wakes"):
			obj.wakes = []
	with open(file, "wb") as f:
		pickle.dump(kwargs, f)
		
		
def wind_drift(entity, wind):
	angle_diff = (wind.current_direction - entity.orientation + 360) % 360
	if angle_diff > 180:
		angle_diff -= 360
	base_turn_rate = 0.0001
	wind_factor = 1 / (((entity.speed + 1) * 100000) / 5)
	angle_factor = abs(angle_diff) / 180
	turn_rate = base_turn_rate + (wind.current_speed * wind_factor * (angle_factor * 2))
	entity.orientation = (entity.orientation - angle_diff * turn_rate) % 360
		
		
class Button:
	def __init__(self, text, pos, width, height, screen_height, color = None):
		self.color = color or sett.colors["BLUE"]
		self.font = pygame.font.Font(None, int(screen_height * 0.02))
		self.rect = pygame.Rect(pos[0], pos[1], width, height)
		self.text = text
		# Pre-render text once
		self.text_surface = self.font.render(self.text, True, sett.colors["WHITE"])
		self.text_rect = self.text_surface.get_rect(center = self.rect.center)

	def is_clicked(self, pos):
		return self.rect.collidepoint(pos)
		
	def draw(self, screen):
		pygame.draw.rect(screen, self.color, self.rect)
		screen.blit(self.text_surface, self.text_rect)
