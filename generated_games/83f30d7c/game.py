import pygame, sys, random, math

pygame.init()

# --- Screen Dimensions ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Aqua-Star Scavenger!")

# --- Color Palette (Rule 4: Neon Water Theme) ---
NEON_BLUE = (0, 191, 255)      # Deep Sky Blue
NEON_CYAN = (0, 255, 255)      # Aqua
NEON_GREEN = (57, 255, 20)     # Bright Green
NEON_PINK = (255, 20, 147)     # Deep Pink
NEON_PURPLE = (138, 43, 226)   # Blue Violet
NEON_ORANGE = (255, 140, 0)    # Dark Orange
NEON_YELLOW = (255, 255, 0)    # Yellow
DARK_BLUE_ACCENT = (25, 25, 112) # Midnight Blue
LIGHT_GREY = (200, 200, 200)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED_OVERLAY = (255, 0, 0, 100) # For screen flash
GLOW_ALPHA = 70 # For glow effect alpha

# --- Fonts ---
font = pygame.font.Font(None, 36)
large_font = pygame.font.Font(None, 72)
medium_font = pygame.font.Font(None, 48)

# --- Game Variables ---
clock = pygame.time.Clock()
FPS = 60
game_over = False
score = 0
screen_flash_duration = 0
screen_flash_timer = 0

# --- Background (Rule 2: Starfield) ---
stars = []
for _ in range(150):
    stars.append({
        'x': random.randint(0, SCREEN_WIDTH),
        'y': random.randint(0, SCREEN_HEIGHT),
        'size': random.randint(1, 3),
        'color': random.choice([WHITE, NEON_YELLOW, NEON_CYAN])
    })

def draw_starfield():
    screen.fill(DARK_BLUE_ACCENT) # Dark base for space
    for star in stars:
        pygame.draw.circle(screen, star['color'], (star['x'], star['y']), star['size'])

# --- Helper Functions for Drawing (Rule 3: Glow Effect) ---
def draw_glowing_circle(surface, color, center, radius, width=0, alpha_step=GLOW_ALPHA):
    """Draws a glowing circle by drawing multiple circles with decreasing size and alpha."""
    for i in range(3):
        alpha = max(0, alpha_step - i * (alpha_step // 2))
        glow_color = color[:3] + (alpha,)
        glow_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, glow_color, (radius, radius), radius - i)
        surface.blit(glow_surface, (center[0] - radius, center[1] - radius))
    pygame.draw.circle(surface, color, center, radius, width) # Bright center

def draw_glowing_polygon(surface, color, points, width=0, alpha_step=GLOW_ALPHA):
    """Draws a glowing polygon."""
    min_x = min(p[0] for p in points)
    max_x = max(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)
    poly_width = max_x - min_x
    poly_height = max_y - min_y
    
    for i in range(3):
        alpha = max(0, alpha_step - i * (alpha_step // 2))
        glow_color = color[:3] + (alpha,)
        
        # Scale points for glow
        scaled_points = []
        scale_factor = 1 + i * 0.1 # Outer glow is slightly larger
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        for p_x, p_y in points:
            new_x = center_x + (p_x - center_x) * scale_factor
            new_y = center_y + (p_y - center_y) * scale_factor
            scaled_points.append((new_x, new_y))

        glow_surface = pygame.Surface((poly_width * 2, poly_height * 2), pygame.SRCALPHA) # Larger surface for glow
        
        # Offset points to be relative to the glow_surface top-left
        offset_points = [(p[0] - min_x + poly_width/2 - poly_width * scale_factor / 2, 
                          p[1] - min_y + poly_height/2 - poly_height * scale_factor / 2) for p in scaled_points]

        if len(offset_points) >= 3:
            pygame.draw.polygon(glow_surface, glow_color, offset_points)
            surface.blit(glow_surface, (min_x - (poly_width * scale_factor / 2 - poly_width/2), min_y - (poly_height * scale_factor / 2 - poly_height/2)))
    
    pygame.draw.polygon(surface, color, points, width) # Bright center

# --- Player Class (Rule 1: Complex shape, Rule 3: Trail effect, Glow effect) ---
class Player:
    def __init__(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT - 70
        self.speed = 5
        self.health = 100
        self.max_health = 100
        self.width = 40
        self.height = 60
        self.last_shot_time = pygame.time.get_ticks()
        self.shoot_cooldown = 200 # milliseconds
        self.trail_positions = [] # Stores (x, y, timestamp)
        self.trail_length = 10
        self.trail_lifespan = 500 # milliseconds
        self.invincible_timer = 0

    def draw(self):
        # Rule 3: Trail effect
        for i, (tx, ty, t_time) in enumerate(self.trail_positions):
            age = pygame.time.get_ticks() - t_time
            if age < self.trail_lifespan:
                alpha = 255 - int(255 * (age / self.trail_lifespan))
                radius = max(1, 8 - i)
                trail_color = NEON_CYAN[:3] + (alpha,)
                pygame.draw.circle(screen, trail_color, (tx, ty), radius)

        # Main Body (Polygon)
        body_points = [
            (self.x, self.y - self.height // 2),        # Top tip
            (self.x + self.width // 2, self.y + self.height // 2), # Bottom right
            (self.x, self.y + self.height // 2 - 10),   # Bottom middle indent
            (self.x - self.width // 2, self.y + self.height // 2)  # Bottom left
        ]
        draw_glowing_polygon(screen, NEON_BLUE, body_points)

        # Wings (Triangles)
        wing_left_points = [
            (self.x - self.width // 2, self.y + self.height // 2),
            (self.x - self.width // 2 - 15, self.y + self.height // 2 - 20),
            (self.x - self.width // 2, self.y + self.height // 2 - 30)
        ]
        draw_glowing_polygon(screen, NEON_CYAN, wing_left_points)

        wing_right_points = [
            (self.x + self.width // 2, self.y + self.height // 2),
            (self.x + self.width // 2 + 15, self.y + self.height // 2 - 20),
            (self.x + self.width // 2, self.y + self.height // 2 - 30)
        ]
        draw_glowing_polygon(screen, NEON_CYAN, wing_right_points)

        # Cockpit (Circle)
        draw_glowing_circle(screen, NEON_YELLOW, (self.x, self.y - 10), 10)

        # Engine Glow (Rule 3: Glow effect for engine)
        engine_glow_center = (self.x, self.y + self.height // 2 + 5)
        draw_glowing_circle(screen, NEON_ORANGE, engine_glow_center, 8, alpha_step=100)
        draw_glowing_circle(screen, NEON_YELLOW, engine_glow_center, 5, alpha_step=100)

        # Fins (Small triangles on top)
        fin_left_points = [
            (self.x - 10, self.y - self.height // 2 - 5),
            (self.x - 5, self.y - self.height // 2 - 20),
            (self.x, self.y - self.height // 2 - 5)
        ]
        pygame.draw.polygon(screen, NEON_CYAN, fin_left_points)

        fin_right_points = [
            (self.x + 10, self.y - self.height // 2 - 5),
            (self.x + 5, self.y - self.height // 2 - 20),
            (self.x, self.y - self.height // 2 - 5)
        ]
        pygame.draw.polygon(screen, NEON_CYAN, fin_right_points)

        if self.invincible_timer > 0 and (pygame.time.get_ticks() // 100) % 2 == 0:
            # Flash player when invincible
            pygame.draw.circle(screen, NEON_PINK, (self.x, self.y), 30, 2)


    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.x -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.x += self.speed
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.y -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.y += self.speed

        # Boundary checks
        self.x = max(self.width // 2, min(self.x, SCREEN_WIDTH - self.width // 2))
        self.y = max(self.height // 2, min(self.y, SCREEN_HEIGHT - self.height // 2))

        # Update trail
        self.trail_positions.insert(0, (self.x, self.y, pygame.time.get_ticks()))
        if len(self.trail_positions) > self.trail_length:
            self.trail_positions.pop()

        # Update invincibility
        if self.invincible_timer > 0:
            self.invincible_timer -= clock.get_time()

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot_time > self.shoot_cooldown:
            self.last_shot_time = now
            return Bullet(self.x, self.y - self.height // 2)
        return None

    def take_damage(self, amount):
        global screen_flash_timer, screen_flash_duration
        if self.invincible_timer <= 0:
            self.health -= amount
            screen_flash_duration = 100 # milliseconds
            screen_flash_timer = screen_flash_duration
            self.invincible_timer = 1000 # 1 second invincibility
            if self.health <= 0:
                return True
        return False

    def get_rect(self):
        return pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, self.width, self.height)

# --- Bullet Class (Rule 3: Glow effect) ---
class Bullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 10
        self.radius = 4

    def draw(self):
        # Rule 3: Glow effect for bullet
        draw_glowing_circle(screen, NEON_PINK, (self.x, self.y), self.radius, alpha_step=100)

    def update(self):
        self.y -= self.speed
        return self.y < 0 # Return True if off-screen

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

# --- Explosion Particle Class (Rule 3: Explosion particles) ---
class ExplosionParticle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.radius = random.randint(3, 8)
        self.speed_x = random.uniform(-3, 3)
        self.speed_y = random.uniform(-3, 3)
        self.lifespan = random.randint(300, 600) # milliseconds
        self.creation_time = pygame.time.get_ticks()

    def draw(self):
        age = pygame.time.get_ticks() - self.creation_time
        if age < self.lifespan:
            alpha = 255 - int(255 * (age / self.lifespan))
            particle_color = self.color[:3] + (alpha,)
            pygame.draw.circle(screen, particle_color, (int(self.x), int(self.y)), self.radius)

    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        return pygame.time.get_ticks() - self.creation_time > self.lifespan # Return True if dead

# --- Enemy Classes (Rule 1: Complex shapes) ---
class Enemy:
    def __init__(self, x, y, speed, health, damage):
        self.x = x
        self.y = y
        self.speed = speed
        self.health = health
        self.damage = damage
        self.width = 0 # Placeholder, set in child classes
        self.height = 0 # Placeholder, set in child classes

    def update(self):
        self.y += self.speed
        return self.y > SCREEN_HEIGHT # Return True if off-screen

    def take_damage(self, amount):
        self.health -= amount
        return self.health <= 0 # Return True if dead

    def get_rect(self):
        return pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, self.width, self.height)

class SquidMine(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, random.uniform(1.5, 3), 20, 10)
        self.width = 40
        self.height = 40
        self.tentacle_offset = random.uniform(-5, 5) # For wobbly animation

    def draw(self):
        # Body (Circle)
        pygame.draw.circle(screen, NEON_PURPLE, (self.x, self.y), 20)
        pygame.draw.circle(screen, DARK_BLUE_ACCENT, (self.x, self.y), 15) # Inner circle

        # Eyes (Dots)
        pygame.draw.circle(screen, WHITE, (self.x - 8, self.y - 5), 3)
        pygame.draw.circle(screen, WHITE, (self.x + 8, self.y - 5), 3)
        pygame.draw.circle(screen, BLACK, (self.x - 8, self.y - 5), 1)
        pygame.draw.circle(screen, BLACK, (self.x + 8, self.y - 5), 1)

        # Tentacles (Lines)
        num_tentacles = 5
        for i in range(num_tentacles):
            angle = math.pi / (num_tentacles - 1) * i + self.tentacle_offset / 10
            end_x = self.x + math.cos(angle + math.pi/2) * 25
            end_y = self.y + math.sin(angle + math.pi/2) * 25 + 15
            pygame.draw.line(screen, NEON_PINK, (self.x, self.y + 10), (end_x, end_y), 3)
        
        # Inner glow
        draw_glowing_circle(screen, NEON_PURPLE, (self.x, self.y), 18, alpha_step=50)


    def update(self):
        self.y += self.speed
        self.tentacle_offset = math.sin(pygame.time.get_ticks() / 200) * 5 # Wobble
        return self.y > SCREEN_HEIGHT

class JellyPuffer(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, random.uniform(2.5, 4.5), 30, 15)
        self.width = 50
        self.height = 40

    def draw(self):
        # Body (Ellipse)
        pygame.draw.ellipse(screen, NEON_GREEN, (self.x - 25, self.y - 20, 50, 40))
        pygame.draw.ellipse(screen, DARK_BLUE_ACCENT, (self.x - 20, self.y - 15, 40, 30))

        # Spikes/Puffs (Small circles/ellipses)
        spike_color = NEON_YELLOW
        pygame.draw.circle(screen, spike_color, (self.x - 20, self.y - 20), 5)
        pygame.draw.circle(screen, spike_color, (self.x + 20, self.y - 20), 5)
        pygame.draw.circle(screen, spike_color, (self.x - 25, self.y), 5)
        pygame.draw.circle(screen, spike_color, (self.x + 25, self.y), 5)
        pygame.draw.circle(screen, spike_color, (self.x - 20, self.y + 20), 5)
        pygame.draw.circle(screen, spike_color, (self.x + 20, self.y + 20), 5)

        # Eyes (Circles)
        pygame.draw.circle(screen, WHITE, (self.x - 10, self.y - 5), 4)
        pygame.draw.circle(screen, WHITE, (self.x + 10, self.y - 5), 4)
        pygame.draw.circle(screen, BLACK, (self.x - 10, self.y - 5), 2)
        pygame.draw.circle(screen, BLACK, (self.x + 10, self.y - 5), 2)
        
        # Inner glow
        draw_glowing_circle(screen, NEON_GREEN, (self.x, self.y), 22, alpha_step=50)

# --- Power-up Class (Rule 1: Complex shape, Rule 3: Glow effect) ---
class PowerUp:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 2
        self.radius = 15
        self.type = random.choice(['shield', 'score']) # Example types

    def draw(self):
        # Main bubble (Large circle with glow)
        draw_glowing_circle(screen, NEON_CYAN, (self.x, self.y), self.radius, alpha_step=GLOW_ALPHA)
        
        # Inner star (Polygon)
        star_points = []
        for i in range(5):
            angle = math.pi / 2 + i * 2 * math.pi / 5
            x_outer = self.x + math.cos(angle) * (self.radius - 5)
            y_outer = self.y + math.sin(angle) * (self.radius - 5)
            star_points.append((x_outer, y_outer))
            
            angle_inner = math.pi / 2 + (i + 0.5) * 2 * math.pi / 5
            x_inner = self.x + math.cos(angle_inner) * (self.radius - 12)
            y_inner = self.y + math.sin(angle_inner) * (self.radius - 12)
            star_points.append((x_inner, y_inner))
        pygame.draw.polygon(screen, NEON_YELLOW, star_points)

        # Sparkle dots
        pygame.draw.circle(screen, WHITE, (self.x + self.radius - 5, self.y - self.radius + 5), 2)
        pygame.draw.circle(screen, WHITE, (self.x - self.radius + 5, self.y + self.radius - 5), 2)

    def update(self):
        self.y += self.speed
        return self.y > SCREEN_HEIGHT

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

# --- Score Popup Class (Rule 3: Score popup) ---
class ScorePopup:
    def __init__(self, x, y, value):
        self.x = x
        self.y = y
        self.value = value
        self.color = NEON_YELLOW
        self.speed_y = -1 # Rises upwards
        self.lifespan = 1000 # milliseconds
        self.creation_time = pygame.time.get_ticks()
        self.font = pygame.font.Font(None, 24)

    def draw(self):
        age = pygame.time.get_ticks() - self.creation_time
        if age < self.lifespan:
            alpha = max(0, 255 - int(255 * (age / self.lifespan)))
            text_surface = self.font.render(f"+{self.value}", True, self.color)
            text_surface.set_alpha(alpha)
            screen.blit(text_surface, (self.x, self.y))

    def update(self):
        self.y += self.speed_y
        return pygame.time.get_ticks() - self.creation_time > self.lifespan # Return True if dead

# --- Game Entities ---
player = Player()
bullets = []
enemies = []
powerups = []
explosion_particles = []
score_popups = []

# --- Difficulty Scaling ---
enemy_spawn_timer = 0
enemy_spawn_interval = 1500 # milliseconds
powerup_spawn_timer = 0
powerup_spawn_interval = 5000 # milliseconds
game_time_start = pygame.time.get_ticks()

def reset_game():
    global player, bullets, enemies, powerups, explosion_particles, score_popups, game_over, score, enemy_spawn_timer, powerup_spawn_timer, game_time_start, screen_flash_timer, screen_flash_duration
    player = Player()
    bullets = []
    enemies = []
    powerups = []
    explosion_particles = []
    score_popups = []
    game_over = False
    score = 0
    enemy_spawn_timer = 0
    powerup_spawn_timer = 0
    game_time_start = pygame.time.get_ticks()
    screen_flash_timer = 0
    screen_flash_duration = 0

# --- Game Loop ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not game_over:
                new_bullet = player.shoot()
                if new_bullet:
                    bullets.append(new_bullet)
            if event.key == pygame.K_r and game_over:
                reset_game()

    if not game_over:
        # --- Update ---
        player.update()

        # Update bullets
        bullets_to_remove = []
        for bullet in bullets:
            if bullet.update():
                bullets_to_remove.append(bullet)
        for bullet in bullets_to_remove:
            bullets.remove(bullet)

        # Update enemies
        enemies_to_remove = []
        for enemy in enemies:
            if enemy.update():
                enemies_to_remove.append(enemy)
            
            # Enemy-Player collision
            if player.get_rect().colliderect(enemy.get_rect()):
                enemies_to_remove.append(enemy)
                if player.take_damage(enemy.damage):
                    game_over = True
        for enemy in enemies_to_remove:
            if enemy in enemies: # Check if still in list (could be removed by bullet)
                enemies.remove(enemy)

        # Update power-ups
        powerups_to_remove = []
        for powerup in powerups:
            if powerup.update():
                powerups_to_remove.append(powerup)
            
            # Power-up-Player collision
            if player.get_rect().colliderect(powerup.get_rect()):
                powerups_to_remove.append(powerup)
                score += 500
                score_popups.append(ScorePopup(powerup.x, powerup.y, 500))
                # Add shield effect or other power-up specific logic here
        for powerup in powerups_to_remove:
            if powerup in powerups:
                powerups.remove(powerup)

        # Update explosion particles
        particles_to_remove = []
        for particle in explosion_particles:
            if particle.update():
                particles_to_remove.append(particle)
        for particle in particles_to_remove:
            explosion_particles.remove(particle)
        
        # Update score popups
        popups_to_remove = []
        for popup in score_popups:
            if popup.update():
                popups_to_remove.append(popup)
        for popup in popups_to_remove:
            score_popups.remove(popup)


        # --- Collision Detection ---
        for bullet in bullets[:]: # Iterate over a copy to allow removal
            for enemy in enemies[:]:
                if bullet.get_rect().colliderect(enemy.get_rect()):
                    if enemy.take_damage(20): # Bullet damage
                        score += 100
                        score_popups.append(ScorePopup(enemy.x, enemy.y, 100))
                        # Rule 3: Explosion particles
                        for _ in range(random.randint(8, 12)):
                            explosion_particles.append(ExplosionParticle(enemy.x, enemy.y, random.choice([NEON_ORANGE, NEON_YELLOW, NEON_PINK])))
                        enemies.remove(enemy)
                    bullets.remove(bullet)
                    break # Bullet hit one enemy, so it's gone

        # --- Spawning ---
        now = pygame.time.get_ticks()
        elapsed_game_time = now - game_time_start

        # Difficulty scaling
        current_enemy_spawn_interval = max(500, enemy_spawn_interval - elapsed_game_time // 100)
        current_enemy_speed_multiplier = 1 + elapsed_game_time // 30000 * 0.1 # Every 30 seconds, speed increases by 10%

        if now - enemy_spawn_timer > current_enemy_spawn_interval:
            enemy_spawn_timer = now
            spawn_x = random.randint(30, SCREEN_WIDTH - 30)
            enemy_type = random.choice([SquidMine, JellyPuffer])
            new_enemy = enemy_type(spawn_x, -50)
            new_enemy.speed *= current_enemy_speed_multiplier
            enemies.append(new_enemy)

        if now - powerup_spawn_timer > powerup_spawn_interval:
            powerup_spawn_timer = now
            spawn_x = random.randint(50, SCREEN_WIDTH - 50)
            powerups.append(PowerUp(spawn_x, -50))

    # --- Draw ---
    draw_starfield()

    for powerup in powerups:
        powerup.draw()

    for enemy in enemies:
        enemy.draw()

    for bullet in bullets:
        bullet.draw()

    player.draw()

    for particle in explosion_particles:
        particle.draw()
        
    for popup in score_popups:
        popup.draw()

    # Rule 5: UI Polish - Score/Lives Text
    # Score
    score_text_surface = font.render(f"Score: {score}", True, LIGHT_GREY)
    score_shadow_surface = font.render(f"Score: {score}", True, BLACK)
    screen.blit(score_shadow_surface, (12, 12))
    screen.blit(score_text_surface, (10, 10))

    # Health Bar (Rule 5: UI Polish)
    health_bar_x = SCREEN_WIDTH - 150
    health_bar_y = 10
    health_bar_width = 140
    health_bar_height = 20
    border_radius = 5

    # Background (dark, rounded rect)
    pygame.draw.rect(screen, DARK_BLUE_ACCENT, (health_bar_x, health_bar_y, health_bar_width, health_bar_height), border_radius=border_radius)
    
    # Fill color based on health
    fill_width = (player.health / player.max_health) * (health_bar_width - 4) # -4 for padding
    health_color = NEON_GREEN
    if player.health < 60:
        health_color = NEON_YELLOW
    if player.health < 30:
        health_color = NEON_ORANGE

    pygame.draw.rect(screen, health_color, (health_bar_x + 2, health_bar_y + 2, fill_width, health_bar_height - 4), border_radius=border_radius)
    
    # White border
    pygame.draw.rect(screen, WHITE, (health_bar_x, health_bar_y, health_bar_width, health_bar_height), 2, border_radius=border_radius)

    # Health Text
    health_text_surface = font.render(f"HP: {player.health}", True, LIGHT_GREY)
    health_text_shadow = font.render(f"HP: {player.health}", True, BLACK)
    screen.blit(health_text_shadow, (health_bar_x + health_bar_width // 2 - health_text_surface.get_width() // 2 + 2, health_bar_y + health_bar_height // 2 - health_text_surface.get_height() // 2 + 2))
    screen.blit(health_text_surface, (health_bar_x + health_bar_width // 2 - health_text_surface.get_width() // 2, health_bar_y + health_bar_height // 2 - health_text_surface.get_height() // 2))

    # Rule 3: Screen Flash
    if screen_flash_timer > 0:
        flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        flash_surface.fill(RED_OVERLAY)
        screen.blit(flash_surface, (0, 0))
        screen_flash_timer -= clock.get_time()

    # Game Over Screen (Rule 5: UI Polish)
    if game_over:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180)) # Semi-transparent dark overlay
        screen.blit(overlay, (0, 0))

        game_over_text = large_font.render("GAME OVER!", True, NEON_PINK)
        game_over_shadow = large_font.render("GAME OVER!", True, DARK_BLUE_ACCENT)
        restart_text = medium_font.render("Press 'R' to Restart", True, NEON_CYAN)
        restart_shadow = medium_font.render("Press 'R' to Restart", True, DARK_BLUE_ACCENT)

        screen.blit(game_over_shadow, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2 + 3, SCREEN_HEIGHT // 2 - game_over_text.get_height() // 2 + 3))
        screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 2 - game_over_text.get_height() // 2))
        
        screen.blit(restart_shadow, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2 + 2, SCREEN_HEIGHT // 2 + 50 + 2))
        screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 50))


    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()