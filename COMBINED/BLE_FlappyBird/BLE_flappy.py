import pygame
import asyncio
from bleak import BleakClient
import threading
from pygame.locals import *
import random
import os
import struct
import sys  # Import sys module for sys.exit()
import datetime  # Import datetime for timestamping

pygame.init()

clock = pygame.time.Clock()
fps = 60

# Set up the display with specified size
screen_width = 1280
screen_height = 768
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Flappy Bird Runner')

# Define fonts
font = pygame.font.SysFont('Bauhaus 93', 40)
small_font = pygame.font.SysFont('Arial', 24)

# Define colours
white = (255, 255, 255)
black = (0, 0, 0)

# Define game variables
ground_scroll = 0
scroll_speed = 5
game_over = False
obstacle_frequency = 1500  # milliseconds
last_obstacle = pygame.time.get_ticks() - obstacle_frequency
score = 0
score_limit = None  # Will be set in settings_menu
save_feedback = ""  # Feedback message after saving

# Directories
base_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(base_dir)
profiles_dir = os.path.join(parent_dir, 'profiles')  # Adjusted to parent directory

# Create Profiles directory if it doesn't exist
if not os.path.exists(profiles_dir):
    os.makedirs(profiles_dir)

# Load images
bg = pygame.image.load(os.path.join(base_dir, 'img', 'bg.png')).convert()
bg = pygame.transform.scale(bg, (screen_width, screen_height))  # Scale background to fit screen
ground_img = pygame.image.load(os.path.join(base_dir, 'img', 'ground.png')).convert_alpha()
button_img = pygame.image.load(os.path.join(base_dir, 'img', 'restart.png')).convert_alpha()
save_button_img = pygame.image.load(os.path.join(base_dir, 'img', 'save.png')).convert_alpha()  # Load save button image

# Function for outputting text onto the screen
def draw_text(text, font, text_col, x, y, center=False):
    img = font.render(text, True, text_col)
    if center:
        rect = img.get_rect(center=(x, y))
        screen.blit(img, rect)
    else:
        screen.blit(img, (x, y))

def reset_game():
    obstacle_group.empty()
    flappy.rect.x = 100
    flappy.rect.bottom = ground_level
    global score, ground_scroll, game_over
    score = 0
    ground_scroll = 0
    game_over = False
    return score

class Bird(pygame.sprite.Sprite):

    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        self.index = 0
        self.counter = 0
        for num in range(1, 4):
            img = pygame.image.load(os.path.join(base_dir, 'img', f'bird{num}.png')).convert_alpha()
            img = pygame.transform.scale(img, (int(img.get_width() * 1.5), int(img.get_height() * 1.5)))  # Scale images
            self.images.append(img)
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.centery = y
        self.max_height = ground_level - 400  # Adjusted maximum height
        self.min_height = ground_level - 20   # Minimum height (just above the ground)
        self.max_force = 100  # Placeholder, will be updated after loading profile

    def update(self):
        if not game_over:
            # Read sensor value and map to vertical position
            sensor_value = ble_handler.get_value()
            if sensor_value is not None:
                # Clamp sensor value between 0 and max_force
                clamped_value = max(0, min(sensor_value, self.max_force))
                # Map sensor value to screen position
                normalized_value = clamped_value / self.max_force  # Value between 0 and 1
                self.rect.centery = self.min_height - normalized_value * (self.min_height - self.max_height)
            else:
                # If no sensor value, keep the bird at minimum height
                self.rect.centery = self.min_height

            # Animation
            self.counter += 1
            flap_cooldown = 5

            if self.counter > flap_cooldown:
                self.counter = 0
                self.index = (self.index + 1) % len(self.images)
                self.image = self.images[self.index]

        else:
            self.image = pygame.transform.rotate(self.images[self.index], -90)

class Obstacle(pygame.sprite.Sprite):

    def __init__(self, x, y, obstacle_height):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((40, obstacle_height))  # Increased obstacle width
        self.image.fill((255, 0, 0))  # Red color for obstacles
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.bottom = y

    def update(self):
        if not game_over:
            self.rect.x -= scroll_speed
        if self.rect.right < 0:
            self.kill()

class Button():
    def __init__(self, x, y, image):
        self.image = image
        self.image = pygame.transform.scale(self.image, (int(self.image.get_width() * 1.5), int(self.image.get_height() * 1.5)))  # Scale button image
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def draw(self):
        # Draw button
        screen.blit(self.image, (self.rect.x - self.image.get_width() // 2, self.rect.y - self.image.get_height() // 2))

class BLEHandler:
    def __init__(self, address, characteristic_uuid):
        self.address = address
        self.characteristic_uuid = characteristic_uuid
        self.loop = asyncio.new_event_loop()
        self.client = BleakClient(self.address, loop=self.loop)
        self.latest_value = None
        self.lock = threading.Lock()
        self.connected_event = threading.Event()

    def start(self):
        # Start the event loop in a separate thread
        threading.Thread(target=self.run_loop, daemon=True).start()
        # Wait for connection to be established
        self.connected_event.wait()

    def run_loop(self):
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.connect_and_listen())
        except asyncio.CancelledError:
            pass

    async def connect_and_listen(self):
        try:
            await self.client.connect()
            self.connected_event.set()
            await self.client.start_notify(self.characteristic_uuid, self.handle_notification)
            # Keep the loop running as long as the client is connected
            while self.client.is_connected:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"BLE connection error: {e}")
        finally:
            await self.disconnect()

    def handle_notification(self, sender, data):
        # Process the data and update latest_value
        try:
            # Assuming data is a 32-bit float
            value = struct.unpack('f', data)[0]
            with self.lock:
                self.latest_value = value
        except Exception as e:
            print(f"Error processing BLE notification: {e}")

    def get_value(self):
        with self.lock:
            return self.latest_value

    def stop(self):
        # Schedule disconnect on the event loop
        future = asyncio.run_coroutine_threadsafe(self.disconnect(), self.loop)
        try:
            future.result(timeout=5)
        except Exception as e:
            print(f"BLE disconnection error: {e}")
        finally:
            # Cancel all tasks and stop the loop
            pending = asyncio.all_tasks(self.loop)
            for task in pending:
                task.cancel()
            self.loop.stop()

    async def disconnect(self):
        try:
            await self.client.stop_notify(self.characteristic_uuid)
            await self.client.disconnect()
        except Exception as e:
            print(f"BLE disconnection error: {e}")

def settings_menu():
    menu = True
    obstacle_height_input = ''
    score_limit_input = ''
    error_message = ''
    active_field = 'profile_selection'  # Start with profile selection

    # Get list of profiles
    profiles = [name for name in os.listdir(profiles_dir) if os.path.isdir(os.path.join(profiles_dir, name))]
    if not profiles:
        print("No profiles found in the profiles directory.")
        pygame.quit()
        ble_handler.stop()
        sys.exit()

    selected_profile_index = 0  # Index of the selected profile
    player_id = profiles[selected_profile_index]  # Default selected player ID

    selected_stats_index = 0
    stats_files = []
    selected_stats_file = None

    while menu:
        screen.fill(black)
        draw_text('Flappy Bird Runner Settings', font, white, screen_width // 2, 50, center=True)

        y_offset = 120

        # Display profiles
        draw_text('Select Player Profile:', small_font, white, screen_width // 2, y_offset, center=True)
        y_offset += 30
        for i, profile in enumerate(profiles):
            if i == selected_profile_index:
                profile_color = (255, 255, 0)  # Yellow for selected profile
            else:
                profile_color = white
            draw_text(profile, small_font, profile_color, screen_width // 2, y_offset + i * 30, center=True)
        y_offset += len(profiles) * 30 + 20

        # If in stats file selection
        if active_field == 'stats_file_selection':
            draw_text('Select Statistics File:', small_font, white, screen_width // 2, y_offset, center=True)
            y_offset += 30
            for i, stats_file in enumerate(stats_files):
                display_name = stats_file
                if i == selected_stats_index:
                    stats_color = (255, 255, 0)
                else:
                    stats_color = white
                draw_text(display_name, small_font, stats_color, screen_width // 2, y_offset + i * 30, center=True)
            y_offset += len(stats_files) * 30 + 20
        else:
            y_offset += 20  # Add space if stats files are not displayed

        # Obstacle Height Input
        if active_field == 'obstacle_height':
            oh_color = (255, 255, 0)
        else:
            oh_color = white
        draw_text('Enter Obstacle Height (50-200):', small_font, white, screen_width // 2, y_offset, center=True)
        draw_text(obstacle_height_input, small_font, oh_color, screen_width // 2, y_offset + 30, center=True)

        y_offset += 70

        # Score Limit Input
        if active_field == 'score_limit':
            sl_color = (255, 255, 0)
        else:
            sl_color = white
        draw_text('Enter Score Limit (e.g., 10):', small_font, white, screen_width // 2, y_offset, center=True)
        draw_text(score_limit_input, small_font, sl_color, screen_width // 2, y_offset + 30, center=True)

        # Instructions
        instruction_y = y_offset + 70
        if active_field == 'profile_selection':
            draw_text('Use UP/DOWN to select profile, ENTER to confirm', small_font, white, screen_width // 2, instruction_y, center=True)
        elif active_field == 'stats_file_selection':
            draw_text('Use UP/DOWN to select stats file, ENTER to confirm', small_font, white, screen_width // 2, instruction_y, center=True)
        elif active_field in ['obstacle_height', 'score_limit']:
            draw_text('Enter value, PRESS ENTER to proceed', small_font, white, screen_width // 2, instruction_y, center=True)

        draw_text('Press TAB to switch fields', small_font, white, screen_width // 2, instruction_y + 30, center=True)

        if error_message:
            draw_text(error_message, small_font, (255, 0, 0), screen_width // 2, instruction_y + 60, center=True)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                ble_handler.stop()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    if active_field == 'profile_selection':
                        if stats_files:
                            active_field = 'stats_file_selection'
                        else:
                            active_field = 'obstacle_height'
                    elif active_field == 'stats_file_selection':
                        active_field = 'obstacle_height'
                    elif active_field == 'obstacle_height':
                        active_field = 'score_limit'
                    else:
                        active_field = 'profile_selection'
                elif active_field == 'profile_selection':
                    if event.key == pygame.K_UP:
                        selected_profile_index = (selected_profile_index - 1) % len(profiles)
                        player_id = profiles[selected_profile_index]
                        # Reset stats file selection
                        selected_stats_index = 0
                        selected_stats_file = None
                        stats_files = []
                    elif event.key == pygame.K_DOWN:
                        selected_profile_index = (selected_profile_index + 1) % len(profiles)
                        player_id = profiles[selected_profile_index]
                        # Reset stats file selection
                        selected_stats_index = 0
                        selected_stats_file = None
                        stats_files = []
                    elif event.key == pygame.K_RETURN:
                        # Load statistics files for the selected profile
                        player_dir = os.path.join(profiles_dir, player_id)
                        stats_files = [f for f in os.listdir(player_dir) if f.startswith('statistics') and f.endswith('.txt')]
                        if stats_files:
                            if len(stats_files) > 1:
                                active_field = 'stats_file_selection'
                            else:
                                selected_stats_file = stats_files[0]
                                active_field = 'obstacle_height'
                        else:
                            error_message = 'No statistics files found for this profile.'
                elif active_field == 'stats_file_selection':
                    if event.key == pygame.K_UP:
                        selected_stats_index = (selected_stats_index - 1) % len(stats_files)
                    elif event.key == pygame.K_DOWN:
                        selected_stats_index = (selected_stats_index + 1) % len(stats_files)
                    elif event.key == pygame.K_RETURN:
                        selected_stats_file = stats_files[selected_stats_index]
                        active_field = 'obstacle_height'
                elif active_field == 'obstacle_height':
                    if event.key == pygame.K_RETURN:
                        active_field = 'score_limit'
                    elif event.key == pygame.K_BACKSPACE:
                        obstacle_height_input = obstacle_height_input[:-1]
                    else:
                        if event.unicode.isdigit():
                            obstacle_height_input += event.unicode
                elif active_field == 'score_limit':
                    if event.key == pygame.K_RETURN:
                        if obstacle_height_input.isdigit() and score_limit_input.isdigit():
                            obstacle_height_value = int(obstacle_height_input)
                            score_limit_value = int(score_limit_input)
                            if 50 <= obstacle_height_value <= 200:
                                menu = False
                                obstacle_height = obstacle_height_value
                                score_limit = score_limit_value
                            else:
                                error_message = 'Obstacle height must be between 50 and 200.'
                        else:
                            error_message = 'Please enter valid inputs.'
                    elif event.key == pygame.K_BACKSPACE:
                        score_limit_input = score_limit_input[:-1]
                    else:
                        if event.unicode.isdigit():
                            score_limit_input += event.unicode

        pygame.display.update()
        clock.tick(30)

    return player_id, selected_stats_file, obstacle_height, score_limit

def load_profile(player_id, stats_file):
    # Load the specified statistics file for the player
    player_dir = os.path.join(profiles_dir, player_id)
    stats_path = os.path.join(player_dir, stats_file)

    max_force = None

    try:
        with open(stats_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                if line.startswith('Max Force:'):
                    max_force = float(line.split(':')[1].strip().split()[0])
    except FileNotFoundError:
        print(f"Statistics file '{stats_file}' not found for player '{player_id}'.")
        return None

    if max_force is None:
        print(f"Max Force not found in statistics file '{stats_file}' for player '{player_id}'.")
        return None

    return max_force

def save_game_data():
    global save_feedback
    # Prepare data to save
    data = {
        'Player ID': player_id,
        'Statistics File': stats_file,
        'Score': score,
        'Obstacle Height': obstacle_height,
        'Max Force': max_force,
        'Timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    # Create Scores directory within player's profile directory if it doesn't exist
    scores_dir = os.path.join(profiles_dir, player_id, 'Scores')
    if not os.path.exists(scores_dir):
        os.makedirs(scores_dir)
    # Generate filename with timestamp
    filename = f"score_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    filepath = os.path.join(scores_dir, filename)
    try:
        with open(filepath, 'w') as f:
            for key, value in data.items():
                f.write(f"{key}: {value}\n")
        save_feedback = "Game saved successfully."
    except Exception as e:
        save_feedback = f"Error saving game: {e}"

# Initialize the BLEHandler
BLE_DEVICE_ADDRESS = "96:18:FC:FA:30:FA"  # Replace with your BLE device's address
SENSOR_CHARACTERISTIC_UUID = "12345678-1234-5678-1234-56789abcdef1"  # Replace with your characteristic UUID
ble_handler = BLEHandler(BLE_DEVICE_ADDRESS, SENSOR_CHARACTERISTIC_UUID)
print("Connecting to BLE device...")
ble_handler.start()
print("Connected to BLE device.")

# Run the settings menu
player_id, stats_file, obstacle_height, score_limit = settings_menu()
max_force = load_profile(player_id, stats_file)

if max_force is None:
    print("Unable to load max force from profile. Exiting.")
    pygame.quit()
    ble_handler.stop()
    sys.exit()

# Ground level
ground_level = screen_height - 40

# Sprite groups
obstacle_group = pygame.sprite.Group()
bird_group = pygame.sprite.Group()

flappy = Bird(100, ground_level - 20)
flappy.max_force = max_force  # Update bird's max_force from profile
bird_group.add(flappy)

# Create button instances
button = Button(screen_width // 2 - 100, screen_height // 2, button_img)
save_button = Button(screen_width // 2 + 100, screen_height // 2, save_button_img)

run = True
while run:

    clock.tick(fps)

    # Draw background
    screen.blit(bg, (0, 0))

    # Draw and scroll the ground
    rel_ground_scroll = ground_scroll % ground_img.get_width()
    screen.blit(ground_img, (-rel_ground_scroll, ground_level - 20))
    if rel_ground_scroll < screen_width:
        screen.blit(ground_img, (-rel_ground_scroll + ground_img.get_width(), ground_level - 20))

    if not game_over:
        ground_scroll += scroll_speed

    # Update and draw sprite groups
    obstacle_group.update()
    obstacle_group.draw(screen)
    bird_group.update()
    bird_group.draw(screen)

    # Generate new obstacles
    time_now = pygame.time.get_ticks()
    if time_now - last_obstacle > obstacle_frequency and not game_over:
        obstacle = Obstacle(screen_width, ground_level, obstacle_height)
        obstacle_group.add(obstacle)
        last_obstacle = time_now

    # Check for collisions
    if pygame.sprite.spritecollide(flappy, obstacle_group, False):
        game_over = True

    # Update score
    if not game_over:
        for obstacle in obstacle_group:
            if obstacle.rect.right < flappy.rect.left and not hasattr(obstacle, 'passed'):
                obstacle.passed = True
                score += 1

    # Draw score at the top center
    draw_text(f'Score: {score}', font, white, screen_width // 2, 20, center=True)

    # Check if score limit reached
    if score_limit is not None and score >= score_limit:
        game_over = True

    if game_over:
        # Draw buttons
        button.draw()
        save_button.draw()
        # Display save feedback
        if save_feedback:
            draw_text(save_feedback, small_font, black, screen_width // 2, screen_height // 2 + 100, center=True)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if game_over:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if button.rect.collidepoint(event.pos):
                    # Reset the game
                    score = reset_game()
                    save_feedback = ""  # Reset save feedback
                elif save_button.rect.collidepoint(event.pos):
                    # Save game data
                    save_game_data()

    pygame.display.update()

pygame.quit()
print("Disconnecting from BLE device...")
ble_handler.stop()
print("Disconnected from BLE device.")
