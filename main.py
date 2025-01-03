import pygame
import pygame_widgets
from pygame.locals import *
from random import randint
from pygame_widgets.textbox import TextBox
from pygame_widgets.slider import Slider
import sys
from button import Button

pygame.init()
size = width, height = 800, 600
screen = pygame.display.set_mode(size)
pygame.mixer.music.load('Tetris.mp3')
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)
FPS = 60
screen_width = 800
screen_height = 600
display_surface = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Graphs")

clock = pygame.time.Clock()

current_dist = 10
BLACK = (0, 0, 0)
NODE_SUCCESSFUL_PATH = (0, 153, 76)
NODE_WRONG_PATH = (194, 36, 25)
NODE_COLOR = (125, 125, 125)
NODE_PATH_COLOR = (13, 212, 212)

FONT = pygame.font.Font('Cinematic.otf', size=32)

node_radius = 30

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



textbox = TextBox(display_surface, 255, 100, 300, 100, fontSize=40,
                  borderColour=(255, 255, 255, 125), textColour=(0, 0, 0),
                  radius=10, borderThickness=10, placeholderText="Введите длину", onSubmit=set_dist)


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
        for dest in self.destinations:
            draw_connection(surface, node_color, self, dest)

    def interact_with(self, other):
        r = other.position - self.position
        direct = r.get_normalized()
        length = r.get_length() / (2 * node_radius)
        if other in self.destinations:
            length /= min(max(1, self.distances[self.destinations.index(other)]), 30)**0.25
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
is_grabing = False
is_displacing = False
is_connecting = False
shift = False
alt = False
displacement_start = Vector(0, 0)
grabed = Node(Vector(-10e8, -10e8))
paused = False
connecting_from = None
connecting_to = None

Objects = []
path = []
camera_pos = Vector(0, 0)
camera_size = Vector(800, 600)
camera_center = camera_pos + camera_size / 2
scale = 1


def get_font(size):
    return pygame.font.SysFont('arial', size)


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
                    play()
                if OPTIONS_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    options()

                if TABLE_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    table()
                if QUIT_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    pygame.quit()
                    sys.exit()
        pygame.display.update()


def play():
    running = True

    while running:
        global is_displacing, is_inputting, inputed, paused, is_grabing, connecting_from, grabed, shift, alt, scale
        events = pygame.event.get()
        pygame_widgets.update(events)
        for event in events:
            if event.type == QUIT:
                running = False
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
                            if obj in path:
                                path.remove(obj)
                            else:
                                path.append(obj)
                        else:
                            is_grabing = True
                            grabed = obj

                        break

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
                        if obj in path:
                            path.remove(obj)
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
                        connecting_from = obj
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

            if event.type == MOUSEBUTTONUP and grabed:
                grabed = None
                is_grabing = False
            if event.type == KEYDOWN and event.key == pygame.K_q:
                paused = not paused
            if event.type == KEYDOWN and event.key == pygame.K_c:
                for obj in Objects:
                    obj.destinations.clear()
                    obj.distances.clear()
                path.clear()
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

        if is_grabing:
            mouse_pos = get_mouse_pos()

            grabed.velocity = mouse_pos - grabed.position
            if paused:
                grabed.position = mouse_pos

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
        for obj in path:
            obj.draw(display_surface, NODE_PATH_COLOR, node_radius)

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

        clock.tick(FPS)
        pygame.display.update()


def options():
    global music_check, check_slider, output, slider
    if check_slider:
        slider = Slider(screen, 100, 150, 600, 40, min=0, max=100, step=1, colour=(255, 255, 255),
                        handleColour=(122, 122, 122))
        output = TextBox(screen, 0, 250, 200, 75, fontSize=70, textColour=(255, 255, 255), colour=(0, 0, 0))
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
                    textbox.show()
                    menu()
                if TURN_OFF_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    music_check = False

                    pygame.mixer.music.pause()
                if TURN_ON_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    music_check = True
                    pygame.mixer.music.unpause()
        output.setText(f'Громкость музыки: {slider.getValue()}%')
        pygame.mixer.music.set_volume(slider.getValue() / 100)
        textbox.hide()
        pygame_widgets.update(pygame.event.get())
        pygame.display.update()


def table():
    pass


menu()
