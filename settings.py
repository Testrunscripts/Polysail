
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


credit_text = "Designed and Developed by: Mytraya\n \nMade in Pygame\n \nSoundtrack created in Udio"


howtoplay_text = """- Hold the left (or press Q) or right side (or press E)\nof the sail pad to trim the sails\n\n- Hold either side of the rudder pad to control the rudder (A and D)\n\n- Hold the left side of the reef pad (or press W) to unreef the sails,\nhold the right side (or press S) to reef them again\n\n- Dock at an island to bring up the menu\n\n- Seagulls can give away island and rock locations."""


def set_display(info):
	global WIDTH, HEIGHT
	WIDTH, HEIGHT = info.current_w, info.current_h
