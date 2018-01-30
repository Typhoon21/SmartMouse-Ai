# Importing the libraries
import numpy as np
import matplotlib.pyplot as plt
from random import randint
# Importing the Kivy packages
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.config import Config
from kivy.graphics import Rectangle
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty, ListProperty, BooleanProperty
from kivy.vector import Vector
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.core.window import Window

# Importing the Dqn object from our AI in ai.py
from ai import Dqn

# Adding this line if we don't want the right click to put a red point
Config.set('input', 'mouse', 'mouse, multitouch_on_demand')

n_points = 0
length = 0

# Getting our AI, which we call "brain", and that contains our neural network that represents our Q-function
brain = Dqn(4, 3, 0.9)
action2rotation = [0, 90, -90]
last_reward = 0
scores = []
# Initializing the map
first_update = True

class Player(Widget):
    angle = NumericProperty(0)
    rotation = NumericProperty(0)
    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)
    velocity = ReferenceListProperty(velocity_x, velocity_y)
    sensor1_x = NumericProperty(0)
    sensor1_y = NumericProperty(0)
    sensor1 = ReferenceListProperty(sensor1_x, sensor1_y)
    sensor2_x = NumericProperty(0)
    sensor2_y = NumericProperty(0)
    sensor2 = ReferenceListProperty(sensor2_x, sensor2_y)
    sensor3_x = NumericProperty(0)
    sensor3_y = NumericProperty(0)
    sensor3 = ReferenceListProperty(sensor3_x, sensor3_y)
    signal1 = NumericProperty(0)
    signal2 = NumericProperty(0)
    signal3 = NumericProperty(0)

    def move(self, rotation):
        self.pos = Vector(*self.velocity) + self.pos
        self.rotation = rotation
        self.angle = self.angle + self.rotation
        self.sensor1 = Vector(40, 0).rotate(self.angle) + self.pos
        self.sensor2 = Vector(40, 0).rotate((self.angle + 50) % 360) + self.pos
        self.sensor3 = Vector(40, 0).rotate((self.angle - 50) % 360) + self.pos
        self.signal1 = int(np.sum(field[int(self.sensor1_x) - 20:int(self.sensor1_x) + 20,
                                  int(self.sensor1_y) - 20:int(self.sensor1_y) + 20])) / 400.
        self.signal2 = int(np.sum(field[int(self.sensor2_x) - 20:int(self.sensor2_x) + 20,
                                  int(self.sensor2_y) - 20:int(self.sensor2_y) + 20])) / 400.
        self.signal3 = int(np.sum(field[int(self.sensor3_x) - 20:int(self.sensor3_x) + 20,
                                  int(self.sensor3_y) - 20:int(self.sensor3_y) + 20])) / 400.

        if self.sensor1_x > width - 15 or self.sensor1_x < 15 or self.sensor1_y > height - 15 or self.sensor1_y < 15:
            self.signal1 = 1.
        if self.sensor2_x > width - 15 or self.sensor2_x < 15 or self.sensor2_y > height - 15 or self.sensor2_y < 15:
            self.signal2 = 1.
        if self.sensor3_x > width - 15 or self.sensor3_x < 15 or self.sensor3_y > height - 15 or self.sensor3_y < 15:
            self.signal3 = 1.
class Ball1(Widget):
    pass
class Ball2(Widget):
    pass
class Ball3(Widget):
    pass

class Cheese(Widget):
    pass

class Trap(Widget):
    # blocks objects drawn on the canvas
    trap_objects = ListProperty()

    def add_trap(self, x, y):
        with self.canvas:
            trap = Rectangle(source='trapper.png', pos=(x, y),
                             size=(self.width,
                                   self.height))  # go to the first of the black position list which will be the last one

        self.trap_objects.append(trap)
        field[int(x):int(x) + self.width, int(y):int(y) + self.height] = 1
        if len(self.trap_objects) > 5:
            field[int(self.trap_objects[0].pos[0]):int(self.trap_objects[0].pos[0]) + self.width,
            int(self.trap_objects[0].pos[1]):int(self.trap_objects[0].pos[1]) + self.height] = 0
            self.canvas.remove((self.trap_objects[0]))
            self.trap_objects.remove(self.trap_objects[0])

    def remove_trap(self, obj):
        field[int(obj.pos[0]):int(obj.pos[0]) + 20, int(obj.pos[1]):int(obj.pos[1]) + 20] = 0
        self.trap_objects.remove(obj)
        self.canvas.remove(obj)

    def remove_all_traps(self):
        for trap in self.enemy_objects:
            self.canvas.remove(trap)
        self.trap_objects = []

def init():
    global field
    global first_update
    field = np.zeros((width, height))
    first_update = False

# Initializing the last distance
last_distance = 0

# Creating the game class
class Game(Widget):
    player = ObjectProperty(None)
    ball1 = ObjectProperty(None)
    ball2 = ObjectProperty(None)
    ball3 = ObjectProperty(None)
    cheese = ObjectProperty(None)
    trap = ObjectProperty(None)
    turn_counter = NumericProperty(0)
    high_score = NumericProperty(0)
    score_holder = NumericProperty(0)
    life = NumericProperty(5)
    distance = NumericProperty(1000)
    rotation = 0
    manuel_mode = BooleanProperty(False)
    time = 600

    def serve_player(self):
        self.player.center = self.center
        self.player.velocity = Vector(8, 0)

    def update(self, dt):
        global brain
        global last_reward
        global scores
        global last_distance
        global goal_x
        global goal_y
        global width
        global height
        width = self.width  # assuming user can change window size runtime
        height = self.height
        if first_update:
            init()
        # Move the snake
        xx = self.cheese.pos[0] - self.player.x
        yy = self.cheese.pos[1] - self.player.y
        if self.manuel_mode:
            self.player.move(self.rotation)
            self.rotation = 0
        else:
            orientation = Vector(*self.player.velocity).angle((xx, yy)) / 180.
            last_signal = [self.player.signal1, self.player.signal2, self.player.signal3, orientation]
            action = brain.update(last_reward, last_signal)
            scores.append(brain.score())
            self.rotation = action2rotation[action]
            self.player.move(self.rotation)
        self.distance = int(np.sqrt(xx ** 2 + yy ** 2))
        self.ball1.pos = self.player.sensor1
        self.ball2.pos = self.player.sensor2
        self.ball3.pos = self.player.sensor3

        # Punishments and rewards
        try:
            if field[int(self.player.x), int(self.player.y)] > 0:
                self.player.velocity = Vector(9, 0).rotate(self.player.angle)
                last_reward = -1
            else:
                self.player.velocity = Vector(9, 0).rotate(self.player.angle)
                last_reward = -0.2
                if self.distance < last_distance:
                    last_reward = 0.1
        except IndexError:
            self.player.velocity = Vector(9, 0).rotate(self.player.angle)
            last_reward = -1

        if self.rotation != 0 and last_reward != -1:
            last_reward -= 0.05
        for trap in self.trap.trap_objects:
            aa = self.player.x - trap.pos[0]
            bb = self.player.y - trap.pos[1]
            d = np.sqrt(aa ** 2 + bb ** 2)
            if -20 <= d <= 20:  # Trappe
                last_reward = -0.8
                self.trap.remove_trap(trap)
                self.score_holder = 0
                self.life -= 1
                if self.life <= 0:  # Game over reset everything
                    self.life = 5
                    self.high_score = 0
                    self.time = 600
                    self.score_holder = 0
                    self.generate_cheese()

        if self.out_of_bound():
            last_reward = -1
        # check if the cheese is being eaten
        if self.distance < self.cheese.width:
            last_reward = 1
            self.generate_cheese()
            self.time = 600
        elif self.time <= 0:
            self.generate_cheese()
            self.time = 600
        self.time -= 1
        last_distance = self.distance

    def out_of_bound(self):
        if self.player.x < 15:
            self.player.x = 15
            return True
        elif self.player.x > self.width - 15:
            self.player.x = self.width - 15
            return True
        elif self.player.y < 15:
            self.player.y = 15
            return True
        elif self.player.y > self.height - 15:
            self.player.y = self.height - 15
            return True
        return False

    def generate_cheese(self):
        self.cheese.pos = ([randint(10, width - 20), randint(10, height - 20)])
        self.score_holder += 1
        if self.score_holder > self.high_score:
            self.high_score = self.score_holder
        if self.score_holder % 5 == 0:
            self.life += 1
        five_traps = 5
        while True:  # Set the traps
            x = randint(self.cheese.pos[0] - 250, self.cheese.pos[0] + 250)
            y = randint(self.cheese.pos[1] - 250, self.cheese.pos[1] + 250)
            # Prevent traps to overlap
            if (abs(self.cheese.pos[0] - x) > 20 or abs(self.cheese.pos[1] - y) > 20) and field[x - 20:x + 20,
                                                                                        y - 20:y + 20].any() != 1:
                five_traps -= 1
                self.trap.add_trap(x, y)
                if five_traps == 0:
                    break

    # Keyboard registration for manual mode
    def __init__(self, **kwargs):
        super(Game, self).__init__(**kwargs)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'w' or keycode[1] == 'up':
            self.rotation = 0
        elif keycode[1] == 'a' or keycode[1] == 'left':
            self.rotation = 90
        elif keycode[1] == 'd' or keycode[1] == 'right':
            self.rotation = -90
        return True

class PlaygroundScreen(Screen):
    game_engine = ObjectProperty(None)
    fps = 60

    def on_enter(self):
        # we screen comes into view, start the game
        self.game_engine.serve_player()
        Clock.schedule_interval(self.game_engine.update, 1.0 / self.fps)
        savebtn = Button(text='save', size=(50, 20), pos=(50, 0))
        loadbtn = Button(text='load', size=(50, 20), pos=(100, 0))
        savebtn.bind(on_release=self.save)
        loadbtn.bind(on_release=self.load)
        self.game_engine.add_widget(savebtn)
        self.game_engine.add_widget(loadbtn)

    def save(self, obj):
        print("saving brain...")
        brain.save()
        plt.plot(scores)
        plt.show()

    def load(self, obj):
        print("loading last saved brain...")
        brain.load()
class WelcomeScreen(Screen):
    manuel_option_widget = ObjectProperty(None)
    options_popup = ObjectProperty(None)

    def show_popup(self):
        # instanciate the popup and display it
        self.options_popup = OptionsPopup()
        self.options_popup.open()
class OptionsPopup(Popup):
    speed_option_widget = ObjectProperty(None)
    manuel_option_widget = ObjectProperty(None)

    def on_dismiss(self):
        PlaygroundScreen.fps = self.speed_option_widget.value
        Game.manuel_mode = self.manuel_option_widget.active
# Adding the API Buttons (clear, save and load)
class GameApp(App):
    screen_manager = ObjectProperty(None)

    def build(self):
        Config.set('graphics', 'resizable', False)
        GameApp.screen_manager = ScreenManager()
        self.screen_manager
        # instanciate the screens
        ws = WelcomeScreen(name="welcome_screen")
        ps = PlaygroundScreen(name="playground_screen")

        # register the screens in the screen manager
        self.screen_manager.add_widget(ws)
        self.screen_manager.add_widget(ps)

        return self.screen_manager
# Running the whole thing
if __name__ == '__main__':
    GameApp().run()
