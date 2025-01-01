import pygame
from pygame.locals import *
from random import randint
import numpy as np

pygame.init()
FPS = 60
screen_width = 800
screen_height = 600
display_surface = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Graphs")
clock = pygame.time.Clock()

BLACK = (0, 0, 0)

NODE_COLOR = np.array((0, 153, 76))
NODE_PATH_COLOR = np.array((13, 212, 212))

node_radius = 30


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
    def __init__(self, position: Vector, destinations=[]):
        self.position = position
        self.destinations = destinations.copy()
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
    if a.position.get_tuple() == b.position.get_tuple():
        return
    width = int(node_radius * 0.3)
    width /= scale
    width = int(width)
    ta = (a.position - camera_center) / scale + camera_center
    tb = (b.position - camera_center) / scale + camera_center
    pygame.draw.line(surface, (int(node_color[0] * 0.55), int(node_color[1] * 0.55), int(node_color[2] * 0.55)),
                     ta.get_tuple(), tb.get_tuple(), width)
    pygame.draw.circle(surface, (int(node_color[0] * 0.55), int(node_color[1] * 0.55), int(node_color[2] * 0.55)),
                       ta.get_tuple(), width / 2)
    pygame.draw.circle(surface, (int(node_color[0] * 0.55), int(node_color[1] * 0.55), int(node_color[2] * 0.55)),
                       tb.get_tuple(), width / 2)


is_grabing = False
is_displacing = False
is_connecting = False
shift = False
alt = False
displacement_start = Vector(0, 0)
grabed = Node(Vector(-10e8, -10e8))
paused = False
connecting_from = None  # Node(Vector(-10e8, -10e8))

Objects = []
path = []
camera_pos = Vector(0, 0)
camera_size = Vector(800, 600)
camera_center = camera_pos + camera_size / 2
scale = 1

running = True
while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = get_mouse_pos()

            for obj in Objects:
                if (mouse_pos - obj.position).get_length() < node_radius:
                    if shift:
                        obj.destinations.clear()
                        for o in Objects:
                            if obj in o.destinations:
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

        if event.type == KEYDOWN and event.mod & pygame.KMOD_LSHIFT:
            shift = True
        if event.type == KEYUP and event.key == pygame.K_LSHIFT:
            shift = False

        if event.type == KEYDOWN and event.mod & pygame.KMOD_LALT:
            alt = True
        if event.type == KEYUP and event.key == pygame.K_LALT:
            alt = False

        if event.type == MOUSEBUTTONDOWN and event.button == 2:
            mouse_pos = get_mouse_pos()
            displacement_start = None
            for obj in Objects:
                if (mouse_pos - obj.position).get_length() < node_radius:
                    for o in Objects:
                        if obj in o.destinations:
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
                    if obj == connecting_from:
                        a = [Vector(0, -node_radius),
                             Vector(0, node_radius),
                             Vector(-node_radius, 0),
                             Vector(node_radius, 0)]
                        new = Node(a[randint(0, 3)] + mouse_pos)
                        new.destinations.append(obj)
                        obj.destinations.append(new)
                        Objects.append(new)
                        break
                    elif connecting_from != None:
                        connecting_from.destinations.append(obj)
                        obj.destinations.append(connecting_from)
                        connecting_from = None
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

    clock.tick(FPS)
    pygame.display.update()
