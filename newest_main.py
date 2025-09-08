
import pygame
import random

import settings as sett

from objects import Boat, Cloud, Island, Rock, Wind
from utils import Button, bounce_back, display_info, draw_wind_rose, get_stop_btns, render_multiline, save_game


pygame.init()
pygame.mixer.init()


#WORLD_SIZE = 50000


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
		self.running = True
		self.screen = pygame.display.set_mode((sett.WIDTH, sett.HEIGHT))

		# cache fonts
		self.font_small = pygame.font.Font(None, int(sett.HEIGHT * 0.02))
		self.font_large = pygame.font.Font(None, int(sett.HEIGHT * 0.1))
		self.font_debug = pygame.font.Font(None, 25)

		# state setup
		self.state_dict = {
			"CREDITS" : self.credits,
			"EXIT" : self.exit_game,
			"MAIN_MENU" : self.main_menu,
			"NEW_GAME" : self.new_game,
		}
		self.state = "MAIN_MENU"
		
		self.playlist = [
		"Assets/Calm Waters.mp3",
		"Assets/Waves of Freedom.mp3",
		"Assets/Drift on the Horizon.mp3",
		]
		random.shuffle(self.playlist)
		self.current_track = 0
		self.MUSIC_END = pygame.USEREVENT + 1
		pygame.mixer.music.set_endevent(self.MUSIC_END)
		pygame.mixer.music.load(self.playlist[0])
		pygame.mixer.music.play()
		
		self.mouse_held = False
		self.mouse_pos = None

		# control rects (reused)
		control_height = int(sett.HEIGHT * 0.15)
		self.sail_rect = pygame.Rect(0.05 * sett.WIDTH, sett.HEIGHT - control_height, 0.25 * sett.WIDTH, control_height)
		self.rudder_rect = pygame.Rect(0.35 * sett.WIDTH, sett.HEIGHT - control_height, 0.25 * sett.WIDTH, control_height)
		self.reef_rect = pygame.Rect(0.65 * sett.WIDTH, sett.HEIGHT - control_height, 0.25 * sett.WIDTH, control_height)

	def exit_game(self):
		if self.game_running:
			self.game_running = False
			self.state = "MAIN_MENU"
		else:
			self.running = False
			pygame.quit()

	def handle_button_click(self, pos):
		for button in self.buttons:
			if button.is_clicked(pos):
				if button.text == "Main Menu":
					self.state = "MAIN_MENU"
				elif button.text == "New Game":
					self.state = "NEW_GAME"
					self.game_running = False
				elif button.text == "Credits":
					if self.state == "CREDITS":
						self.state = "MAIN_MENU"
					else:
						self.state = "CREDITS"
				elif button.text == "Exit":
					self.state = "EXIT"

	def handle_events(self, boat=None, stop_buttons=None):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				self.exit_game()
			elif event.type == pygame.MOUSEBUTTONDOWN:
				self.mouse_held = True
				self.mouse_pos = event.pos

				# Handle docked buttons first
				if boat and boat.stopped and stop_buttons:
					for btn in stop_buttons:
						if btn.rect.collidepoint(event.pos):
							if btn.text == "Set Sail":
								boat.release()
							elif btn.text == "Save":
								boat = self.boat
								boat.surface = None
								for island in self.islands:
									island.surface = None
								for rock in self.rocks:
									rock.surface = None
								save_game(boat = boat, islands = self.islands, rocks = self.rocks, wind = self.wind)
							elif btn.text == "Exit":
								self.exit_game()
							return  # stop further processing this click

				# Normal button click handling
				self.handle_button_click(event.pos)

			elif event.type == pygame.MOUSEBUTTONUP:
				self.mouse_held = False
				
			elif event.type == self.MUSIC_END:
				self.current_track = (self.current_track + 1) % len(self.playlist)
				pygame.mixer.music.load(self.playlist[self.current_track])
				pygame.mixer.music.play()

		# Held adjustments for normal controls
		if self.state == "NEW_GAME" and boat and getattr(self, "mouse_held", False) and not boat.stopped:
			if self.sail_rect.collidepoint(self.mouse_pos):
				boat.adjust_sail(0.5 if self.mouse_pos[0] < self.sail_rect.centerx else -0.5)
			elif self.rudder_rect.collidepoint(self.mouse_pos):
				boat.adjust_rudder(0.05 if self.mouse_pos[0] < self.rudder_rect.centerx else -0.05)
			elif self.reef_rect.collidepoint(self.mouse_pos):
				boat.adjust_reef(0.05 if self.mouse_pos[0] < self.reef_rect.centerx else -0.05)

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

	def main_menu(self):
		sett.WORLD_WIDTH, sett.WORLD_HEIGHT = sett.WIDTH, sett.HEIGHT
		#boat = Boat(x = sett.WIDTH // 2, y = sett.HEIGHT // 2)
		wind = Wind()
		clouds = []
		self.game_running = True
		#cam_x, cam_y = sett.WORLD_WIDTH // 2, sett.WORLD_HEIGHT // 2
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
			self.handle_events()
			text_surface = self.font_large.render("POLYSAIL", True, sett.colors["WHITE"])
			self.screen.blit(text_surface, (sett.WIDTH // 2 - text_surface.get_width() // 2, sett.HEIGHT // 10))
			wind.update_wind(current_time)
			for cloud in clouds:
				cloud.apply_wind(wind)
				cloud.draw(self.screen, cam_x, cam_y)
			for button in self.buttons:
				button.draw(self.screen)
			pygame.display.flip()

	def new_game(self):
		self.game_running = True
		dev = DevTools(self.clock)
		
		sett.WORLD_WIDTH, sett.WORLD_HEIGHT = 25000, 25000
		self.boat = Boat(x = sett.WIDTH // 2, y = sett.HEIGHT // 2)
		self.wind = Wind()
		
		stop_buttons = None
		
		clouds = []
		self.islands = []
		# Spawn one guaranteed island right under the boat
		boat_x, boat_y = sett.WIDTH // 2, sett.HEIGHT // 2
		starting_island = Island(x=boat_x, y=boat_y + 210, size=200)  # 400px down, size 800
		self.islands.append(starting_island)
		self.rocks = []
		min_distance = 200
		for _ in range(150):
			clouds.append(Cloud())
		for _ in range(50):
			x, y = random.uniform(-sett.WORLD_WIDTH, sett.WORLD_WIDTH), random.uniform(-sett.WORLD_HEIGHT, sett.WORLD_HEIGHT)
			# reject if too close to boat
			while ((x - sett.WIDTH // 2) ** 2 + (y - sett.HEIGHT // 2) ** 2) < min_distance ** 2:
				x, y = random.uniform(-sett.WORLD_WIDTH, sett.WORLD_WIDTH), random.uniform(-sett.WORLD_HEIGHT, sett.WORLD_HEIGHT)
			self.islands.append(Island(x=x, y=y))
				#islands.append(Island())
		for _ in range(250):
			x, y = random.uniform(-sett.WORLD_WIDTH, sett.WORLD_WIDTH), random.uniform(-sett.WORLD_HEIGHT, sett.WORLD_HEIGHT)
			# reject if too close to boat
			while ((x - sett.WIDTH // 2) ** 2 + (y - sett.HEIGHT // 2) ** 2) < min_distance ** 2:
				x, y = random.uniform(-sett.WORLD_WIDTH, sett.WORLD_WIDTH), random.uniform(-sett.WORLD_HEIGHT, sett.WORLD_HEIGHT)
			self.rocks.append(Rock(x=x, y=y))
				#rocks.append(Rock())
		
		while self.game_running:
			current_time = pygame.time.get_ticks()
			dt = self.clock.get_time() / 1000
			self.screen.fill(sett.colors["LIGHT BLUE"])
		
			cam_x, cam_y = self.boat.x - sett.WIDTH // 2, self.boat.y - sett.HEIGHT // 2
			for cloud in clouds:
				cloud.apply_wind(self.wind)
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
							stop_buttons = get_stop_btns()
					elif (self.boat.x - island.x) ** 2 + (self.boat.y - island.y) ** 2 <= island.size ** 2:
						# inside the island, but too fast to dock
						bounce_back(self.boat, island)
			
			self.wind.update_wind(current_time)
			
			for island in self.islands:
				offset_x = island.x - cam_x
				offset_y = island.y - cam_y
				if not (offset_x + island.size < 0 or offset_x - island.size > sett.WIDTH or offset_y + island.size < 0 or offset_y - island.size > sett.HEIGHT):
					island.draw(self.screen, cam_x, cam_y)
			for rock in self.rocks:
				offset_x = rock.x - cam_x
				offset_y = rock.y - cam_y
				if not (offset_x + rock.size < 0 or offset_x - rock.size > sett.WIDTH or offset_y + rock.size < 0 or offset_y - rock.size > sett.HEIGHT):
					rock.draw(self.screen, cam_x, cam_y)
			self.boat.draw(self.screen, cam_x, cam_y)
			for cloud in clouds:
				offset_x = cloud.x - cam_x
				offset_y = cloud.y - cam_y
				if not (offset_x + cloud.size < 0 or offset_x - cloud.size > sett.WIDTH or offset_y + cloud.size < 0 or offset_y - cloud.size > sett.HEIGHT):
					cloud.draw(self.screen, cam_x, cam_y)
			if self.boat.stopped:
				for btn in stop_buttons:
					btn.draw(self.screen)
			self.handle_events(self.boat, stop_buttons = stop_buttons if stop_buttons else None)
			
			pygame.draw.rect(self.screen, sett.colors["RED"], self.sail_rect)
			pygame.draw.rect(self.screen, sett.colors["RED"], self.rudder_rect)
			pygame.draw.rect(self.screen, sett.colors["RED"], self.reef_rect)
			draw_wind_rose(self.screen, (200, 150), 30, self.wind.current_direction, self.wind.current_speed, self.font_small, self.font_small)
			display_info(self.screen, self.boat)
			dev.draw_debug(self.screen)
			pygame.display.flip()
			self.clock.tick(60)

	def run(self):
		while self.running:
			self.state_dict[self.state]()
			
			
if __name__ == "__main__":
	game = Game()
	game.run()
			