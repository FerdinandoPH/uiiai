import os, pygame, random
import numpy as np
def convertir_a_bgra(superficie):
    """Convierte una superficie de RGBA a BGRA usando NumPy."""
    raw_data = pygame.image.tostring(superficie, "RGBA", False)
    array = np.frombuffer(raw_data, dtype=np.uint8).reshape((superficie.get_height(), superficie.get_width(), 4))
    array = array.copy()
    array[:, :, [0, 2]] = array[:, :, [2, 0]]  # Intercambiar R y B
    return pygame.image.fromstring(array.tobytes(), superficie.get_size(), "RGBA")
def pre_multiplicar_alpha(superficie, w, h):
    """Pre-multiplica los valores RGB por el canal alfa usando NumPy."""
    # Obtener los datos de la superficie como un array de NumPy
    raw_data = pygame.image.tostring(superficie, "RGBA", False)
    array = np.frombuffer(raw_data, dtype=np.uint8).reshape((h, w, 4))

    # Hacer una copia para permitir modificaciones
    array = array.copy()

    # Pre-multiplicar RGB por el canal alfa
    alpha = array[:, :, 3:4] / 255.0  # Normalizar el alfa
    array[:, :, :3] = (array[:, :, :3] * alpha).astype(np.uint8)

    # Actualizar la superficie con los datos modificados
    superficie_pixels = pygame.image.fromstring(array.tobytes(), (w, h), "RGBA")
    return superficie_pixels
class Gato(pygame.sprite.Sprite):
    def __init__(self, w, h):
        super().__init__()
        
        gato_imgs = [os.path.join(os.path.dirname(os.path.realpath(__file__)), "Recursos", f'uiiai{i}.png') for i in range(0, 236)]
        self.animations={
            # 'idle':[pygame.image.load(gato_imgs[0])],
            # 'rapido':[pygame.image.load(gato_imgs[i]) for i in range(1, 54)],
            # 'lento':[pygame.image.load(gato_imgs[i]) for i in range(54, 115)],
            # 'alterno':[pygame.image.load(gato_imgs[i]) for i in range(115, 236)]
            'idle':[convertir_a_bgra(pygame.image.load(gato_imgs[0]))],
            'rapido':[convertir_a_bgra(pygame.image.load(gato_imgs[i])) for i in range(1, 54)],
            'lento':[convertir_a_bgra(pygame.image.load(gato_imgs[i])) for i in range(54, 115)],
            'alterno':[convertir_a_bgra(pygame.image.load(gato_imgs[i])) for i in range(115, 236)]
        }
        self.fxs={
            'rapido':pygame.mixer.Sound(os.path.join(os.path.dirname(os.path.realpath(__file__)), "Recursos", "uiiaiRapido.mp3")),
            'lento':pygame.mixer.Sound(os.path.join(os.path.dirname(os.path.realpath(__file__)), "Recursos", "uiiaiLento.mp3")),
            'alterno':pygame.mixer.Sound(os.path.join(os.path.dirname(os.path.realpath(__file__)), "Recursos", "uiiaiAlterno.mp3"))
        }
        self.current_animation = 'idle'
        self.images = self.animations[self.current_animation]
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        # self.rect = pygame.Rect(self.img_rect.topleft[0]+150, self.img_rect.y, self.img_rect.width-150, self.img_rect.height)
        # self.rect.width-=150
        # recorte_izquierda = 200  # Cantidad de píxeles a recortar por la izquierda
        # self.image = self.image.subsurface((recorte_izquierda, 0, self.img_rect.width - recorte_izquierda, self.img_rect.height))
        #self.rect = self.image.get_rect(topleft=(0, 0))
        self.speed = [10, 10]
        self.transition_to = 'idle'
        self.loop = False
        self.move = False
        self.screen_w = w
        self.screen_h = h
        self.rect.x = random.randint(0, w - self.rect.width)
        self.rect.y = random.randint(0, h - self.rect.height)
        self.last_x = -1
        self.last_y = -1
        self.alpha = 255
        self.generating_alphas = True
        self.render_as_alpha = True
        self.alpha_imgs = self.images
        self.alpha_img = self.alpha_imgs[0]
        #self.generate_alphas()
        #self.tapaGatos = TapaGatos(self)
    def generate_alphas(self):
        if self.rect.x != self.last_x or self.rect.y != self.last_y:
            self.generating_alphas = True
            self.alpha_imgs = []
            alphas= []
            fondo_base = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
            sprite_base = self.images[0]
            for i in range(0, 256):
                #print(i)
                copia_sprite = sprite_base.copy()
                copia_fondo = fondo_base.copy()
                copia_sprite.set_alpha(i)
                copia_fondo.fill((0, 0, 0, 0))
                copia_fondo.blit(copia_sprite, (self.rect.x, self.rect.y))
                copia_fondo = pre_multiplicar_alpha(copia_fondo, self.screen_w, self.screen_h)
                alphas.append(copia_fondo)
                #alphas.append(pre_multiplicar_alpha(copia_sprite, self.rect.width, self.rect.height))
            self.last_x = self.rect.x
            self.last_y = self.rect.y
            self.alpha_imgs = alphas
            self.alpha_img = self.alpha_imgs[self.alpha]
        self.generating_alphas = False
    def set_pos(self, x, y):
        self.rect.x = x
        self.rect.y = y
        self.generate_alphas()
    def set_pos_random(self):
        self.set_pos(random.randint(0, self.screen_w - self.rect.width), random.randint(0, self.screen_h - self.rect.height))
    def update(self):
        #self.tapaGatos.update()
        self.index += 1
        if self.index >= len(self.images):
            self.set_animation(self.current_animation if self.loop else self.transition_to)
        self.image = self.images[self.index]
        if self.current_animation != 'idle' and self.move:
            self.rect.move_ip(self.speed)
            if self.rect.left < 0 or self.rect.right > self.screen_w:
                self.speed[0] = -self.speed[0]
            if self.rect.top < 0 or self.rect.bottom > self.screen_h:
                self.speed[1] = -self.speed[1]
    def set_animation(self, animation_name):
        if animation_name in self.animations:
            self.current_animation = animation_name
            self.images = self.animations[self.current_animation]
            self.index = 0
            self.play_fx()
    def play_fx(self, fx=None):
        if fx is None: fx = self.current_animation
        pygame.mixer.stop()
        if fx != 'idle':
            self.fxs[fx].play()
    def set_alpha(self, new_alpha):
        if self.alpha != new_alpha:
            self.alpha = new_alpha
            #print(f"Alpha: {self.alpha}")
            self.alpha_img = self.alpha_imgs[self.alpha]
    def get_alpha(self):
        return self.alpha
# class TapaGatos(pygame.sprite.Sprite):
#     def __init__(self, gato):
#         super().__init__()
#         self.image = pygame.image.load(os.path.join(os.path.dirname(os.path.realpath(__file__)), "Recursos", "uiiaiBlank.png"))
#         self.rect = self.image.get_rect()
#         self.gato = gato
#         self.rect.topleft = self.gato.rect.topleft
#         self.alpha = self.gato.alpha
#         self.image.set_alpha(self.alpha)
#     def update(self):
#         self.rect.x = self.gato.rect.x
#         self.rect.y = self.gato.rect.y
#     def set_alpha(self, new_alpha):
#         self.alpha = new_alpha
#         self.image.set_alpha(255-self.alpha)
#     def get_alpha(self):
#         return self.alpha