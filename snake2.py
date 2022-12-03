import math
import time
import msvcrt
import ctypes
import random

from ctypes import wintypes


   #######  ##     #     ##     #    ##  #######
   #        # #    #    #  #    #   ##   #
   #        #  #   #   #    #   #  ##    #
   #######  #   #  #  ########  ####     ##### 
         #  #    # #  #      #  #  ##    #
         #  #     ##  #      #  #   ##   #
   #######  #      #  #      #  #    ##  #######

DUMP = False

class snakegame:
    field_width  = None
    field_height = None

    field_state = []

    snake_length = 0
    snake_head = [0, 0]

    head_dir = 10

    game_lost = False
    snakebody = []

    defaults = {}

    map = None

    def initialize(settings):
      
        try:
            for prop in settings:
                if not callable(getattr(snakegame, prop)):
                    setattr(snakegame, prop, settings[prop])
                else:
                    raise AttributeError
        except AttributeError as e:
            e.args = ("Invalid game setting '{}' does not exist.".format(prop),)
            raise

        snakegame.snakebody = [list(snakegame.snake_head)] * snakegame.snake_length
        snakegame.defaults = settings

        snakegame.loadmap()

        snakegame.snake_head = list(snakegame.snake_head)

    def reset():
        snakegame.initialize(snakegame.defaults)
        snakegame.game_lost = False

    def loadmap(file=None):
        if file:
            if not hasattr(file, 'read'):
                file = open(file, 'r')
            snakegame.map = [int(line, base=2) for line in file]
        else:
            snakegame.map = snakegame.map or [0] * snakegame.field_height

        snakegame.field_state = list(snakegame.map)

        if len(snakegame.field_state) != snakegame.field_height:
            raise Exception("field map is invalid")



WIN32  = ctypes.WinDLL("kernel32")
stdout = WIN32.GetStdHandle(-11)    


def HideCursor():
    class _CONSOLE_CURSOR_INFO(ctypes.Structure):
        _fields_ = [('dwSize', wintypes.DWORD),
                    ('bVisible', ctypes.c_bool)]

    hidden_cursor = _CONSOLE_CURSOR_INFO()
    hidden_cursor.bVisible = False

    WIN32.SetConsoleCursorInfo(stdout, ctypes.byref(hidden_cursor))

HideCursor()


COORD = wintypes._COORD

box_tl = "\u250C"
box_tr = "\u2510"
box_bl = "\u2514"
box_br = "\u2518"

vborder   = "\u2500"
hborder   = "\u2502"

# Helper functions
def move_cursor(pos=(0,0)):
    WIN32.SetConsoleCursorPosition(stdout, COORD(*pos))

def change_dir(dir):
    
    if (snakegame.head_dir + dir) == 10: return
    snakegame.head_dir = dir

def move_snake():
    
    inc   = 1
    index = 0
    wrap  = snakegame.field_width
    dir = snakegame.head_dir

    if dir in [4, 8]:
        
        inc = -1

    if dir in [2, 8]:
      
        index = 1
        wrap = snakegame.field_height

    snakegame.snake_head[index] += inc
    snakegame.snake_head[index] %= wrap

    if has_obstacle(snakegame.snake_head):
        snakegame.game_lost = True 

    snakegame.snakebody.insert(0, list(snakegame.snake_head))
    tail = snakegame.snakebody.pop()

    tx, ty = tail
    snakegame.field_state[ty] -= snakegame.field_state[ty] & (1 << tx)

    hx, hy = snakegame.snake_head
    snakegame.field_state[hy] |= (1 << hx)

def has_obstacle(pos):
    x, y = pos
    return bool(snakegame.field_state[y] & (1 << x))

def draw_field():
    w = snakegame.field_width
    h = snakegame.field_height

   
    move_cursor()

    print(box_tl, vborder * w, box_tr, sep='')

    for i in range(h):
        scanline  = snakegame.field_state[i]
        screen_line = [" "] * w

        for pix in range(w):
            if scanline & 1: screen_line[pix] = "#"
            scanline >>= 1

        screen_line = "".join(screen_line)

        print(hborder, end='')
        print(screen_line, end='')
        print(hborder)

    print(box_bl, vborder * w, box_br, sep='')
    if DUMP:
        for i in snakegame.field_state:
            x = bin(i)[2:]
            print("0b","0"*(w-len(x)),x, sep='')

def transition():
    w = snakegame.field_width
    h = snakegame.field_height

    
    move_cursor()

    width_band = 10

    inner_offset = [-i for i in range(h//2)]
    inner_offset += [(i - h) for i in range(h//2, h)]

    outer_offset = [k-width_band  for k in inner_offset]

    last = min(outer_offset)
    pow2 = (1 << w) - 1

    while last < (w//2 + 1):
        for i in range(h):
            in_pos = inner_offset[i]
            out_pos = outer_offset[i]

            r_in = w - in_pos - 1
            r_out = w - out_pos - 1

            gm_st = snakegame.field_state[i]

       
            if in_pos >= 0: gm_st |= 1 << in_pos

    
            if 0 < r_in < w:
                gm_st |= 1 << r_in

            if out_pos >= 0:  
                x = gm_st & ( (1 << (out_pos+1)) - 1 )
                gm_st -= x

            if 0 < r_out < w:
                x = pow2 - ( (1 << (r_out+1)) - 1 )
                gm_st -= (gm_st & x)

            snakegame.field_state[i] = gm_st

            inner_offset[i] += 1
            outer_offset[i] += 1

        last += 1
        draw_field()

        time.sleep(0.01 if not DUMP else 1)

def draw_lostScreen():
    w = snakegame.field_width
    h = snakegame.field_height

    text = ["GAME OVER",
            "Want to try again?",
            "Enter y to continue, any other button to quit"]

    v_offset = (h - len(text)) // 2

    transition()
    move_cursor()

    print(box_tl, vborder * w, box_tr, sep='')

    for i in range(h):
        print(hborder, end='')
        print(" "*w, end='')
        print(hborder)

    print(box_bl, vborder * w, box_br, sep='')

    for i, t in enumerate(text):
        h_offset = (w - len(t)) // 2
        move_cursor([h_offset, i + v_offset])
        print(t)

    move_cursor([w // 2, i + v_offset + 1])
    return input().lower() == 'y'

snakegame.initialize({
    'field_width'   : 75,
    'field_height'  : 20,

    'snake_length'  : 10,
    'head_dir'      :  4,
    'snake_head'    : [75//2, 20//2]
})

try:
    while True:
        while not snakegame.game_lost:
            move_snake()
            draw_field()

            if msvcrt.kbhit():
                dir = msvcrt.getch()
                while msvcrt.kbhit():
                    dir = msvcrt.getch()
                dir = ord(dir)

                if dir == 72 or dir == 56: dir = 8
                elif dir == 80 or dir == 50: dir = 2
                elif dir == 75 or dir == 52: dir = 4
                elif dir == 77 or dir == 54: dir = 6
                else:
                    continue
                change_dir(dir)
            time.sleep(0.03)

        time.sleep(1)
        retry = draw_lostScreen()
        snakegame.reset()

        if not retry:
            break
except Exception as e:
    print(e)
input()