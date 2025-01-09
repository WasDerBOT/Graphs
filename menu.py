import pygame
import sys
from button import Button

pygame.init()
size = width, height = 800, 800
screen = pygame.display.set_mode(size)
pygame.mixer.music.load('Tetris.mp3')
pygame.mixer.music.play(-1)


def get_font(size):
    return pygame.font.SysFont('arial', size)


def menu():
    while True:
        pygame.display.set_caption('Меню')
        screen.fill((0, 0, 0))
        MENU_TEXT = get_font(125).render('Меню', True, 'White')
        MENU_RECT = MENU_TEXT.get_rect(center=(400, 150))
        screen.blit(MENU_TEXT, MENU_RECT)
        PLAY_BUTTON = Button(image=None, pos=(400, 300), text_input='ИГРАТЬ', font=get_font(75), base_color='White',
                             hovering_color='Green')
        OPTIONS_BUTTON = Button(image=None, pos=(400, 400), text_input='НАСТРОЙКИ', font=get_font(75),
                                base_color='White', hovering_color='Green')
        TABLE_BUTTON = Button(image=None, pos=(400, 500), text_input='ТАБЛИЦА ЛИДЕРОВ', font=get_font(75),
                              base_color='White', hovering_color='Green')
        QUIT_BUTTON = Button(image=None, pos=(400, 600), text_input='ВЫХОД', font=get_font(75), base_color='White',
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
    pass


def options():
    music_check = True

    while True:
        pygame.display.set_caption('Настройки')
        screen.fill((0, 0, 0))
        OPTIONS_TEXT = get_font(125).render('Настройки', True, 'White')
        OPTIONS_RECT = OPTIONS_TEXT.get_rect(center=(400, 150))
        screen.blit(OPTIONS_TEXT, OPTIONS_RECT)

        BACK_BUTTON = Button(image=None, pos=(400, 600), text_input='НАЗАД', font=get_font(75), base_color='White',
                                 hovering_color='Green')
        TURN_ON_BUTTON = Button(image=None, pos=(400, 350), text_input='ВКЛЮЧИТЬ МУЗЫКУ', font=get_font(75),
                                base_color='White', hovering_color='Green')
        TURN_OFF_BUTTON = Button(image=None, pos=(400, 350), text_input='ВЫКЛЮЧИТЬ МУЗЫКУ', font=get_font(75),
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
                    menu()
                if TURN_OFF_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    music_check = False

                    pygame.mixer.music.pause()
                if TURN_ON_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    music_check = True
                    pygame.mixer.music.unpause()
        pygame.display.update()


def table():
    pass


menu()
