# i tried making multitool :/
# dont think i ever end it
from time import sleep

sleep(1)
controls = False

firstl = True



if controls == False:
    try:
        import keyboard
        keyboard.add_hotkey('a', print('Работает'))
        keyboard.unhook_all_hotkeys()
    except Exception as e:
        print(f'Ошибка импорта Keyboard! {e}, возрат к упрощенному управлению!')
        controls = True
controls = True
# * Краденый код чтобы ты не 
# * устанавливал лишниюю библиотеку

# * Я хз как он работает, я просто
# * вставлял переменные из аддона
def colored(
    text: object,
    color: str | tuple[int, int, int] | None = None):
    result = str(text)
    RESET = "\033[0m"
    COLORS: dict[str, int] = {
        "black": 30,
        "grey": 30,  # Actually black but kept for backwards compatibility
        "red": 31,
        "green": 32,
        "yellow": 33,
        "blue": 34,
        "magenta": 35,
        "cyan": 36,
        "light_grey": 37,
        "dark_grey": 90,
        "light_red": 91,
        "light_green": 92,
        "light_yellow": 93,
        "light_blue": 94,
        "light_magenta": 95,
        "light_cyan": 96,
        "white": 97,
    }
    rgb_fore_fmt_str = "\033[38;2;%d;%d;%dm%s"
    fmt_str = "\033[%dm%s"
    if color is not None:
        if isinstance(color, str):
            result = fmt_str % (COLORS[color], result)
        elif isinstance(color, tuple):
           result = rgb_fore_fmt_str % (color[0], color[1], color[2], result)
    result += RESET
    return result

def keyboardUpdate(upLim, dnLim):
    global controls
    global firstl
    if firstl == True:
        point = 1
        firstl = False
    
    
    if controls == True:
        n = int(input())
        if n > (upLim-1) and n < (dnLim+1):
            point = n
        else:
            point = point
    print(point)
    return point


def menu():
    while True:
        cursor = keyboardUpdate(1, 4)
        print(f'Сейчас курсор {cursor}')
menu()