from enum import Enum
import time
import pygame
import win32con
import ctypes
from ctypes import wintypes
import threading
from Gato import Gato
from Config_public import Config
import random
import requests, getpass, os
from requests.auth import HTTPBasicAuth

log_file = 'C:\\Users\\Public\\Documents\\uiiai\\log.txt'
headers = {'Content-Type': 'text/plain; charset=utf-8'}
config = Config()
config.cargar()
#Setup
pygame.init()
global w, h, screen, hwnd, user32, gdi32, UpdateLayeredWindow
pygame.mixer.init()
info = pygame.display.Info()
w = info.current_w
h = info.current_h

gato = Gato(w,h)
def crear_pantalla():
    global screen, hwnd, user32, gdi32, UpdateLayeredWindow
    screen = pygame.display.set_mode((w, h), pygame.NOFRAME)  # For borderless, use pygame.NOFRAME
    hwnd = pygame.display.get_wm_info()["window"]

    #Setup Window
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
    GWL_EXSTYLE = -20
    WS_EX_LAYERED = 0x00080000
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, user32.GetWindowLongW(hwnd, GWL_EXSTYLE) | WS_EX_LAYERED)
    UpdateLayeredWindow = user32.UpdateLayeredWindow
    UpdateLayeredWindow.argtypes = [
        wintypes.HWND, wintypes.HDC, ctypes.POINTER(POINT), ctypes.POINTER(SIZE),
        wintypes.HDC, ctypes.POINTER(POINT), wintypes.COLORREF,
        ctypes.POINTER(BLENDFUNCTION), wintypes.DWORD
    ]
    # Remove the window from the taskbar
    ctypes.windll.user32.SetWindowLongW(hwnd, -20, ctypes.windll.user32.GetWindowLongW(hwnd, -20) | 0x00000080)
class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

class SIZE(ctypes.Structure):
    _fields_ = [("cx", wintypes.LONG), ("cy", wintypes.LONG)]

class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [("BlendOp", ctypes.c_byte),
                ("BlendFlags", ctypes.c_byte),
                ("SourceConstantAlpha", ctypes.c_byte),
                ("AlphaFormat", ctypes.c_byte)]


# Thread time
render_flag = threading.Event()
backtoyou_create = threading.Event()
backtoyou_destroy = threading.Event()
end_top = threading.Event()
end_question = threading.Event()
end_random = threading.Event()
end_render = threading.Event()
def end_program():
    with hilo_top_lock:
        end_top.set()
    end_question.set()
    end_render.set()
    end_random.set()
def keep_window_on_top(keep_top):
    global hwnd
    user32 = ctypes.WinDLL("user32")
    user32.SetWindowPos.restype = wintypes.HWND
    user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, wintypes.INT, wintypes.INT, wintypes.INT, wintypes.INT, wintypes.UINT]
    while not keep_top.is_set():
        result1 = user32.SetWindowPos(hwnd, -1, 600, 300, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        # if result1 == 0:
        #     error_code = ctypes.GetLastError()
        #     print(f"Error: SetWindowPos failed with error nº {error_code}")
        # else:
        #     print(f"SetWindowPos worked: {result1}")
        pygame.time.wait(500)  # Espera 0.5 segundos antes de volver a poner la ventana al frente

hilo_top = threading.Thread(target=keep_window_on_top,args=(end_top,))
hilo_top_lock = threading.Lock()
#hilo_top.start()

gato.set_alpha(0)
gato_lock = threading.Lock()
def control(end_question, gato, gato_lock):
    while not end_question.is_set():
        opcion = input("1: Rapido\n2: Lento\n3: Alterno\n4: Parar en seco\n5: Mover\n6: Loop\n7: Salir\nTu respuesta: ")
        with gato_lock:
            if opcion == '1':
                gato.set_animation('rapido')
            elif opcion == '2':
                gato.set_animation('lento')
            elif opcion == '3':
                gato.set_animation('alterno')
            elif opcion == '4':
                gato.set_animation('idle')
            elif opcion == '5':
                gato.move = not gato.move
                print("Movimiento activado" if gato.move else "Movimiento desactivado")
            elif opcion == '6':
                gato.loop = not gato.loop
                print("Loop activado" if gato.loop else "Loop desactivado")
            elif opcion == '7':
                end_program()
            else:
                print("Opcion no valida")
# hilo_control = threading.Thread(target=control,args=(end_question, gato, gato_lock,))
# hilo_control.start()

def transicion_alfa(gato, gato_lock, alfa_final, tiempo_transicion):
    alfa_original = gato.get_alpha()
    fracciones = 50
    fin_transicion = False
    direccion = 1 if alfa_final > alfa_original else -1 if alfa_final < alfa_original else 0
    if direccion == 0:
        return
    while not fin_transicion:
        with gato_lock:
            gato.set_alpha(min(max(0,round(gato.get_alpha() + abs(alfa_final-alfa_original)*direccion/fracciones)),255))
            if (direccion == 1 and gato.get_alpha() >= alfa_final) or (direccion == -1 and gato.get_alpha() <= alfa_final):
                gato.set_alpha(alfa_final)
                fin_transicion = True
        pygame.time.wait(int(tiempo_transicion*1000/fracciones))
def esperar_a_idle(gato, gato_lock):
    while True:
        with gato_lock:
            if gato.current_animation == 'idle':
                break
        pygame.time.wait(100)
def activar_generacion_alfas(gato, gato_lock):
    with gato_lock:
        gato.generating_alphas = True
    gato.generate_alphas()
def random_decider(end_random, gato: Gato, gato_lock, end_top, hilo_top, hilo_top_lock):
    class Estado_Gato(Enum):
        OCULTO = 0
        FANTASMOSO = 1
        VISIBILIZANDO = 2
        VISIBLE = 3
        MOVIMIENTO = 4
    estado = Estado_Gato.OCULTO
    prob_retorno = config.probabilidades['retorno']
    prob_tanteo = config.probabilidades['tanteo']
    prob_frenesi = config.probabilidades['frenesi']
    prob_fantasmoso = config.probabilidades['fantasmoso']
    espera_a_alfas = False
    while not end_random.is_set():
        #print(estado)
        if estado == Estado_Gato.OCULTO:
            prob_retorno = config.probabilidades['retorno']
            prob_tanteo = config.probabilidades['tanteo']
            prob_frenesi = config.probabilidades['frenesi']
            with hilo_top_lock:
                end_top.set()
            with gato_lock:
                gato.set_animation('idle')
                gato.render_as_alpha = True
            transicion_alfa(gato, gato_lock, 0, random.uniform(config.duraciones['quitar'][0], config.duraciones['quitar'][1]))
            with gato_lock:
                if config.probabilidades["cambiar_pos"]>=random.randint(1,100):
                    gato.rect.x = random.randint(0, w - gato.rect.width)
                    gato.rect.y = random.randint(0, h - gato.rect.height)
                    gato.generating_alphas = True
                    gato.alpha_imgs = []
            
            render_flag.clear()
            #pygame.display.quit()
            tiempo_dormir = random.randint(config.esperas['oculto'][0], config.esperas['oculto'][1])
            time.sleep(tiempo_dormir)
            config.cargar()
            #print(config.__dict__)
            if config.__dict__["activo"]:
                gato.generate_alphas()
                estado = Estado_Gato.FANTASMOSO if prob_fantasmoso >= random.randint(1,100) else Estado_Gato.VISIBLE
        else:
            if not render_flag.is_set():
                #crear_pantalla()
                backtoyou_create.clear()
                render_flag.set()
                backtoyou_create.wait()
                if not hilo_top.is_alive():
                    with hilo_top_lock:
                        end_top.clear()
                        hilo_top = threading.Thread(target=keep_window_on_top,args=(end_top,), daemon=True)
                        hilo_top.start()
                
                

            if estado == Estado_Gato.FANTASMOSO:
                with gato_lock:
                    gato.set_animation('idle')
                transicion_alfa(gato, gato_lock, random.randint(80,180), random.uniform(config.duraciones['mostrarFantasma'][0], config.duraciones['mostrarFantasma'][1]))
                time.sleep(random.randint(config.esperas['fantasma'][0], config.esperas['fantasma'][1]))
                prob_fantasmoso /= 1.5
                estado = Estado_Gato.OCULTO
            elif estado == Estado_Gato.VISIBLE:
                with gato_lock:
                    gato.set_animation('idle')
                if not espera_a_alfas:
                    transicion_alfa(gato, gato_lock, 255, random.uniform(config.duraciones['mostrarVisible'][0], config.duraciones['mostrarVisible'][1]))
                else:
                    with gato_lock:
                        if not gato.generating_alphas:
                            espera_a_alfas = False
                time.sleep(random.randint(config.esperas['visible'][0], config.esperas['visible'][1])*(1 if not espera_a_alfas else 2))
                if prob_retorno >= random.randint(1,100) and not espera_a_alfas:
                    estado = Estado_Gato.OCULTO
                    prob_fantasmoso = max(50, prob_fantasmoso)
                else:
                    estado = Estado_Gato.MOVIMIENTO
                    prob_fantasmoso = config.probabilidades['fantasmoso']
            elif estado == Estado_Gato.MOVIMIENTO:
                with gato_lock:
                    gato.render_as_alpha = False
                if prob_tanteo >= random.randint(1,100):
                    with gato_lock:
                        gato.set_animation('rapido')
                    pygame.time.wait(int(0.15*1000))
                    with gato_lock:
                        gato.set_animation('idle')
                    prob_tanteo /= 2
                    estado = Estado_Gato.VISIBLE
                else:
                    prob_tanteo = 0
                    if prob_frenesi >= random.randint(1,100): #quitado temporalmente
                        prob_frenesi = 0
                        with gato_lock:
                            gato.move = True
                            gato.loop = True
                            gato.set_animation('rapido')
                        time.sleep(random.randint(config.esperas['frenesi'][0], config.esperas['frenesi'][1]))
                        with gato_lock:
                            gato.loop = False
                        esperar_a_idle(gato, gato_lock)
                        with gato_lock:
                            gato.move = False
                            gato.set_animation('idle')
                        prob_retorno *= 1.5
                        espera_a_alfas = True
                        threading.Thread(target=activar_generacion_alfas, args=(gato, gato_lock,), daemon=True).start()
                    else:
                        if not espera_a_alfas:
                            prob_frenesi += 10
                        opcion = random.choice(['rapido', 'lento', 'alterno'])
                        with gato_lock:
                            gato.set_animation(opcion)
                        esperar_a_idle(gato, gato_lock)
                prob_retorno *= 2
                estado = Estado_Gato.VISIBLE
hilo_random = threading.Thread(target=random_decider,args=(end_random, gato, gato_lock, end_top, hilo_top, hilo_top_lock,), daemon=True)
hilo_random.start()
def custom_layered_render(superficie):
    global w, h, hwnd, user32, gdi32, UpdateLayeredWindow
    """Actualiza la ventana con transparencias avanzadas."""
    hdc_screen = user32.GetDC(0)
    hdc_window = gdi32.CreateCompatibleDC(hdc_screen)

    bitmap = gdi32.CreateCompatibleBitmap(hdc_screen, w, h)
    gdi32.SelectObject(hdc_window, bitmap)

    pixel_data = pygame.image.tostring(superficie, "RGBA", False)
    ctypes.windll.gdi32.SetBitmapBits(bitmap, len(pixel_data), pixel_data)

    src_point = POINT(0, 0)
    size = SIZE(w, h)
    blend = BLENDFUNCTION(0, 0, 255, 1)  # Usa el canal alpha
    dest_point = POINT(0, 0)

    UpdateLayeredWindow(hwnd, hdc_screen, ctypes.byref(dest_point), ctypes.byref(size),
                        hdc_window, ctypes.byref(src_point), 0, ctypes.byref(blend), 2)

    gdi32.DeleteObject(bitmap)
    gdi32.DeleteDC(hdc_window)
    user32.ReleaseDC(0, hdc_screen)
if __name__ == "__main__":
    
    base_surface = pygame.Surface((w, h), pygame.SRCALPHA)
    all_sprites = pygame.sprite.Group()
    with gato_lock:
        all_sprites.add(gato)
    clock = pygame.time.Clock()
    while not end_render.is_set():
        if not render_flag.is_set():
            pygame.display.quit()
            render_flag.wait()
            if not backtoyou_create.is_set():
                crear_pantalla()
                trabajo_retomado = False
                backtoyou_create.set()

        for event in pygame.event.get():
            continue
            if event.type == pygame.QUIT:
                end_program()
                break
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    end_program()
                    break
        base_surface.fill((0,0,0,0))  # Transparent background
        with gato_lock:
            if gato.render_as_alpha:
                if not gato.generating_alphas:
                    custom_layered_render(gato.alpha_img)
                else:
                    custom_layered_render(base_surface)
            else:
                all_sprites.update()
                all_sprites.draw(base_surface)
                custom_layered_render(base_surface)
            # capas_gatos.update()
            # capas_gatos.draw(screen)
            #pygame.draw.rect(screen, dark_red, gato.rect, 2)  # El último argumento es el grosor del borde
        clock.tick(30)

pygame.quit()