import pyautogui
import keyboard
import cv2
import numpy as np
import itertools
from PIL import ImageGrab
from solver.mines import Solver, Information
import random


def recognize_in_image(img, small_img, threshold=0.85):
    res = cv2.matchTemplate(img, small_img, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res >= threshold)
    return list(zip(*loc[::-1]))


box_image_names = ['images/minesweeper0.png', 'images/minesweeper1.png', 'images/minesweeper2.png',
                   'images/minesweeper3.png', 'images/minesweeper4.png', 'images/minesweeper5.png',
                   'images/minesweeper6.png']
box_images = [cv2.imread(name, 0) for name in box_image_names]

def get_best_box_for_image(color_img, base):
    base_x, base_y = base

    img = cv2.cvtColor(color_img, cv2.COLOR_BGR2GRAY)

    recognized_points = [recognize_in_image(img, image) for image in box_images]
    tagged_points = list(
        itertools.chain(
            *[[(point[0], point[1], i) for point in points] for i, points in enumerate(recognized_points)]))

    minesweeper_points = {(round(x / 24), round(y / 24)): n for x, y, n in tagged_points}

    for (x, y), v in minesweeper_points.items():
        cv2.rectangle(color_img, (x * 24, y * 24), (x * 24 + 20, y * 24 + 20), (0, 255, v * 40), 0)
        cv2.putText(color_img, str(v), (x * 24 + 4, y * 24 + 12), cv2.FONT_ITALIC, 0.5, (0, 255, 255))

    spaces = set((x, y) for x in range(30) for y in range(16))
    solver = Solver(spaces)

    outer_spaces = set((x, y) for x in range(-1, 31) for y in range(-1, 17))
    info = Information(frozenset(outer_spaces.difference(spaces)), 0)
    solver.add_information(info)

    minesweeper_points_keys = minesweeper_points.keys()

    # total mines
    info = Information(frozenset(spaces), 99)
    solver.add_information(info)

    for key, value in minesweeper_points.items():
        px, py = key
        local_spaces = set((px + x, py + y) for x in range(-1, 2) for y in range(-1, 2))
        info = Information(frozenset(local_spaces.difference(minesweeper_points_keys)), value)
        solver.add_information(info)

    solver.solve()

    good_spaces = [e for e in solver.solved_spaces.items()
                   if e[1] == 0
                   and e[0] not in minesweeper_points_keys
                   and 0 <= e[0][0] < 30 and 0 <= e[0][1] < 16]

    if len(good_spaces) == 0:
        print("GOGOGO!!!")
        probabilities, total = solver.get_probabilities()

        print(probabilities)
        for (x, y), v in probabilities.items():
            cv2.rectangle(color_img, (x * 24, y * 24), (x * 24 + 20, y * 24 + 20), (255, 0, 255), 0)
            cv2.putText(color_img, "{:.2f}".format(v/total), (x * 24 + 4, y * 24 + 12), cv2.FONT_ITALIC, 0.3, (255, 0, 255))

        filtered_probabilites = list(
            filter(lambda e: 0 <= e[0][0] < 30 and 0 <= e[0][1] < 16 and e[0] not in minesweeper_points_keys,
                   probabilities.items()))
        best_choice, probability = min(filtered_probabilites, key=lambda x: x[1])
        print(best_choice, probability/total)
        good_spaces.append(((best_choice[0], best_choice[1]), 0))

    good_coordinates = [(x * 24 + base_x, y * 24 + base_y, v) for (x, y), v in good_spaces]

    if keyboard.is_pressed('shift'):
        cv2.imshow('image', color_img)
        cv2.waitKey(0)

    return good_coordinates


pyautogui.PAUSE = 0.01

while True:
    while not keyboard.is_pressed('c'):
        pass

    try:
        corner_points = recognize_in_image(np.array(ImageGrab.grab()),
                                           cv2.cvtColor(np.array(cv2.imread('images/corner2.png', 0)), cv2.COLOR_BGR2RGB))
        corner_point = min(corner_points, key=lambda x: x[0] + x[1])
        # base_point = (corner_point[0] + 10, corner_point[1] + 74)
        base_point = (corner_point[0] + 10, corner_point[1] + 72)
    except Exception as e:
        print(e)

    while not keyboard.is_pressed('ctrl'):
        # try:
        pyautogui.moveTo(1, 1)
        screenshot = ImageGrab.grab(bbox=(base_point[0], base_point[1], base_point[0] + 800, base_point[1] + 600))
        main_img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2RGB)

        # cv2.imshow('t', main_img)
        # cv2.waitKey(0)

        try:
            results = get_best_box_for_image(main_img, (base_point[0], base_point[1]))
            random.shuffle(results)
            for cx, cy, v in results:
                if v == 0:
                    pyautogui.moveTo(cx + 12, cy + 12)
                    pyautogui.click()
                # ahk.mouse_move(0, 0, speed=10, relative=False)
        except Exception as e:
            print(e)

