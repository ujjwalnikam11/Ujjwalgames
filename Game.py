import pygame
import random
import os
import sys

# --- RESOURCE PATH LOGIC ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# ================= INITIALIZATION =================
pygame.init()
try: pygame.mixer.init()
except: pass

WIDTH, HEIGHT = 400, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
pygame.display.set_caption("Jungle Nitro Racing - Extreme")

# --- CONFIG & ASSETS ---
STANDARD_SIZE = (45, 90)
LANES = [110, 175, 245] # Teen fixed lanes taaki cars raste mein na fanse

def safe_load(f, size=None):
    path = resource_path(f)
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, size) if size else img
    return None

car_img = safe_load("car.png", STANDARD_SIZE)
road_img = safe_load("jungle_road.png", (WIDTH, HEIGHT))
logo_img = safe_load("icon.jpeg", (120, 120))

enemy_files = ["car_yellow.png", "car_blue_top.png", "car_red.png", "enemy_car.png"]
enemy_images = [img for f in enemy_files if (img := safe_load(f, STANDARD_SIZE))]
if not enemy_images: enemy_images.append(car_img)

try:
    crash_sound = pygame.mixer.Sound(resource_path("crash.mp3"))
    nitro_sound = pygame.mixer.Sound(resource_path("nitro_dubstep.mp3"))
    pygame.mixer.music.load(resource_path("jungle_bg.mp3"))
    pygame.mixer.music.play(-1)
except:
    crash_sound = nitro_sound = None

# ================= HELPERS =================
def draw_heart(surface, x, y, size):
    points = [(x, y + size // 4), (x - size // 2, y - size // 2), (x - size, y + size // 4), (x, y + size), (x + size, y + size // 4), (x + size // 2, y - size // 2)]
    pygame.draw.polygon(surface, (255, 0, 0), points)

# ================= ENEMY CLASS =================
class Enemy:
    def __init__(self):
        self.image = random.choice(enemy_images)
        self.rect = self.image.get_rect()
        self.reset()

    def reset(self):
        self.rect.x = random.choice(LANES)
        self.rect.y = random.randint(-900, -100) # Screen ke bohot upar se spawn
        self.speed_offset = random.randint(0, 3) # Har car ki apni alag speed

    def move(self, speed):
        self.rect.y += (speed + self.speed_offset)
        if self.rect.y > HEIGHT:
            self.reset()
            return True # Score badhane ke liye
        return False

# ================= GAME STATE =================
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 22, bold=True)
nitro_font = pygame.font.SysFont("Impact", 35)

class Game:
    def __init__(self):
        self.in_menu = True
        self.reset()

    def reset(self):
        self.score, self.lives, self.nitro, self.bg_y = 0, 3, 100, 0
        self.game_over, self.hit_cooldown = False, 0
        self.player_rect = car_img.get_rect(center=(WIDTH//2, HEIGHT-100))
        # Ek saath 3 cars spawn hongi
        self.enemies = [Enemy() for _ in range(3)]

state = Game()
nitro_channel = pygame.mixer.Channel(1)
running = True

# ================= MAIN LOOP =================
while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if state.in_menu: state.in_menu = False
            elif state.game_over: state.reset()

    screen.blit(road_img, (0, int(state.bg_y)))
    screen.blit(road_img, (0, int(state.bg_y - HEIGHT)))

    if state.in_menu:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); overlay.fill((0,0,0,180))
        screen.blit(overlay, (0,0))
        if logo_img: screen.blit(logo_img, (WIDTH//2 - 60, HEIGHT//2 - 220))
        screen.blit(font.render("JUNGLE NITRO: EXTREME", True, (255, 215, 0)), (80, 250))
        screen.blit(font.render("CLICK TO START", True, (255, 255, 255)), (115, 320))

    elif not state.game_over:
        dynamic_speed = 6 + (state.score // 15)
        keys = pygame.key.get_pressed()
        is_nitro = keys[pygame.K_SPACE] and state.nitro > 0
        curr_speed = dynamic_speed + 8 if is_nitro else dynamic_speed
        
        if is_nitro:
            state.nitro -= 1.2
            nitro_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); nitro_overlay.fill((0, 100, 255, 70))
            screen.blit(nitro_overlay, (0,0))
            screen.blit(nitro_font.render("NITRO BOOST", True, (0, 255, 255)), (WIDTH//2 - 90, HEIGHT - 180))
            if nitro_sound and not nitro_channel.get_busy(): nitro_channel.play(nitro_sound)
        else:
            nitro_channel.stop()
            if state.nitro < 100: state.nitro += 0.4

        state.bg_y = (state.bg_y + curr_speed) % HEIGHT
        move_val = 10 if is_nitro else 6
        if keys[pygame.K_LEFT] and state.player_rect.left > 80: state.player_rect.x -= move_val
        if keys[pygame.K_RIGHT] and state.player_rect.right < 320: state.player_rect.x += move_val

        # --- MULTIPLE ENEMIES LOGIC ---
        for e in state.enemies:
            if e.move(curr_speed):
                state.score += 1
            
            # Collision
            if state.hit_cooldown == 0 and state.player_rect.colliderect(e.rect):
                if crash_sound: crash_sound.play()
                state.lives -= 1
                state.hit_cooldown = 60
                e.reset()
                if state.lives <= 0: state.game_over = True

            screen.blit(e.image, e.rect)

        if state.hit_cooldown > 0: state.hit_cooldown -= 1
        if state.hit_cooldown % 10 < 5: screen.blit(car_img, state.player_rect)
        
        # HUD
        screen.blit(font.render(f"Score: {state.score}", True, (255, 255, 255)), (15, 10))
        pygame.draw.rect(screen, (0, 200, 255), (15, 40, int(state.nitro), 10))
        for i in range(state.lives): draw_heart(screen, WIDTH - 25 - (i * 25), 25, 8)

    elif state.game_over:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); overlay.fill((0,0,0,220))
        screen.blit(overlay, (0,0))
        screen.blit(font.render("GAME OVER", True, (255, 50, 50)), (130, 250))
        screen.blit(font.render(f"Final Score: {state.score}", True, (255, 255, 255)), (130, 300))
        screen.blit(font.render("Click to Restart", True, (255, 215, 0)), (115, 350))

    pygame.display.flip()
pygame.quit()