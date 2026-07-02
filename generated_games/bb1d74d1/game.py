import pygame, sys, random, math

pygame.init()

# --- Screen Dimensions ---
WIDTH, HEIGHT = 800, 600
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Prince Valiant and the Giggling Gauntlet!")

# --- Clock ---
CLOCK = pygame.time.Clock()

# --- Color Palette (Jewel Tones) ---
SAPPHIRE = (25, 25, 112)
AMETHYST = (147, 112, 219)
EMERALD = (50, 205, 50)
RUBY = (220, 20, 60)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)
PEARL = (248, 248, 255)
TOPAZ = (255, 193, 7)
CRIMSON_GLOW = (255, 0, 80)
AZURE_GLOW = (0, 200, 255)
DARK_SAPPHIRE = (15, 15, 70)
FOREST_GREEN = (34, 139, 34)

# --- Game States ---
GAME_STATE_PLAYING = 1
GAME_STATE_GAME_OVER = 2
current_game_state = GAME_STATE_PLAYING

# --- Fonts ---
font_small = pygame.font.Font(None, 24)
font_medium = pygame.font.Font(None, 36)
font_large = pygame.font.Font(None, 72)

# --- Background Gradient Colors ---
GRADIENT_TOP_COLOR = DARK_SAPPHIRE
GRADIENT_BOTTOM_COLOR = SAPPHIRE

def draw_gradient_background(surface):
    """Draws a vertical gradient background."""
    for y in range(HEIGHT):
        r = GRADIENT_TOP_COLOR[0] + (GRADIENT_BOTTOM_COLOR[0] - GRADIENT_TOP_COLOR[0]) * y / HEIGHT
        g = GRADIENT_TOP_COLOR[1] + (GRADIENT_BOTTOM_COLOR[1] - GRADIENT_TOP_COLOR[1]) * y / HEIGHT
        b = GRADIENT_TOP_COLOR[2] + (GRADIENT_BOTTOM_COLOR[2] - GRADIENT_TOP_COLOR[2]) * y / HEIGHT
        pygame.draw.line(surface, (int(r), int(g), int(b)), (0, y), (WIDTH, y))

class Player:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT - 80
        self.size = 20
        self.speed = 5
        self.health = 100
        self.max_health = 100
        self.last_shot_time = pygame.time.get_ticks()
        self.shoot_delay = 300 # milliseconds
        self.rapid_fire_active = False
        self.rapid_fire_end_time = 0
        self.trail = []
        self.trail_length = 5
        self.trail_spacing = 10

    def draw(self, surface):
        # Glow effect
        glow_colors = [AZURE_GLOW, AZURE_GLOW, PEARL]
        glow_sizes = [self.size + 10, self.size + 5, self.size]
        for i in range(len(glow_colors)):
            alpha = int(255 * (0.3 - i * 0.1)) # Fading alpha
            temp_surface = pygame.Surface((glow_sizes[i]*2, glow_sizes[i]*2), pygame.SRCALPHA)
            pygame.draw.circle(temp_surface, (glow_colors[i][0], glow_colors[i][1], glow_colors[i][2], alpha), 
                               (glow_sizes[i], glow_sizes[i]), glow_sizes[i])
            surface.blit(temp_surface, (self.x - glow_sizes[i], self.y - glow_sizes[i]))

        # Trail effect
        for i, pos in enumerate(self.trail):
            alpha = int(255 * (i / self.trail_length) * 0.5) # Fades out
            trail_color = (AZURE_GLOW[0], AZURE_GLOW[1], AZURE_GLOW[2], alpha)
            pygame.draw.circle(surface, trail_color, pos, 3 + i//2, 0) # Fades out and shrinks

        # Player character (Prince Valiant)
        # Body (Tunic)
        body_rect = pygame.Rect(self.x - self.size, self.y - self.size, self.size * 2, self.size * 2)
        pygame.draw.ellipse(surface, AMETHYST, body_rect)
        
        # Head
        pygame.draw.circle(surface, PEARL, (self.x, self.y - self.size - 10), self.size // 2)
        
        # Arms
        pygame.draw.line(surface, PEARL, (self.x - self.size + 5, self.y - self.size + 10), (self.x - self.size - 10, self.y - 5), 4)
        pygame.draw.line(surface, PEARL, (self.x + self.size - 5, self.y - self.size + 10), (self.x + self.size + 10, self.y - 5), 4)
        
        # Legs
        pygame.draw.line(surface, AMETHYST, (self.x - self.size // 2, self.y + self.size - 5), (self.x - self.size // 2, self.y + self.size + 15), 5)
        pygame.draw.line(surface, AMETHYST, (self.x + self.size // 2, self.y + self.size - 5), (self.x + self.size // 2, self.y + self.size + 15), 5)

        # Shield (triangle)
        shield_points = [
            (self.x - self.size - 15, self.y - 10),
            (self.x - self.size - 5, self.y - 25),
            (self.x - self.size + 5, self.y - 10)
        ]
        pygame.draw.polygon(surface, SILVER, shield_points)
        pygame.draw.circle(surface, AMETHYST, (self.x - self.size - 5, self.y - 15), 3) # Shield boss

    def update(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.y += self.speed

        self.x = max(self.size, min(WIDTH - self.size, self.x))
        self.y = max(self.size, min(HEIGHT - self.size, self.y))

        # Update trail
        if len(self.trail) == 0 or math.hypot(self.x - self.trail[-1][0], self.y - self.trail[-1][1]) > self.trail_spacing:
            self.trail.append((self.x, self.y))
            if len(self.trail) > self.trail_length:
                self.trail.pop(0)
        
        # Rapid fire power-up check
        if self.rapid_fire_active and pygame.time.get_ticks() > self.rapid_fire_end_time:
            self.rapid_fire_active = False
            self.shoot_delay = 300 # Reset to normal delay

    def shoot(self, projectiles):
        now = pygame.time.get_ticks()
        current_delay = self.shoot_delay / 2 if self.rapid_fire_active else self.shoot_delay
        if now - self.last_shot_time > current_delay:
            projectiles.append(Projectile(self.x, self.y - self.size - 20))
            self.last_shot_time = now

    def get_rect(self):
        return pygame.Rect(self.x - self.size, self.y - self.size - 20, self.size * 2, self.size * 2 + 20)

class Projectile:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 8
        self.speed = 10

    def draw(self, surface):
        # Inner glow
        pygame.draw.circle(surface, AZURE_GLOW, (self.x, self.y), self.radius + 4, 0)
        # Main spark
        pygame.draw.circle(surface, PEARL, (self.x, self.y), self.radius, 0)
        # Outer smaller sparks
        pygame.draw.circle(surface, AZURE_GLOW, (self.x + 5, self.y - 5), self.radius // 3)
        pygame.draw.circle(surface, AZURE_GLOW, (self.x - 5, self.y - 5), self.radius // 3)

    def update(self):
        self.y -= self.speed

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

class GigglingGoblin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 25
        self.speed_x = random.choice([-2, 2])
        self.speed_y = 1
        self.health = 20
        self.score_value = 100

    def draw(self, surface):
        # Body (large circle)
        pygame.draw.circle(surface, FOREST_GREEN, (self.x, self.y), self.size)
        
        # Head (smaller circle)
        pygame.draw.circle(surface, FOREST_GREEN, (self.x, self.y - self.size - 10), self.size * 0.7)
        
        # Ears (triangles)
        pygame.draw.polygon(surface, FOREST_GREEN, [
            (self.x - self.size * 0.7 - 5, self.y - self.size - 15),
            (self.x - self.size * 0.7 + 5, self.y - self.size - 25),
            (self.x - self.size * 0.7 + 10, self.y - self.size - 15)
        ])
        pygame.draw.polygon(surface, FOREST_GREEN, [
            (self.x + self.size * 0.7 + 5, self.y - self.size - 15),
            (self.x + self.size * 0.7 - 5, self.y - self.size - 25),
            (self.x + self.size * 0.7 - 10, self.y - self.size - 15)
        ])
        
        # Eyes (dots)
        pygame.draw.circle(surface, RUBY, (self.x - self.size * 0.3, self.y - self.size - 15), 3)
        pygame.draw.circle(surface, RUBY, (self.x + self.size * 0.3, self.y - self.size - 15), 3)
        
        # Club (line + circle)
        pygame.draw.line(surface, SILVER, (self.x + self.size + 5, self.y - 5), (self.x + self.size + 15, self.y + 10), 5)
        pygame.draw.circle(surface, SILVER, (self.x + self.size + 15, self.y + 10), 8)

    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y

        if self.x < self.size or self.x > WIDTH - self.size:
            self.speed_x *= -1
        
        if self.y > HEIGHT + self.size: # Off screen
            return True
        return False

    def get_rect(self):
        return pygame.Rect(self.x - self.size, self.y - self.size - 20, self.size * 2, self.size * 2 + 20)

class WobblingWisp:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 20
        self.amplitude = 30
        self.frequency = 0.05
        self.speed = 2
        self.initial_x = x
        self.health = 10
        self.score_value = 150

    def draw(self, surface):
        # Core (bright center) - Glow effect
        glow_colors = [PEARL, AZURE_GLOW, AZURE_GLOW]
        glow_sizes = [self.size // 2, self.size // 2 + 5, self.size // 2 + 10]
        for i in range(len(glow_colors)):
            alpha = int(255 * (0.6 - i * 0.2)) # Fading alpha
            temp_surface = pygame.Surface((glow_sizes[i]*2, glow_sizes[i]*2), pygame.SRCALPHA)
            pygame.draw.circle(temp_surface, (glow_colors[i][0], glow_colors[i][1], glow_colors[i][2], alpha), 
                               (glow_sizes[i], glow_sizes[i]), glow_sizes[i])
            surface.blit(temp_surface, (self.x - glow_sizes[i], self.y - glow_sizes[i]))

        # Body (ellipse)
        body_rect = pygame.Rect(self.x - self.size, self.y - self.size // 2, self.size * 2, self.size)
        pygame.draw.ellipse(surface, AMETHYST, body_rect)

        # Wings (smaller ellipses, semi-transparent)
        wing_surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(wing_surface, (AMETHYST[0], AMETHYST[1], AMETHYST[2], 150), 
                            pygame.Rect(self.size * 0.1, self.size * 0.1, self.size, self.size * 1.5))
        pygame.draw.ellipse(wing_surface, (AMETHYST[0], AMETHYST[1], AMETHYST[2], 150), 
                            pygame.Rect(self.size * 0.9, self.size * 0.1, self.size, self.size * 1.5))
        surface.blit(wing_surface, (self.x - self.size, self.y - self.size))

        # Tendrils (lines)
        pygame.draw.line(surface, AMETHYST, (self.x - self.size // 2, self.y + self.size // 2), (self.x - self.size // 2 - 5, self.y + self.size + 5), 2)
        pygame.draw.line(surface, AMETHYST, (self.x + self.size // 2, self.y + self.size // 2), (self.x + self.size // 2 + 5, self.y + self.size + 5), 2)

    def update(self):
        self.y += self.speed
        self.x = self.initial_x + self.amplitude * math.sin(pygame.time.get_ticks() * self.frequency / 1000)

        if self.y > HEIGHT + self.size: # Off screen
            return True
        return False

    def get_rect(self):
        return pygame.Rect(self.x - self.size, self.y - self.size, self.size * 2, self.size * 2)

class EnchantedScroll:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 40
        self.speed = 2
        self.powerup_duration = 5000 # 5 seconds

    def draw(self, surface):
        # Scroll body (rounded rect)
        scroll_rect = pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, self.width, self.height)
        pygame.draw.rect(surface, GOLD, scroll_rect, border_radius=5)
        
        # Rolled ends (ellipses)
        pygame.draw.ellipse(surface, TOPAZ, (self.x - self.width // 2 - 2, self.y - self.height // 2, self.width + 4, 5))
        pygame.draw.ellipse(surface, TOPAZ, (self.x - self.width // 2 - 2, self.y + self.height // 2 - 5, self.width + 4, 5))
        
        # Seal (circle + polygon)
        pygame.draw.circle(surface, RUBY, (self.x + self.width // 4, self.y + self.height // 4), 6)
        seal_star_points = [
            (self.x + self.width // 4, self.y + self.height // 4 - 5),
            (self.x + self.width // 4 + 2, self.y + self.height // 4 - 2),
            (self.x + self.width // 4 + 5, self.y + self.height // 4),
            (self.x + self.width // 4 + 2, self.y + self.height // 4 + 2),
            (self.x + self.width // 4, self.y + self.height // 4 + 5),
            (self.x + self.width // 4 - 2, self.y + self.height // 4 + 2),
            (self.x + self.width // 4 - 5, self.y + self.height // 4),
            (self.x + self.width // 4 - 2, self.y + self.height // 4 - 2)
        ]
        pygame.draw.polygon(surface, GOLD, seal_star_points)

    def update(self):
        self.y += self.speed
        if self.y > HEIGHT + self.height: # Off screen
            return True
        return False

    def get_rect(self):
        return pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, self.width, self.height)

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.radius = random.randint(3, 8)
        self.speed_x = random.uniform(-3, 3)
        self.speed_y = random.uniform(-5, -1)
        self.life = 60 # frames
        self.initial_life = self.life

    def draw(self, surface):
        alpha = int(255 * (self.life / self.initial_life))
        draw_color = (self.color[0], self.color[1], self.color[2], alpha)
        pygame.draw.circle(surface, draw_color, (int(self.x), int(self.y)), self.radius)

    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.speed_y += 0.1 # Gravity effect
        self.life -= 1
        return self.life <= 0

class ScorePopup:
    def __init__(self, x, y, score, color):
        self.x = x
        self.y = y
        self.score = score
        self.color = color
        self.life = 60 # frames
        self.initial_y = y

    def draw(self, surface):
        alpha = int(255 * (self.life / 60))
        text_surface = font_small.render(f"+{self.score}", True, (self.color[0], self.color[1], self.color[2], alpha))
        surface.blit(text_surface, (self.x - text_surface.get_width() // 2, self.y))

    def update(self):
        self.y -= 1 # Rise
        self.life -= 1
        return self.life <= 0

# --- Game Variables ---
player = Player()
projectiles = []
enemies = []
powerups = []
explosion_particles = []
score_popups = []
score = 0
enemy_spawn_timer = 0
enemy_spawn_delay = 1000 # milliseconds
difficulty_increase_interval = 10000 # 10 seconds
last_difficulty_increase_time = pygame.time.get_ticks()

screen_flash_alpha = 0
screen_flash_duration = 100 # milliseconds
screen_flash_start_time = 0

def reset_game():
    global player, projectiles, enemies, powerups, explosion_particles, score_popups, score
    global enemy_spawn_timer, enemy_spawn_delay, difficulty_increase_interval, last_difficulty_increase_time
    global screen_flash_alpha, screen_flash_start_time, current_game_state

    player = Player()
    projectiles = []
    enemies = []
    powerups = []
    explosion_particles = []
    score_popups = []
    score = 0
    enemy_spawn_timer = 0
    enemy_spawn_delay = 1000
    difficulty_increase_interval = 10000
    last_difficulty_increase_time = pygame.time.get_ticks()
    screen_flash_alpha = 0
    screen_flash_start_time = 0
    current_game_state = GAME_STATE_PLAYING

# --- UI Drawing Functions ---
def draw_text_with_shadow(surface, text, font, color, shadow_color, x, y):
    shadow_surface = font.render(text, True, shadow_color)
    text_surface = font.render(text, True, color)
    surface.blit(shadow_surface, (x + 2, y + 2))
    surface.blit(text_surface, (x, y))

def draw_health_bar(surface, x, y, width, height, current_health, max_health):
    # Background (rounded rect)
    pygame.draw.rect(surface, DARK_SAPPHIRE, (x, y, width, height), border_radius=5)
    
    # Fill
    fill_width = (current_health / max_health) * width
    health_color = EMERALD if current_health > max_health * 0.5 else RUBY
    pygame.draw.rect(surface, health_color, (x, y, fill_width, height), border_radius=5)
    
    # Border (white)
    pygame.draw.rect(surface, PEARL, (x, y, width, height), 2, border_radius=5)

def draw_game_over_screen(surface):
    # Semi-transparent dark overlay
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))

    # Game Over text
    draw_text_with_shadow(surface, "GAME OVER", font_large, RUBY, DARK_SAPPHIRE,
                          WIDTH // 2 - font_large.size("GAME OVER")[0] // 2,
                          HEIGHT // 2 - 50)
    
    # Final Score
    draw_text_with_shadow(surface, f"Score: {score}", font_medium, GOLD, DARK_SAPPHIRE,
                          WIDTH // 2 - font_medium.size(f"Score: {score}")[0] // 2,
                          HEIGHT // 2 + 20)

    # Restart hint
    draw_text_with_shadow(surface, "Press R to restart", font_small, PEARL, DARK_SAPPHIRE,
                          WIDTH // 2 - font_small.size("Press R to restart")[0] // 2,
                          HEIGHT // 2 + 80)

# --- Game Loop ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and current_game_state == GAME_STATE_PLAYING:
                player.shoot(projectiles)
            if event.key == pygame.K_r and current_game_state == GAME_STATE_GAME_OVER:
                reset_game()

    if current_game_state == GAME_STATE_PLAYING:
        keys = pygame.key.get_pressed()
        player.update(keys)

        # Update projectiles
        for p in projectiles:
            p.update()
        projectiles = [p for p in projectiles if p.y > 0]

        # Update enemies
        now = pygame.time.get_ticks()
        if now - enemy_spawn_timer > enemy_spawn_delay:
            enemy_x = random.randint(player.size, WIDTH - player.size)
            if random.random() < 0.7: # 70% chance for goblin
                enemies.append(GigglingGoblin(enemy_x, -50))
            else: # 30% chance for wisp
                enemies.append(WobblingWisp(enemy_x, -50))
            enemy_spawn_timer = now
        
        enemies_to_remove = []
        for i, e in enumerate(enemies):
            if e.update(): # If enemy goes off screen
                enemies_to_remove.append(i)
                player.health -= 10 # Player takes damage for letting enemy escape
                screen_flash_alpha = 150
                screen_flash_start_time = pygame.time.get_ticks()
                if player.health <= 0:
                    current_game_state = GAME_STATE_GAME_OVER
        for i in reversed(enemies_to_remove):
            enemies.pop(i)

        # Update powerups
        if random.random() < 0.0015 and len(powerups) < 1: # Small chance to spawn a powerup
            powerups.append(EnchantedScroll(random.randint(50, WIDTH - 50), -50))
        
        powerups_to_remove = []
        for i, p in enumerate(powerups):
            if p.update():
                powerups_to_remove.append(i)
        for i in reversed(powerups_to_remove):
            powerups.pop(i)

        # Collision detection: Projectile vs Enemy
        projectiles_to_remove = []
        enemies_to_remove = []
        for i, p in enumerate(projectiles):
            for j, e in enumerate(enemies):
                if p.get_rect().colliderect(e.get_rect()):
                    e.health -= 10 # Projectile damage
                    projectiles_to_remove.append(i)
                    if e.health <= 0:
                        enemies_to_remove.append(j)
                        score += e.score_value
                        score_popups.append(ScorePopup(e.x, e.y, e.score_value, GOLD))
                        # Explosion particles
                        for _ in range(random.randint(8, 12)):
                            explosion_particles.append(Particle(e.x, e.y, random.choice([RUBY, GOLD, CRIMSON_GLOW])))
                    break # Projectile hits only one enemy
        
        # Remove hit projectiles and dead enemies
        projectiles = [p for i, p in enumerate(projectiles) if i not in projectiles_to_remove]
        enemies = [e for i, e in enumerate(enemies) if i not in enemies_to_remove]

        # Collision detection: Player vs Enemy
        for e in enemies:
            if player.get_rect().colliderect(e.get_rect()):
                player.health -= 20
                enemies.remove(e) # Enemy disappears on collision
                score_popups.append(ScorePopup(e.x, e.y, -20, RUBY))
                screen_flash_alpha = 150
                screen_flash_start_time = pygame.time.get_ticks()
                if player.health <= 0:
                    current_game_state = GAME_STATE_GAME_OVER
                break # Player can only collide with one enemy per frame

        # Collision detection: Player vs Powerup
        powerups_to_remove = []
        for i, pu in enumerate(powerups):
            if player.get_rect().colliderect(pu.get_rect()):
                player.rapid_fire_active = True
                player.rapid_fire_end_time = pygame.time.get_ticks() + pu.powerup_duration
                powerups_to_remove.append(i)
                score += 500
                score_popups.append(ScorePopup(pu.x, pu.y, 500, EMERALD))
        powerups = [pu for i, pu in enumerate(powerups) if i not in powerups_to_remove]

        # Update particles
        particles_to_remove = []
        for i, p in enumerate(explosion_particles):
            if p.update():
                particles_to_remove.append(i)
        explosion_particles = [p for i, p in enumerate(explosion_particles) if i not in particles_to_remove]

        # Update score popups
        popups_to_remove = []
        for i, sp in enumerate(score_popups):
            if sp.update():
                popups_to_remove.append(i)
        score_popups = [sp for i, sp in enumerate(score_popups) if i not in popups_to_remove]

        # Difficulty scaling
        if now - last_difficulty_increase_time > difficulty_increase_interval:
            enemy_spawn_delay = max(200, enemy_spawn_delay - 50) # Faster spawns, minimum 200ms
            for e in enemies: # Make existing enemies faster
                if isinstance(e, GigglingGoblin):
                    e.speed_y += 0.1
                    e.speed_x += 0.1 * (1 if e.speed_x > 0 else -1)
                elif isinstance(e, WobblingWisp):
                    e.speed += 0.1
            last_difficulty_increase_time = now

        # --- Drawing ---
        draw_gradient_background(SCREEN)

        player.draw(SCREEN)

        for p in projectiles:
            p.draw(SCREEN)
        
        for e in enemies:
            e.draw(SCREEN)

        for pu in powerups:
            pu.draw(SCREEN)
        
        for p in explosion_particles:
            p.draw(SCREEN)
        
        for sp in score_popups:
            sp.draw(SCREEN)

        # UI: Score and Health
        draw_text_with_shadow(SCREEN, f"Score: {score}", font_medium, GOLD, DARK_SAPPHIRE, 10, 10)
        draw_health_bar(SCREEN, WIDTH - 160, 10, 150, 20, player.health, player.max_health)

        # Screen Flash effect
        if screen_flash_alpha > 0:
            flash_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash_surface.fill((RUBY[0], RUBY[1], RUBY[2], screen_flash_alpha))
            SCREEN.blit(flash_surface, (0, 0))
            
            if pygame.time.get_ticks() - screen_flash_start_time > screen_flash_duration:
                screen_flash_alpha = 0
            else:
                screen_flash_alpha = max(0, screen_flash_alpha - 5) # Fade out

    elif current_game_state == GAME_STATE_GAME_OVER:
        draw_gradient_background(SCREEN) # Still draw background
        draw_game_over_screen(SCREEN)

    pygame.display.flip()
    CLOCK.tick(60)

pygame.quit()
sys.exit()