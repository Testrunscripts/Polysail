
WIDTH, HEIGHT = 0, 0
WORLD_WIDTH, WORLD_HEIGHT = 10000, 10000


colors = {
"BLACK" : (0, 0, 0),
"BLUE" : (50, 150, 200),
"GREEN" : (40, 200, 100, 255),
"GREY" : (91, 102, 125),
"LIGHT BLUE" : (100, 200, 255),
"RED" : (200, 50, 50),
"WHITE" : (250, 250, 250, 255),
}


credit_text = "Designed and Developed by: Noah Huskey\n \nMade in Pygame\n \nSoundtrack created in Udio"


def set_display(info):
	global WIDTH, HEIGHT
	WIDTH, HEIGHT = info.current_w, info.current_h
