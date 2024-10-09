import pygame
import asyncio
from bleak import BleakClient
import threading
from pygame.locals import *
import random
import os
import struct

# Get the directory where flappy.py is located
base_dir = os.path.dirname(os.path.abspath(__file__))

pygame.init()

clock = pygame.time.Clock()
fps = 60
sensor_threshold = 5
screen_width = 864
screen_height = 936

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Flappy Bird')

# Define font
font = pygame.font.SysFont('Bauhaus 93', 60)

# Define colours
white = (255, 255, 255)

# Define game variables
ground_scroll = 0
scroll_speed = 4
flying = False
game_over = False
pipe_gap = 160
pipe_frequency = 1500  # milliseconds
last_pipe = pygame.time.get_ticks() - pipe_frequency
score = 0
pass_pipe = False

# Load images with the correct paths relative to flappy.py
bg = pygame.image.load(os.path.join(base_dir, 'img', 'bg.png'))
ground_img = pygame.image.load(os.path.join(base_dir, 'img', 'ground.png'))
button_img = pygame.image.load(os.path.join(base_dir, 'img', 'restart.png'))

# Function for outputting text onto the screen
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

def reset_game():
    pipe_group.empty()
    flappy.rect.x = 100
    flappy.rect.y = int(screen_height / 2)
    score = 0
    return score

class Bird(pygame.sprite.Sprite):

    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        self.index = 0
        self.counter = 0
        # Load bird images relative to base_dir
        for num in range(1, 4):
            img = pygame.image.load(os.path.join(base_dir, 'img', f'bird{num}.png'))
            self.images.append(img)
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.vel = 0
        self.clicked = False

    def update(self):

        if flying:
            # Apply gravity
            self.vel += 0.5
            if self.vel > 8:
                self.vel = 8
            if self.rect.bottom < 768:
                self.rect.y += int(self.vel)

        if not game_over:
            # Instead of mouse input, use sensor to trigger jump
            sensor_value = ble_handler.get_value()
            if sensor_value is not None:
                if sensor_value > sensor_threshold and not self.clicked:
                    self.clicked = True
                    self.vel = -10
                if sensor_value <= sensor_threshold:
                    self.clicked = False

            # Handle the animation
            flap_cooldown = 5
            self.counter += 1

            if self.counter > flap_cooldown:
                self.counter = 0
                self.index += 1
                if self.index >= len(self.images):
                    self.index = 0
                self.image = self.images[self.index]

            # Rotate the bird
            self.image = pygame.transform.rotate(self.images[self.index], self.vel * -2)
        else:
            # Point the bird at the ground
            self.image = pygame.transform.rotate(self.images[self.index], -90)

class Pipe(pygame.sprite.Sprite):

    def __init__(self, x, y, position):
        pygame.sprite.Sprite.__init__(self)
        # Load pipe image relative to base_dir
        self.image = pygame.image.load(os.path.join(base_dir, 'img', 'pipe.png'))
        self.rect = self.image.get_rect()
        # Position variable determines if the pipe is coming from the bottom or top
        if position == 1:
            self.image = pygame.transform.flip(self.image, False, True)
            self.rect.bottomleft = [x, y - int(pipe_gap / 2)]
        elif position == -1:
            self.rect.topleft = [x, y + int(pipe_gap / 2)]

    def update(self):
        self.rect.x -= scroll_speed
        if self.rect.right < 0:
            self.kill()

class Button():
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

    def draw(self):
        action = False

        # Get mouse position
        pos = pygame.mouse.get_pos()

        # Check mouseover and clicked conditions
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1:
                action = True

        # Draw button
        screen.blit(self.image, (self.rect.x, self.rect.y))

        return action

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
        self.loop.run_until_complete(self.connect_and_listen())

    async def connect_and_listen(self):
        try:
            await self.client.connect()
            self.connected_event.set()
            await self.client.start_notify(self.characteristic_uuid, self.handle_notification)
            # Keep the loop running as long as the client is connected
            while self.client.is_connected:
                await asyncio.sleep(1)
        except Exception as e:
            print(f"BLE connection error: {e}")

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

    async def disconnect(self):
        try:
            await self.client.stop_notify(self.characteristic_uuid)
            await self.client.disconnect()
        except Exception as e:
            print(f"BLE disconnection error: {e}")
        finally:
            self.loop.stop()

pipe_group = pygame.sprite.Group()
bird_group = pygame.sprite.Group()

flappy = Bird(100, int(screen_height / 2))

bird_group.add(flappy)

# Create restart button instance
button = Button(screen_width // 2 - 50, screen_height // 2 - 100, button_img)

# Initialize the BLEHandler
BLE_DEVICE_ADDRESS = "96:18:FC:FA:30:FA"  # Replace with your BLE device's address
SENSOR_CHARACTERISTIC_UUID = "12345678-1234-5678-1234-56789abcdef1"  # Replace with your characteristic UUID
ble_handler = BLEHandler(BLE_DEVICE_ADDRESS, SENSOR_CHARACTERISTIC_UUID)
print("Connecting to BLE device...")
ble_handler.start()
print("Connected to BLE device.")

run = True
while run:

    clock.tick(fps)

    # Draw background
    screen.blit(bg, (0, 0))

    pipe_group.draw(screen)
    bird_group.draw(screen)
    bird_group.update()

    # Draw and scroll the ground
    screen.blit(ground_img, (ground_scroll, 768))

    # Check the score
    if len(pipe_group) > 0:
        if bird_group.sprites()[0].rect.left > pipe_group.sprites()[0].rect.left \
                and bird_group.sprites()[0].rect.right < pipe_group.sprites()[0].rect.right \
                and not pass_pipe:
            pass_pipe = True
        if pass_pipe:
            if bird_group.sprites()[0].rect.left > pipe_group.sprites()[0].rect.right:
                score += 1
                pass_pipe = False
    draw_text(str(score), font, white, int(screen_width / 2), 20)

    # Look for collision
    if pygame.sprite.groupcollide(bird_group, pipe_group, False, False) or flappy.rect.top < 0:
        game_over = True
    # Once the bird has hit the ground it's game over and no longer flying
    if flappy.rect.bottom >= 768:
        game_over = True
        flying = False

    if flying and not game_over:
        # Generate new pipes
        time_now = pygame.time.get_ticks()
        if time_now - last_pipe > pipe_frequency:
            pipe_height = random.randint(-100, 100)
            btm_pipe = Pipe(screen_width, int(screen_height / 2) + pipe_height, -1)
            top_pipe = Pipe(screen_width, int(screen_height / 2) + pipe_height, 1)
            pipe_group.add(btm_pipe)
            pipe_group.add(top_pipe)
            last_pipe = time_now

        pipe_group.update()

        ground_scroll -= scroll_speed
        if abs(ground_scroll) > 35:
            ground_scroll = 0

    # Check for game over and reset
    if game_over:
        if button.draw():
            game_over = False
            score = reset_game()

    # Check if the force sensor should start the game
    if not flying and not game_over:
        sensor_value = ble_handler.get_value()
        if sensor_value is not None:
            # If the sensor value crosses the threshold, start the game
            if sensor_value > sensor_threshold:
                flying = True

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    pygame.display.update()

pygame.quit()
print("Disconnecting from BLE device...")
ble_handler.stop()
print("Disconnected from BLE device.")
