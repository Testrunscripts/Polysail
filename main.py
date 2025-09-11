
import os
import pygame
import random
import sys

import settings as sett

from objects import Boat, Cloud, Island, Rock, Seagull, Wind
from utils import Button, bounce_back, display_info, draw_wind_rose, get_stop_btns, load_game, render_multiline, save_game


pygame.init()
pygame.mixer.init()


def resource_path(relative_path):
	if hasattr(sys, '_MEIPASS'):
		return os.path.join(sys._MEIPASS, relative_path)
	return os.path.join(os.path.abspath("."), relative_path)


class DevTools:
	def __init__(self, clock):
		self.clock = clock
		
	def draw_debug(self, screen):
		font = pygame.font.Font(None, 25)
		text_surface = font.render("FPS: " + str(round(self.clock.get_fps(), 1)), True, sett.colors["WHITE"])
		screen.blit(text_surface, (sett.WIDTH // 1.2, sett.HEIGHT // 100))


class Game:
	def __init__(self):
		info = pygame.display.Info()
		sett.set_display(info)
		self.buttons = []
		self.clock = pygame.time.Clock()
		self.game_running = False
		self.load_data = False
		self.running = True
		self.screen = pygame.display.set_mode((sett.WIDTH, sett.HEIGHT))

		#Cache fonts
		self.font_small = pygame.font.Font(None, int(sett.HEIGHT * 0.02))
		self.font_large = pygame.font.Font(None, int(sett.HEIGHT * 0.1))
		self.font_debug = pygame.font.Font(None, 25)

		#State setup
		self.state_dict = {
			"CREDITS" : self.credits,
			"EXIT" : self.exit_game,
			"HOWTOPLAY" : self.how_to_play,
			"MAIN_MENU" : self.main_menu,
			"NEW_GAME" : self.new_game,
		}
		self.state = "MAIN_MENU"
		
		self.playlist = [
		"Assets/Calm Waters.mp3",
		"Assets/Waves of Freedom.mp3",
		"Assets/Drift on the Horizon.mp3",
		"Assets/Sailing the Digital Tides.mp3",
		]
		random.shuffle(self.playlist)
		self.current_track = 0
		self.MUSIC_END = pygame.USEREVENT + 1
		pygame.mixer.music.set_endevent(self.MUSIC_END)
		pygame.mixer.music.load(resource_path(self.playlist[0]))
		pygame.mixer.music.play()
		
		self.mouse_held = False
		self.mouse_pos = None

		#Control rects
		control_height = int(sett.HEIGHT * 0.15)
		self.sail_rect = pygame.Rect(0.05 * sett.WIDTH, sett.HEIGHT - control_height, 0.25 * sett.WIDTH, control_height)
		self.rudder_rect = pygame.Rect(0.35 * sett.WIDTH, sett.HEIGHT - control_height, 0.25 * sett.WIDTH, control_height)
		self.reef_rect = pygame.Rect(0.65 * sett.WIDTH, sett.HEIGHT - control_height, 0.25 * sett.WIDTH, control_height)
		
		self.boat = None
		self.wind = None
		
		self.islands = []
		self.rocks = []

	def exit_game(self):
		if self.state == "EXIT":
			self.running = False
			pygame.quit()
		elif self.state != "MAIN_MENU":
			self.game_running = False
			self.state = "MAIN_MENU"
		else:
			self.game_running = False
			self.state = "EXIT"

	def handle_button_click(self, pos):
		for button in self.buttons:
			if button.is_clicked(pos) and button.is_active(self.state):
				if button.text == "Main Menu":
					self.state = "MAIN_MENU"
				elif button.text == "New Game":
					self.state = "NEW_GAME"
					self.game_running = False
				elif button.text == "Load Game":
					self.load_data = True
					self.state = "NEW_GAME"
					self.game_running = False
				elif button.text == "How to Play":
					if self.state == "HOWTOPLAY":
						self.state = "MAIN_MENU"
					else:
						self.game_running = False
						self.state = "HOWTOPLAY"
				elif button.text == "Credits":
					if self.state == "CREDITS":
						self.state = "MAIN_MENU"
					else:
						self.game_running = False
						self.state = "CREDITS"
				elif button.text == "Exit":
					self.exit_game()

	def handle_events(self, boat=None, stop_buttons=None):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				self.exit_game()
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					self.exit_game()
			elif event.type == pygame.MOUSEBUTTONDOWN:
				self.mouse_held = True
				self.mouse_pos = event.pos

				#Handle docked buttons first
				if boat and boat.stopped and stop_buttons:
					for btn in stop_buttons:
						if btn.rect.collidepoint(event.pos):
							if btn.text == "Set Sail":
								boat.release()
							elif btn.text == "Save":
								self.boat.surface = None
								surface = self.boat.island.island_name_surface
								self.boat.island_name_surface = None
								for island in self.islands:
									island.surface = None
								for rock in self.rocks:
									rock.surface = None
								save_game(boat = boat, islands = self.islands, rocks = self.rocks, wind = self.wind)
								self.boat.island.island_name_surface = surface
							elif btn.text == "Exit":
								self.exit_game()
							return  #Stop further processing this click

				#Normal button click handling
				self.handle_button_click(event.pos)

			elif event.type == pygame.MOUSEBUTTONUP:
				self.mouse_held = False
				
			elif event.type == self.MUSIC_END:
				self.current_track = (self.current_track + 1) % len(self.playlist)
				pygame.mixer.music.load(resource_path(self.playlist[self.current_track]))
				pygame.mixer.music.play()

		#Held adjustments for normal controls
		if self.state == "NEW_GAME" and boat and getattr(self, "mouse_held", False) and not boat.stopped:
			if self.sail_rect.collidepoint(self.mouse_pos):
				boat.adjust_sail(0.5 if self.mouse_pos[0] < self.sail_rect.centerx else -0.5)
			elif self.rudder_rect.collidepoint(self.mouse_pos):
				boat.adjust_rudder(0.05 if self.mouse_pos[0] < self.rudder_rect.centerx else -0.05)
			elif self.reef_rect.collidepoint(self.mouse_pos):
				boat.adjust_reef(0.05 if self.mouse_pos[0] < self.reef_rect.centerx else -0.05)
				
		#Held adjustments for keyboard controls
		keys = pygame.key.get_pressed()
		if self.state == "NEW_GAME" and boat and not boat.stopped:
			#Sail angle (Q/E)
			if keys[pygame.K_q]:
				boat.adjust_sail(0.5)
			if keys[pygame.K_e]:
				boat.adjust_sail(-0.5)
			#Rudder (A/D)
			if keys[pygame.K_a]:
				boat.adjust_rudder(0.05)
			if keys[pygame.K_d]:
				boat.adjust_rudder(-0.05)
			#Reef (W/S)
			if keys[pygame.K_w]:
				boat.adjust_reef(0.05)
			if keys[pygame.K_s]:
				boat.adjust_reef(-0.05)

	def credits(self):
		if not self.buttons:
			scale_width = sett.WIDTH // 10
			scale_height = sett.HEIGHT // 20
			self.buttons = [Button("Main Menu", (sett.WIDTH // 2 - scale_width, int(sett.HEIGHT // 1.2)),
				scale_width * 2, scale_height // 2, sett.HEIGHT)]

		self.screen.fill(sett.colors["LIGHT BLUE"])
		render_multiline(self.screen, sett.credit_text, self.font_small, sett.colors["WHITE"])
		self.handle_events()
		for button in self.buttons:
			button.draw(self.screen)
		pygame.display.flip()
		
	def how_to_play(self):
		if not self.buttons:
			scale_width = sett.WIDTH // 10
			scale_height = sett.HEIGHT // 20
			self.buttons = [Button("Main Menu", (sett.WIDTH // 2 - scale_width, int(sett.HEIGHT // 1.2)),
				scale_width * 2, scale_height // 2, sett.HEIGHT)]

		self.screen.fill(sett.colors["LIGHT BLUE"])
		render_multiline(self.screen, sett.howtoplay_text, self.font_small, sett.colors["WHITE"])
		self.handle_events()
		for button in self.buttons:
			button.draw(self.screen)
		pygame.display.flip()

	def main_menu(self):
		sett.WORLD_WIDTH, sett.WORLD_HEIGHT = sett.WIDTH, sett.HEIGHT
		wind = Wind()
		clouds = []
		self.game_running = True
		cam_x, cam_y = 0, 0
		for _ in range(25):
			cloud = Cloud()
			cloud.x = random.uniform(cam_x - sett.WORLD_WIDTH, cam_x + sett.WORLD_WIDTH)
			cloud.y = random.uniform(cam_y - sett.WORLD_HEIGHT, cam_y + sett.WORLD_HEIGHT)
			clouds.append(cloud)
		if not self.buttons:
			scale_width = sett.WIDTH // 10
			scale_height = sett.HEIGHT // 20
			button_texts = ["New Game", "Load Game", "How to Play", "Credits", "Exit"]
			self.buttons = [Button(text, (sett.WIDTH // 2 - scale_width, sett.HEIGHT // 2 + i * scale_height),
				scale_width * 2, scale_height // 2, sett.HEIGHT) for i, text in enumerate(button_texts)]

		while self.game_running:
			current_time = pygame.time.get_ticks()
			self.screen.fill(sett.colors["LIGHT BLUE"])
			text_surface = self.font_large.render("POLYSAIL", True, sett.colors["WHITE"])
			self.screen.blit(text_surface, (sett.WIDTH // 2 - text_surface.get_width() // 2, sett.HEIGHT // 10))
			wind.update_wind(current_time)
			for cloud in clouds:
				cloud.apply_wind(wind)
				cloud.draw(self.screen, cam_x, cam_y)
			for button in self.buttons:
				button.draw(self.screen)
			self.handle_events()
			pygame.display.flip()

	def new_game(self):
		self.game_running = True
		
		clouds, seagulls, stop_buttons = self.setup()
		dev = DevTools(self.clock)
		
		while self.game_running:
			current_time = pygame.time.get_ticks()
			dt = self.clock.get_time() / 1000
			self.screen.fill(sett.colors["LIGHT BLUE"])
		
			cam_x, cam_y = self.boat.x - sett.WIDTH // 2, self.boat.y - sett.HEIGHT // 2
			for cloud in clouds:
				cloud.apply_wind(self.wind)
			for seagull in seagulls:
				offset_x = seagull.x - cam_x
				offset_y = seagull.y - cam_y
				dist_sq = offset_x**2 + offset_y**2
				if dist_sq <= 4000**2:
					seagull.move(dt)
			if not self.boat.stopped:
				for rock in self.rocks:
					offset_x = rock.x - cam_x
					offset_y = rock.y - cam_y
					if not (offset_x + rock.size < 0 or offset_x - rock.size > sett.WIDTH or offset_y + rock.size < 0 or offset_y - rock.size > sett.HEIGHT):
						if rock.check_collision(self.boat):
							bounce_back(self.boat, rock)
				self.boat.apply_wind(self.wind, dt)
				self.boat.move(dt)
				for island in self.islands:
					offset_x = island.x - cam_x
					offset_y = island.y - cam_y
					if not (offset_x + island.size < 0 or offset_x - island.size > sett.WIDTH or offset_y + island.size < 0 or offset_y - island.size > sett.HEIGHT):
						if island.check_docking(self.boat):
							self.boat.stop_at_obstacle(island)
							self.boat.island.island_name_surface = self.font_large.render(self.boat.island.name.capitalize(), True, sett.colors["WHITE"], sett.colors["BLUE"])
							stop_buttons = get_stop_btns()
						elif (self.boat.x - island.x) ** 2 + (self.boat.y - island.y) ** 2 <= island.size ** 2:
						#Inside the island, but too fast to dock
							bounce_back(self.boat, island)
			
			self.wind.update_wind(current_time)
			
			for rock in self.rocks:
				offset_x = rock.x - cam_x
				offset_y = rock.y - cam_y
				if not (offset_x + rock.size < 0 or offset_x - rock.size > sett.WIDTH or offset_y + rock.size < 0 or offset_y - rock.size > sett.HEIGHT):
					rock.draw(self.screen, cam_x, cam_y)
			for island in self.islands:
				offset_x = island.x - cam_x
				offset_y = island.y - cam_y
				if not (offset_x + island.size < 0 or offset_x - island.size > sett.WIDTH or offset_y + island.size < 0 or offset_y - island.size > sett.HEIGHT):
					island.draw(self.screen, cam_x, cam_y)
			self.boat.draw(self.screen, cam_x, cam_y)
			for seagull in seagulls:
				offset_x = seagull.x - cam_x
				offset_y = seagull.y - cam_y
				if not (offset_x + seagull.size < 0 or offset_x - seagull.size > sett.WIDTH or offset_y + seagull.size < 0 or offset_y - seagull.size > sett.HEIGHT):
					seagull.draw(self.screen, cam_x, cam_y)
			for cloud in clouds:
				offset_x = cloud.x - cam_x
				offset_y = cloud.y - cam_y
				if not (offset_x + cloud.size < 0 or offset_x - cloud.size > sett.WIDTH or offset_y + cloud.size < 0 or offset_y - cloud.size > sett.HEIGHT):
					cloud.draw(self.screen, cam_x, cam_y)
			if self.boat.stopped:
				for btn in stop_buttons:
					btn.draw(self.screen)
				if self.boat.island and hasattr(self.boat.island, "island_name_surface"):
					first_button = stop_buttons[0]
					name_x = sett.WIDTH // 2 - self.boat.island.island_name_surface.get_width() // 2
					name_y = first_button.rect.top - int(sett.HEIGHT * 0.5)
					self.screen.blit(self.boat.island.island_name_surface, (name_x, name_y))
		
			self.handle_events(self.boat, stop_buttons = stop_buttons if stop_buttons else None)
			
			#Draw the control pads
			for rect, label in [(self.sail_rect, "Sail"), (self.rudder_rect, "Rudder"), (self.reef_rect, "Reef")]:
			 #Rectangle
			 pygame.draw.rect(self.screen, sett.colors["RED"], rect)
			 #Line
			 center_x = rect.centerx
			 pygame.draw.line(self.screen, sett.colors["WHITE"], (center_x, rect.top), (center_x, rect.bottom), 2)
			 #Label
			 label_surface = self.font_small.render(label, True, sett.colors["WHITE"])
			 label_x = rect.centerx - label_surface.get_width() // 2
			 label_y = rect.top - label_surface.get_height() - 5  #5 pixels above the rect
			 self.screen.blit(label_surface, (label_x, label_y))
			draw_wind_rose(self.screen, (200, 150), 30, self.wind.current_direction, self.wind.current_speed, self.font_small, self.font_small)
			display_info(self.screen, self.boat)
			dev.draw_debug(self.screen)
			pygame.display.flip()
			self.clock.tick(60)

	def run(self):
		while self.running:
			self.state_dict[self.state]()
			
	def setup(self):
		sett.WORLD_WIDTH, sett.WORLD_HEIGHT = 20000, 20000
		clouds = []
		seagulls = []
		stop_buttons = None
		for _ in range(int(sett.WORLD_HEIGHT / 200)):
			clouds.append(Cloud())
		if self.load_data:
			self.load_data = False
			try:
				state = load_game()
				self.boat = state["boat"]
				self.islands = state["islands"]
				self.boat.island.island_name_surface = self.font_large.render(self.boat.island.name.capitalize(), True, sett.colors["WHITE"], sett.colors["BLUE"])
				for island in self.islands:
					for _ in range(random.randint(1, 5)):
						seagulls.append(Seagull(island.x, island.y, max_radius = 2000))
				self.rocks = state["rocks"]
				for rock in self.rocks:
					for _ in range(random.randint(0, 3)):
						seagulls.append(Seagull(rock.x, rock.y, max_radius = 700))
				self.wind = state["wind"]
				return clouds, seagulls, get_stop_btns()
			except Exception as e:
				self.game_running = False
				self.state = "MAIN_MENU"
				return clouds, seagulls, stop_buttons
		self.boat = Boat(x = sett.WIDTH // 2, y = sett.HEIGHT // 2)
		self.wind = Wind()
		boat_x, boat_y = sett.WIDTH // 2, sett.HEIGHT // 2
		starting_island = Island(x=boat_x, y=boat_y + 210, size=200)
		self.islands.append(starting_island)
		for _ in range(random.randint(1, 5)):
				seagulls.append(Seagull(boat_x, boat_y + 210, max_radius = 2000))
		self.rocks = []
		min_distance = 200
		for _ in range(int(sett.WORLD_HEIGHT / 750)):
			x, y = random.uniform(-sett.WORLD_WIDTH, sett.WORLD_WIDTH), random.uniform(-sett.WORLD_HEIGHT, sett.WORLD_HEIGHT)
			#Reject if too close to boat
			while ((x - sett.WIDTH // 2) ** 2 + (y - sett.HEIGHT // 2) ** 2) < min_distance ** 2:
				x, y = random.uniform(-sett.WORLD_WIDTH, sett.WORLD_WIDTH), random.uniform(-sett.WORLD_HEIGHT, sett.WORLD_HEIGHT)
			self.islands.append(Island(x=x, y=y))
			for _ in range(random.randint(1, 5)):
				seagulls.append(Seagull(x, y, max_radius = 2000))
		for _ in range(int(sett.WORLD_HEIGHT / 150)):
			x, y = random.uniform(-sett.WORLD_WIDTH, sett.WORLD_WIDTH), random.uniform(-sett.WORLD_HEIGHT, sett.WORLD_HEIGHT)
			#Reject if too close to boat
			while ((x - sett.WIDTH // 2) ** 2 + (y - sett.HEIGHT // 2) ** 2) < min_distance ** 2:
				x, y = random.uniform(-sett.WORLD_WIDTH, sett.WORLD_WIDTH), random.uniform(-sett.WORLD_HEIGHT, sett.WORLD_HEIGHT)
			self.rocks.append(Rock(x=x, y=y))
			for _ in range(random.randint(0, 3)):
				seagulls.append(Seagull(x, y, max_radius = 700))
		return clouds, seagulls, stop_buttons
			
			
if __name__ == "__main__":
	game = Game()
	game.run()
			