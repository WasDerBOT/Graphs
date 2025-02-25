import csv
import os
import sqlite3
import sys
from math import sin, cos
from random import randint

import pygame
import pygame_widgets
from pygame.locals import *
from pygame_widgets.dropdown import Dropdown
from pygame_widgets.slider import Slider
from pygame_widgets.textbox import TextBox

from button import Button

pygame.init()
size = width, height = 800, 600
screen = pygame.display.set_mode(size)
pygame.mixer.music.load('valve.mp3')
pygame.mixer.music.play()
intro_timer = 0
intro_v = -100
intro_clock = pygame.time.Clock()
intro_flag = False
intro_text = 0
FPS = 60
screen_width = 800
screen_height = 600
display_surface = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Graphs")
lives = 0
clock = pygame.time.Clock()
timer_clock = pygame.time.Clock()
current_dist = 10
BLACK = (0, 0, 0)
NODE_SUCCESSFUL_PATH = (0, 153, 76)
NODE_WRONG_PATH = (194, 36, 25)
NODE_COLOR = (125, 125, 125)
NODE_PATH_COLOR = (13, 212, 212)
PATH_COLOR = NODE_PATH_COLOR
NODE_FINISH_COLOR = (245, 236, 66)
NODE_START_COLOR = (164, 245, 66)
USER = ''
FONT = pygame.font.Font('Cinematic.otf', size=32)

node_radius = 30
current_level = -1
inputed = False
music_check = True
check_slider = True


def set_dist():
    global current_dist, inputed, is_inputting
    is_inputting = False
    inputed = True

    try:
        current_dist = int(textbox.getText())
        textbox.setText("")
    except ValueError:
        print("Type number!")


def set_level_name():
    name = level_name.getText()
    level_name.setText("")


textbox = TextBox(display_surface, 255, 100, 300, 100, fontSize=40,
                  borderColour=(255, 255, 255, 125), textColour=(0, 0, 0),
                  radius=10, borderThickness=10, placeholderText="Введите длину", onSubmit=set_dist)

slider = Slider(screen, 100, 150, 600, 40, min=0, max=100, step=1, colour=(255, 255, 255),
                handleColour=(122, 122, 122))

output = TextBox(screen, 0, 250, 200, 75, fontSize=70, textColour=(255, 255, 255), colour=(0, 0, 0))

slider.hide()
output.hide()
textbox.hide()


users_path = [].copy()


def get_mouse_pos():
    m_pos = pygame.mouse.get_pos()
    m_pos = Vector(m_pos[0], m_pos[1])
    m_pos = (m_pos - camera_center) * scale + camera_center
    return m_pos


class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def get_tuple(self):
        return self.x, self.y

    def get_length(self):
        return (self.x ** 2 + self.y ** 2) ** 0.5

    def __copy__(self):
        return Vector(self.x, self.y)

    def get_normalized(self):
        return self.__copy__() / self.get_length()

    def __add__(self, other):
        if type(other) != Vector:
            raise ValueError
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        if type(other) != Vector:
            raise ValueError
        return Vector(self.x - other.x, self.y - other.y)

    def __truediv__(self, other):
        if type(other) != int and type(other) != float or other == 0:
            return Vector(self.x / 0.0001, self.y / 0.0001)
        return Vector(self.x / other, self.y / other)

    def __mul__(self, other):
        if type(other) != int and type(other) != float:
            raise ValueError
        return Vector(self.x * other, self.y * other)

    def __str__(self):
        return f"{self.x} : {self.y}"

    def limited(self, a):
        if self.get_length() > a:
            return self.get_normalized() * a
        return self


mx = 0


class Node:
    def __init__(self, position: Vector, destinations=[], distances=[]):
        self.position = position
        self.destinations = destinations.copy()
        self.distances = distances.copy()
        self.velocity = Vector(0, 0)

    def __copy__(self):
        return Node(self.position, self.destinations)

    def __str__(self):
        return str(self.position)

    def draw(self, surface, node_color, radius):

        radius /= scale
        position = (self.position - camera_center) / scale + camera_center
        pygame.draw.circle(surface, node_color, position.get_tuple(), radius)
        pygame.draw.circle(surface, (int(node_color[0] * 0.55), int(node_color[1] * 0.55), int(node_color[2] * 0.55)),
                           position.get_tuple(), int(radius), int(radius * 0.3))
        global users_path
        for dest in self.destinations:
            if self in users_path:
                if dest in users_path:
                    draw_connection(surface, node_color, self, dest)
            else:
                draw_connection(surface, node_color, self, dest)
            if self is not path_start and self is not path_finish and (dest is path_start or dest is path_finish):
                dest.draw(surface, node_color, radius)

        if self is path_start:
            FONT = pygame.font.Font('Cinematic.otf', size=int(50 / scale))
            text_surface = FONT.render(str("S"), True, (255, 255, 255))
            display_surface.blit(text_surface,
                                 ((self.position + Vector(-node_radius * 0.25,
                                                          -node_radius * 0.75) - camera_center) / scale + camera_center).get_tuple())
        if self is path_finish:
            FONT = pygame.font.Font('Cinematic.otf', size=int(50 / scale))
            text_surface = FONT.render(str("F"), True, (255, 255, 255))
            display_surface.blit(text_surface,
                                 ((self.position + Vector(-node_radius * 0.25,
                                                          -node_radius * 0.75) - camera_center) / scale + camera_center).get_tuple())

    def interact_with(self, other):
        r = other.position - self.position
        direct = r.get_normalized()
        length = r.get_length() / (2 * node_radius)
        if other in self.destinations:
            length /= min(max(1, self.distances[self.destinations.index(other)]), 30) ** 0.25
        force = Vector(0, 0)
        if other in self.destinations or self in other.destinations:
            force = direct * length ** 3
            force *= 0.01

        force -= direct / length ** 3.5
        period = 1 / FPS
        dv = force * period * 400
        global mx
        mx = max(mx, dv.get_length())
        if abs(dv.get_length()) < 0.3:
            return
        self.velocity += dv.limited(node_radius)

    def process(self):
        self.position += self.velocity


def draw_connection(surface, node_color, a: Node, b: Node):
    dist = a.distances[a.destinations.index(b)]

    if a.position.get_tuple() == b.position.get_tuple():
        return
    width = int(node_radius * 0.3)
    width /= scale
    width = int(width)
    text_pos = (a.position + b.position) / 2
    FONT = pygame.font.Font('Cinematic.otf', size=int(32 / scale))
    text_surface = FONT.render(str(dist), True, (255, 255, 255))

    ta = (a.position - camera_center) / scale + camera_center
    tb = (b.position - camera_center) / scale + camera_center

    direction = (tb - ta).get_normalized().get_tuple()
    if a.position.get_tuple()[0] > b.position.get_tuple()[0]:
        perp = Vector(-direction[1], direction[0]).get_normalized()
        display_surface.blit(text_surface, ((text_pos + perp * 30 - camera_center) / scale + camera_center).get_tuple())

    pygame.draw.line(surface, (int(node_color[0] * 0.55), int(node_color[1] * 0.55), int(node_color[2] * 0.55)),
                     ta.get_tuple(), tb.get_tuple(), width)
    pygame.draw.circle(surface, (int(node_color[0] * 0.55), int(node_color[1] * 0.55), int(node_color[2] * 0.55)),
                       ta.get_tuple(), width / 2)
    pygame.draw.circle(surface, (int(node_color[0] * 0.55), int(node_color[1] * 0.55), int(node_color[2] * 0.55)),
                       tb.get_tuple(), width / 2)


is_inputting = False
is_grabbing = False
is_displacing = False
is_connecting = False
right_mouse_button_mode = 0
shift = False
alt = False
displacement_start = Vector(0, 0)
grabbed = Node(Vector(-10e8, -10e8))
paused = False
connecting_from = None
connecting_to = None
path_start = None
path_finish = None
game_mod = False
Objects = []
right_path = []
camera_pos = Vector(0, 0)
camera_size = Vector(800, 600)
camera_center = camera_pos + camera_size / 2
scale = 1
timer = 0
is_admin = True


def save(start, finish, name="UNTITLED"):
    with open(f"levels/{name}.csv", "w") as f:
        writer = csv.writer(
            f,
            delimiter=";", quoting=csv.QUOTE_NONNUMERIC
        )
        writer.writerow([Objects.index(start), Objects.index(finish)])

        for i in range(len(Objects)):
            a = Objects[i]
            writer.writerow(
                [str(a.position.x) + "," + str(a.position.y), ','.join([str(Objects.index(i)) for i in a.destinations]),
                 ','.join([str(k) for k in a.distances])])


def load(name="NOTPROVIDED"):
    if name == "NOTPROVIDED":
        raise ValueError
    objects_local = [].copy()
    destndist = []
    with open(f"levels/{name}.csv", "r") as f:
        reader = csv.reader(
            f,
            delimiter=";", quoting=csv.QUOTE_NONNUMERIC
        )

        for index, line in enumerate(reader):
            if index == 0:
                start, finish = line
                continue
            if not line:
                continue

            pos = [float(i) for i in line[0].split(",")]
            pos = Vector(pos[0], pos[1])

            objects_local.append(Node(pos))
            destndist.append([[int(i) for i in line[1].split(",")].copy(), [int(i) for i in line[2].split(",")]])

        for i in range(len(destndist)):
            objects_local[i].destinations = [objects_local[k] for k in destndist[i][0]]
            objects_local[i].distances = [k for k in destndist[i][1]]
        return objects_local.copy(), start, finish


class Graph:
    def __init__(self, Nodes):
        self.Nodes = Nodes
        self.visited = []

    def __find__(self, vertex: Node, finish: Node, current_path: list, current_path_dist: int):
        further_paths = []
        if vertex is finish:
            return [current_path, current_path_dist].copy()
        for dest in vertex.destinations:
            if dest in current_path:
                continue

            temp = self.__find__(dest, finish, (current_path + [dest]).copy(),
                                 current_path_dist + vertex.distances[vertex.destinations.index(dest)])
            if finish in temp or True:
                further_paths.append(temp)

        further_paths = sorted(further_paths, key=lambda x: x[-1])
        if not further_paths:
            return [[], 10e9].copy()
        return further_paths[0].copy()

    def findPath(self, start: Node, finish: Node) -> list:
        temp = self.__find__(start, finish, [start].copy(), 0)
        return temp


def get_font(size):
    return pygame.font.SysFont('arial', size)


def random_node(node, objects_local):
    if randint(0, 100) > 80 or len(node.destinations) <= 1:
        a = randint(1, 100) / 100
        pos = Vector(node.position.x + cos(a), node.position.y + sin(a))
        dist = randint(1, 50)
        temp = Node(pos, [node].copy(), [dist].copy())
        node.destinations.append(temp)
        node.distances.append(dist)
        objects_local.append(temp)
    else:
        next = randint(0, len(node.destinations) - 1)
        random_node(node.destinations[next], objects_local)


def get_random_graph(vertices):
    objects_local = [Node(Vector(0, 0))].copy()
    for i in range(vertices):
        random_node(objects_local[0], objects_local)

    return objects_local


def is_right_path():
    for obj in users_path:
        print(Objects.index(obj))
    print("-----")
    for obj in right_path:
        print(Objects.index(obj))
    if len(users_path) != len(right_path):
        return False
    for node in right_path:
        if node not in users_path:
            return False
    return True


def check_path():
    global users_path, right_path, lives
    if is_right_path():
        print(is_right_path())
        next_level()
    else:
        lives -= 1
    if lives <= 0:
        global current_level, timer
        timer = 1
        current_level = -1
        start_campaign()


def intro():
    global intro_timer, intro_v, intro_flag, intro_text
    while True:
        pygame.display.set_caption('Меню')
        screen.fill((0, 0, 0))
        if intro_timer < 5:
            KOLHOZ_TEXT = get_font(125).render('KOLHOZ', True, 'White')
            KOLHOZ_RECT = KOLHOZ_TEXT.get_rect(center=(intro_v, 200))
        elif intro_timer < 11:
            SOWTFARE_TEXT = get_font(125).render('SOFTWARE', True, 'Orange')
            SOWTFARE_RECT = SOWTFARE_TEXT.get_rect(center=(425, 400))
            SOWTFARE_TEXT.set_alpha(intro_text)
            intro_flag = True
        screen.blit(KOLHOZ_TEXT, KOLHOZ_RECT)
        if intro_flag:
            intro_text += 0.18
            screen.blit(SOWTFARE_TEXT, SOWTFARE_RECT)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if intro_timer >= 9.5 or (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE):
                pygame.mixer.music.load('Tetris.mp3')
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play(-1)
                menu()
        pygame.display.update()
        intro_timer += intro_clock.tick() / 1000
        intro_v = - 100 + 100 * intro_timer


def menu():
    while True:
        pygame.display.set_caption('Меню')
        screen.fill((0, 0, 0))
        MENU_TEXT = get_font(125).render('Меню', True, 'White')
        MENU_RECT = MENU_TEXT.get_rect(center=(400, 150))
        screen.blit(MENU_TEXT, MENU_RECT)
        PLAY_BUTTON = Button(image=None, pos=(400, 275), text_input='ИГРАТЬ', font=get_font(75), base_color='White',
                             hovering_color='Green')
        OPTIONS_BUTTON = Button(image=None, pos=(400, 350), text_input='НАСТРОЙКИ', font=get_font(75),
                                base_color='White', hovering_color='Green')
        TABLE_BUTTON = Button(image=None, pos=(400, 425), text_input='ТАБЛИЦА ЛИДЕРОВ', font=get_font(75),
                              base_color='White', hovering_color='Green')
        QUIT_BUTTON = Button(image=None, pos=(400, 500), text_input='ВЫХОД', font=get_font(75), base_color='White',
                             hovering_color='Green')
        for button in [PLAY_BUTTON, OPTIONS_BUTTON, TABLE_BUTTON, QUIT_BUTTON]:
            button.changeColor(pygame.mouse.get_pos())
            button.update(screen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if PLAY_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    create()
                if OPTIONS_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    options()

                if TABLE_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    table()
                if QUIT_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    pygame.quit()
                    sys.exit()
        pygame.display.update()


def create():
    global is_admin
    lshift = False
    rshift = False
    lalt = False
    ralt = False
    rctrl = False
    while True:
        screen.fill((0, 0, 0))
        GAME_BUTTON = Button(image=None, pos=(400, 125), text_input='КАМПАНИЯ', font=get_font(75), base_color='White',
                             hovering_color='Green')
        LEVELS_BUTTON = Button(image=None, pos=(400, 225), text_input='КАТАЛОГ УРОВНЕЙ', font=get_font(75),
                               base_color='White', hovering_color='Green')
        CREATE_LEVEL_BUTTON = Button(image=None, pos=(400, 325), text_input='СОЗДАНИЕ УРОВНЕЙ', font=get_font(75),
                                     base_color='White', hovering_color='Green')
        BACK_BUTTON = Button(image=None, pos=(400, 500), text_input='НАЗАД', font=get_font(75), base_color='White',
                             hovering_color='Green')
        buttons = [GAME_BUTTON, LEVELS_BUTTON, BACK_BUTTON]
        if is_admin:
            buttons.append(CREATE_LEVEL_BUTTON)
        for button in buttons:
            button.changeColor(pygame.mouse.get_pos())
            button.update(screen)
        for event in pygame.event.get():
            if event.type == KEYDOWN and hasattr(event, 'mod') and event.mod & pygame.KMOD_LSHIFT:
                lshift = True
            if event.type == KEYUP and hasattr(event, 'mod') and event.key == pygame.K_LSHIFT:
                lshift = False

            if event.type == KEYDOWN and hasattr(event, 'mod') and event.mod & pygame.KMOD_LALT:
                lalt = True
            if event.type == KEYUP and hasattr(event, 'mod') and event.key == pygame.K_LALT:
                lalt = False

            if event.type == KEYDOWN and hasattr(event, 'mod') and event.mod & pygame.KMOD_RSHIFT:
                rshift = True
            if event.type == KEYUP and hasattr(event, 'mod') and event.key == pygame.K_RSHIFT:
                rshift = False

            if event.type == KEYDOWN and hasattr(event, 'mod') and event.mod & pygame.KMOD_RALT:
                ralt = True
            if event.type == KEYUP and hasattr(event, 'mod') and event.key == pygame.K_RALT:
                ralt = False

            if event.type == KEYDOWN and hasattr(event, 'mod') and event.mod & pygame.KMOD_RCTRL:
                rctrl = True
            if event.type == KEYUP and hasattr(event, 'mod') and event.key == pygame.K_RCTRL:
                rctrl = False

            if event.type == KEYDOWN and event.key == pygame.K_KP_PLUS and lalt and ralt and lshift and rshift and rctrl:
                is_admin = not is_admin

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if GAME_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    start_campaign()
                if LEVELS_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    choose_level()
                if CREATE_LEVEL_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    play()
                if BACK_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    menu()
        pygame.display.update()


LEVELS = ['__LEVEL1__', '__LEVEL2__', '__LEVEL3__', '__LEVEL4__', '__LEVEL5__']  # сюда вставь названия уровней кампании


def start_campaign(current_lives=3):
    running = True
    global lives, current_level, USER
    user_name = TextBox(display_surface, 200, 170, 350, 100, fontSize=40,
                         borderColour=(255, 255, 255, 125), textColour=(0, 0, 0),
                         radius=10, borderThickness=10, placeholderText="Ваше имя")
    lives = current_lives

    current_level += 1

    global Objects
    print(current_level)
    Objects, start_index, finish_index = load(LEVELS[current_level])
    global path_start, path_finish
    path_start = Objects[int(start_index)]
    path_finish = Objects[int(finish_index)]
    BACK_BUTTON = Button(image=None, pos=(400, 500), text_input='НАЗАД', font=get_font(75), base_color='White',
                         hovering_color='Green')
    NEXT_BUTTON = Button(image=None, pos=(400, 400), text_input='НАЧАТЬ', font=get_font(75), base_color='White',
                         hovering_color='Green')
    while running:
        screen.fill((0, 0, 0))
        for button in [BACK_BUTTON, NEXT_BUTTON]:
            button.changeColor(pygame.mouse.get_pos())
            button.update(screen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if BACK_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    user_name.hide()
                    create()
                if NEXT_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    user_name.hide()
                    USER = user_name.getText()
                    play()
        pygame_widgets.update(pygame.event.get())
        pygame.display.update()


def win():
    pass


def next_level():
    global current_level, Objects, right_path
    if current_level == len(LEVELS):
        win()
        return
    current_level += 1
    for obj in Objects:
        obj.destinations.clear()
        obj.distances.clear()
    right_path.clear()

    global connecting_from
    connecting_from = None

    Objects.clear()
    if current_level == len(LEVELS):
        win()
    Objects, start_index, finish_index = load(LEVELS[current_level])
    global path_start, path_finish, timer
    path_start = Objects[int(start_index)]
    path_finish = Objects[int(finish_index)]
    play()


def choose_level():
    pygame.display.set_caption('Выбор уровня')
    running = True
    onlyfiles = list(map(lambda x: x[:-4], os.listdir('levels')))
    dropdown = Dropdown(
        screen, 420, 170, 280, 50, name='СПИСОК УРОВНЕЙ',
        choices=onlyfiles,
        borderRadius=3, colour=pygame.Color('green'), direction='down', textHAlign='left',
        fontSize=40
    )
    dropdown.show()
    BACK_BUTTON = Button(image=None, pos=(400, 500), text_input='НАЗАД', font=get_font(75), base_color='White',
                         hovering_color='Green')
    LOAD_LEVEL_BUTTON = Button(image=None, pos=(200, 200), text_input='ЗАГРУЗИТЬ', font=get_font(55),
                               base_color='White',
                               hovering_color='Green')
    while running:
        screen.fill((0, 0, 0))
        for button in [BACK_BUTTON, LOAD_LEVEL_BUTTON]:
            button.changeColor(pygame.mouse.get_pos())
            button.update(screen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if BACK_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    dropdown.hide()
                    create()
                if LOAD_LEVEL_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    dropdown.hide()
                    global Objects
                    Objects, start_index, finish_index = load(dropdown.getSelected())
                    global path_start, path_finish
                    print(start_index, finish_index)
                    path_start = Objects[int(start_index)]
                    path_finish = Objects[int(finish_index)]

                    play()
        pygame_widgets.update(pygame.event.get())
        pygame.display.update()


def play():
    users_path.clear()
    global is_displacing, is_inputting, inputed, paused, is_grabbing, connecting_from, grabbed, shift, alt, scale, current_level
    global right_path, path_start, path_finish, right_mouse_button_mode, is_admin, Objects, timer, timer_clock, lives, game_mod
    textbox.show()
    running = True
    esc = False
    BACK_BUTTON = Button(image=None, pos=(150, 550), text_input='НАЗАД', font=get_font(75), base_color='White',
                         hovering_color='Green')
    if is_admin:
        SAVE_LEVEL_BUTTON = Button(image=None, pos=(550, 550), text_input='СОХРАНИТЬ', font=get_font(75),
                                   base_color='White',
                                   hovering_color='Green')
        SAVE_LEVEL_BUTTON.reverse()
    BACK_BUTTON.reverse()
    if not Objects:
        Objects = []

    if lives != 0:
        game_mod = True
    while running:
        events = pygame.event.get()
        pygame_widgets.update(events)

        if esc:
            BACK_BUTTON.changeColor(pygame.mouse.get_pos())
            BACK_BUTTON.update(screen)
            if is_admin:
                SAVE_LEVEL_BUTTON.changeColor(pygame.mouse.get_pos())
                SAVE_LEVEL_BUTTON.update(screen)
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if BACK_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    for obj in Objects:
                        obj.destinations.clear()
                        obj.distances.clear()
                    right_path.clear()
                    Objects.clear()
                    connecting_from = None
                    textbox.hide()
                    lives = 0
                    timer = 0
                    game_mod = False
                    current_level = -1
                    create()
                if game_mod and CHECK_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    temp = Graph(Objects)
                    right_path.clear()
                    if path_start not in Objects:
                        path_start = None
                    if path_finish not in Objects:
                        path_finish = None
                    if path_start is not None and path_finish is not None:
                        right_path, dist = temp.findPath(path_start, path_finish)
                    check_path()

                if is_admin and SAVE_LEVEL_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    textbox.hide()
                    save_menu()
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = get_mouse_pos()

                for obj in Objects:
                    if (mouse_pos - obj.position).get_length() < node_radius:
                        if shift:
                            obj.destinations.clear()
                            obj.distances.clear()
                            for o in Objects:
                                if obj in o.destinations:
                                    o.distances.pop(o.destinations.index(obj))
                                    o.destinations.remove(obj)
                        elif alt:
                            if obj in users_path:
                                users_path.remove(obj)
                            else:
                                users_path.append(obj)
                        else:
                            is_grabbing = True
                            grabbed = obj

                        break
            if event.type == KEYDOWN and hasattr(event, 'mod') and event.key == pygame.K_ESCAPE:
                esc = not esc
                BACK_BUTTON.reverse()
                if is_admin:
                    SAVE_LEVEL_BUTTON.reverse()
            if event.type == KEYDOWN and event.key == pygame.K_g:
                for obj in Objects:
                    obj.destinations.clear()
                    obj.distances.clear()
                right_path.clear()
                Objects.clear()
                connecting_from = None
                Objects = get_random_graph(30)

            if event.type == KEYDOWN and hasattr(event, 'mod') and event.mod & pygame.KMOD_LSHIFT:
                shift = True
            if event.type == KEYUP and hasattr(event, 'mod') and event.key == pygame.K_LSHIFT:
                shift = False

            if event.type == KEYDOWN and hasattr(event, 'mod') and event.mod & pygame.KMOD_LALT:
                alt = True
            if event.type == KEYUP and hasattr(event, 'mod') and event.key == pygame.K_LALT:
                alt = False

            if event.type == MOUSEBUTTONDOWN and event.button == 2:
                mouse_pos = get_mouse_pos()
                displacement_start = None
                for obj in Objects:
                    if (mouse_pos - obj.position).get_length() < node_radius:
                        for o in Objects:
                            if obj in o.destinations:
                                o.distances.pop(o.destinations.index(obj))
                                o.destinations.remove(obj)
                        Objects.remove(obj)
                        if obj in right_path:
                            right_path.remove(obj)
                        break
                else:
                    continue  # this functional currently turned off
                    is_displacing = True
                    displacement_start = Vector(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1])
            if event.type == MOUSEBUTTONUP and event.button == 2:
                is_displacing = False

            if event.type == MOUSEBUTTONDOWN and event.button == 3:
                mouse_pos = get_mouse_pos()
                for obj in Objects:
                    if (mouse_pos - obj.position).get_length() < node_radius:
                        right_path.clear()
                        if right_mouse_button_mode == 0:
                            connecting_from = obj
                        elif right_mouse_button_mode == 1:
                            path_start = obj
                        elif right_mouse_button_mode == 2:
                            path_finish = obj

                        break
                else:
                    Objects.append(Node(mouse_pos))
                    continue

            if event.type == MOUSEBUTTONUP and event.button == 3:
                mouse_pos = get_mouse_pos()
                for obj in Objects:
                    if (mouse_pos - obj.position).get_length() < node_radius:
                        if connecting_from is not None:
                            is_inputting = True
                        connecting_to = obj
                        break

            if event.type == MOUSEWHEEL:
                scale = max(min((scale * 10 - event.y) / 10, 10), 1)

            if event.type == MOUSEBUTTONUP and grabbed:
                grabbed = None
                is_grabbing = False
            if event.type == KEYDOWN and event.key == pygame.K_q:
                paused = not paused
            if event.type == KEYDOWN and event.key == pygame.K_SPACE:
                right_mouse_button_mode += 1
                right_mouse_button_mode %= 3
                if right_mouse_button_mode == 0:
                    print("Connecting mode")
                elif right_mouse_button_mode == 1:
                    print("Start setting mode")
                elif right_mouse_button_mode == 2:
                    print("Finish setting mode")

            if event.type == KEYDOWN and event.key == pygame.K_e:
                temp = Graph(Objects)
                right_path.clear()
                if path_start not in Objects:
                    path_start = None
                if path_finish not in Objects:
                    path_finish = None
                if path_start is not None and path_finish is not None:
                    right_path, dist = temp.findPath(path_start, path_finish)

            if event.type == KEYDOWN and event.key == pygame.K_c:
                for obj in Objects:
                    obj.destinations.clear()
                    obj.distances.clear()
                right_path.clear()
                Objects.clear()
                connecting_from = None
        # Processing
        for obj in Objects:
            if paused:
                break
            obj.velocity *= 0.8

            # Kinda gravity
            # obj.velocity += Vector(0, 1) * 30 / FPS

            for another in Objects:
                if another == obj:
                    continue
                obj.interact_with(another)

        for obj in Objects:
            if paused:
                break
            if abs(obj.position.get_length()) > 10000:
                Objects.remove(obj)
            obj.process()

        if is_grabbing:
            mouse_pos = get_mouse_pos()

            grabbed.velocity = mouse_pos - grabbed.position
            if paused:
                grabbed.position = mouse_pos

        if is_displacing:
            current = Vector(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1])
            displacement = current - displacement_start
            displacement_start = current.__copy__()
            camera_pos += displacement
            camera_center = camera_pos + camera_size / 2
        # Drawing
        display_surface.fill(BLACK)
        for obj in Objects:
            obj.draw(display_surface, NODE_COLOR, node_radius)
        for obj in users_path:
            obj.draw(display_surface, PATH_COLOR, node_radius)

        if is_inputting:
            textbox.draw()
        if inputed:
            inputed = False
            if connecting_to == connecting_from:
                a = [Vector(0, -node_radius),
                     Vector(0, node_radius),
                     Vector(-node_radius, 0),
                     Vector(node_radius, 0)]

                new = Node(a[randint(0, 3)] + mouse_pos)
                new.destinations.append(connecting_to)
                new.distances.append(current_dist)
                connecting_to.destinations.append(new)
                connecting_to.distances.append(current_dist)
                Objects.append(new)
            elif connecting_from is not None:
                connecting_from.distances.append(current_dist)
                connecting_from.destinations.append(connecting_to)
                connecting_to.destinations.append(connecting_from)
                connecting_to.distances.append(current_dist)
            connecting_to = None
            connecting_from = None
        if esc:
            BACK_BUTTON.changeColor(pygame.mouse.get_pos())
            BACK_BUTTON.update(screen)
            if is_admin:
                SAVE_LEVEL_BUTTON.changeColor(pygame.mouse.get_pos())
                SAVE_LEVEL_BUTTON.update(screen)

        clock.tick(FPS)
        if game_mod:
            TIMER_TEXT = get_font(35).render(f'ВРЕМЯ:{300 - round(timer) + 1}', True, 'White')
            TIMER_RECT = TIMER_TEXT.get_rect(center=(100, 50))
            LIVES_TEXT = get_font(35).render(f'ЖИЗНИ:{lives}', True, 'White')
            LIVES_RECT = LIVES_TEXT.get_rect(center=(650, 50))
            screen.blit(TIMER_TEXT, TIMER_RECT)
            screen.blit(LIVES_TEXT, LIVES_RECT)
            timer += timer_clock.tick() / 1000
            CHECK_BUTTON = Button(image=None, pos=(650, 480), text_input='ПРОВЕРИТЬ', font=get_font(45),
                                  base_color='White',
                                  hovering_color='Green')
            CHECK_BUTTON.changeColor(pygame.mouse.get_pos())
            CHECK_BUTTON.update(screen)
        pygame.display.update()


def save_menu():
    textbox.hide()
    save_flag = False
    global level_name
    level_name = TextBox(display_surface, 50, 100, 350, 100, fontSize=40,
                         borderColour=(255, 255, 255, 125), textColour=(0, 0, 0),
                         radius=10, borderThickness=10, placeholderText="Название уровня", onSubmit=set_level_name)

    pygame.display.set_caption('Сохранение уровня')
    running = True

    BACK_BUTTON = Button(image=None, pos=(400, 500), text_input='НАЗАД', font=get_font(75), base_color='White',
                         hovering_color='Green')
    SAVE_LEVEL_BUTTON = Button(image=None, pos=(580, 160), text_input='СОХРАНИТЬ', font=get_font(55),
                               base_color='White',
                               hovering_color='Green')
    while running:
        screen.fill((0, 0, 0))
        if save_flag:
            SAVE_TEXT = get_font(50).render('СОХРАНЕНО', True, 'Green')
            SAVE_RECT = SAVE_TEXT.get_rect(center=(400, 250))
            screen.blit(SAVE_TEXT, SAVE_RECT)
        for button in [BACK_BUTTON, SAVE_LEVEL_BUTTON]:
            button.changeColor(pygame.mouse.get_pos())
            button.update(screen)
        events = pygame.event.get()
        pygame_widgets.update(events)
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if BACK_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    level_name.hide()
                    play()
                if SAVE_LEVEL_BUTTON.checkForInput(pygame.mouse.get_pos()) or (
                        event.type == KEYDOWN and event.key == pygame.K_RETURN):
                    if not path_start or not path_finish:
                        print("Start or finish is not set !")
                        continue
                    save(path_start, path_finish, level_name.getText())
                    save_flag = True
        pygame.display.update()


def options():
    global music_check, check_slider, output, slider
    slider.show()
    output.show()
    if check_slider:
        output.disable()
        check_slider = False
    while True:
        pygame.display.set_caption('Настройки')
        screen.fill((0, 0, 0))
        OPTIONS_TEXT = get_font(125).render('Настройки', True, 'White')
        OPTIONS_RECT = OPTIONS_TEXT.get_rect(center=(400, 70))
        screen.blit(OPTIONS_TEXT, OPTIONS_RECT)

        BACK_BUTTON = Button(image=None, pos=(400, 550), text_input='НАЗАД', font=get_font(75), base_color='White',
                             hovering_color='Green')
        TURN_ON_BUTTON = Button(image=None, pos=(400, 450), text_input='ВКЛЮЧИТЬ МУЗЫКУ', font=get_font(75),
                                base_color='White', hovering_color='Green')
        TURN_OFF_BUTTON = Button(image=None, pos=(400, 450), text_input='ВЫКЛЮЧИТЬ МУЗЫКУ', font=get_font(75),
                                 base_color='White', hovering_color='Green')
        BACK_BUTTON.changeColor(pygame.mouse.get_pos())
        BACK_BUTTON.update(screen)

        if music_check:
            TURN_OFF_BUTTON.changeColor(pygame.mouse.get_pos())
            TURN_OFF_BUTTON.update(screen)
            TURN_ON_BUTTON.reverse()
        else:
            TURN_ON_BUTTON.changeColor(pygame.mouse.get_pos())
            TURN_ON_BUTTON.update(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if BACK_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    slider.hide()
                    output.hide()
                    menu()
                if TURN_OFF_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    music_check = False

                    pygame.mixer.music.pause()
                if TURN_ON_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    music_check = True
                    pygame.mixer.music.unpause()
        output.setText(f'Громкость музыки: {slider.getValue()}%')
        pygame.mixer.music.set_volume(slider.getValue() / 100)
        pygame_widgets.update(pygame.event.get())
        pygame.display.update()


def table():
    connection = sqlite3.connect('my_database.db')
    cursor = connection.cursor()
    cursor.execute(f'SELECT * FROM Users')
    users = cursor.fetchall()
    best_player = []
    if len(users) > 5:
        for i in range(5):
            USER_NAME_TEXT = get_font(50).render(f'{i + 1}.{users[i][1]}', True, 'White')
            USER_NAME_RECT = USER_NAME_TEXT.get_rect(center=(250, 150 + 50 * (i + 1)))
            USER_SCORE_TEXT = get_font(50).render(f'{users[i][2]}', True, 'White')
            USER_SCORE_RECT = USER_NAME_TEXT.get_rect(center=(600, 150 + 50 * (i + 1)))
            best_player.append([USER_NAME_TEXT, USER_NAME_RECT, USER_SCORE_TEXT, USER_SCORE_RECT])
    else:
        for i in range(len(users)):
            USER_NAME_TEXT = get_font(50).render(f'{i + 1}.{users[i][1]}', True, 'White')
            USER_NAME_RECT = USER_NAME_TEXT.get_rect(center=(250, 150 + 70 * (i + 1)))
            USER_SCORE_TEXT = get_font(50).render(f'{users[i][2]}', True, 'White')
            USER_SCORE_RECT = USER_NAME_TEXT.get_rect(center=(600, 150 + 70 * (i + 1)))
            best_player.append([USER_NAME_TEXT, USER_NAME_RECT, USER_SCORE_TEXT, USER_SCORE_RECT])
    while True:
        pygame.display.set_caption('Таблица лидеров')
        screen.fill((0, 0, 0))
        TABLE_TEXT = get_font(100).render('Лучшие игроки', True, 'White')
        TABLE_RECT = TABLE_TEXT.get_rect(center=(400, 50))
        screen.blit(TABLE_TEXT, TABLE_RECT)
        USER_TEXT = get_font(75).render('Имя:', True, 'White')
        USER_RECT = USER_TEXT.get_rect(center=(250, 150))
        screen.blit(USER_TEXT, USER_RECT)
        SCORE_TEXT = get_font(75).render('Счёт:', True, 'White')
        SCORE_RECT = SCORE_TEXT.get_rect(center=(600, 150))
        screen.blit(SCORE_TEXT, SCORE_RECT)
        BACK_BUTTON = Button(image=None, pos=(400, 550), text_input='НАЗАД', font=get_font(75), base_color='White',
                             hovering_color='Green')
        BACK_BUTTON.changeColor(pygame.mouse.get_pos())
        BACK_BUTTON.update(screen)
        for i in range(len(best_player)):
            screen.blit(best_player[i][0], best_player[i][1])
            screen.blit(best_player[i][2], best_player[i][3])
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if BACK_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    menu()
        pygame.display.update()


intro()
