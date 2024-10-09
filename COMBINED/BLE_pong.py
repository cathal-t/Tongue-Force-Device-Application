import pygame
import asyncio
from bleak import BleakClient
import threading
import struct

# Initialize Pygame
pygame.init()

WIDTH, HEIGHT = 1200, 900
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong")

FPS = 90

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

PADDLE_WIDTH, PADDLE_HEIGHT = 20, 200
BALL_RADIUS = 7

SCORE_FONT = pygame.font.SysFont("comicsans", 50)
WINNING_SCORE = 10

class Paddle:
    COLOR = WHITE
    VEL = 6

    def __init__(self, x, y, width, height):
        self.x = self.original_x = x
        self.y = self.original_y = y
        self.width = width
        self.height = height

    def draw(self, win):
        pygame.draw.rect(
            win, self.COLOR, (int(self.x), int(self.y), self.width, self.height))

    def move(self, vel):
        self.y += vel

    def reset(self):
        self.x = self.original_x
        self.y = self.original_y

class Ball:
    MAX_VEL = 5
    COLOR = WHITE

    def __init__(self, x, y, radius):
        self.x = self.original_x = x
        self.y = self.original_y = y
        self.radius = radius
        self.x_vel = self.MAX_VEL
        self.y_vel = 0

    def draw(self, win):
        pygame.draw.circle(win, self.COLOR, (int(self.x), int(self.y)), self.radius)

    def move(self):
        self.x += self.x_vel
        self.y += self.y_vel

    def reset(self):
        self.x = self.original_x
        self.y = self.original_y
        self.y_vel = 0
        self.x_vel *= -1

def draw(win, paddles, ball, left_score, right_score):
    win.fill(BLACK)

    left_score_text = SCORE_FONT.render(f"{left_score}", 1, WHITE)
    right_score_text = SCORE_FONT.render(f"{right_score}", 1, WHITE)
    win.blit(left_score_text, (WIDTH//4 - left_score_text.get_width()//2, 20))
    win.blit(right_score_text, (WIDTH * (3/4) -
                                right_score_text.get_width()//2, 20))

    for paddle in paddles:
        paddle.draw(win)

    for i in range(10, HEIGHT, HEIGHT//20):
        if i % 2 == 1:
            continue
        pygame.draw.rect(win, WHITE, (WIDTH//2 - 5, i, 10, HEIGHT//20))

    ball.draw(win)
    pygame.display.update()

def handle_collision(ball, left_paddle, right_paddle):
    if ball.y + ball.radius >= HEIGHT:
        ball.y_vel *= -1
    elif ball.y - ball.radius <= 0:
        ball.y_vel *= -1

    if ball.x_vel < 0:
        if left_paddle.y <= ball.y <= left_paddle.y + left_paddle.height:
            if ball.x - ball.radius <= left_paddle.x + left_paddle.width:
                ball.x_vel *= -1

                middle_y = left_paddle.y + left_paddle.height / 2
                difference_in_y = middle_y - ball.y
                reduction_factor = (left_paddle.height / 2) / ball.MAX_VEL
                y_vel = difference_in_y / reduction_factor
                ball.y_vel = -1 * y_vel

    else:
        if right_paddle.y <= ball.y <= right_paddle.y + right_paddle.height:
            if ball.x + ball.radius >= right_paddle.x:
                ball.x_vel *= -1

                middle_y = right_paddle.y + right_paddle.height / 2
                difference_in_y = middle_y - ball.y
                reduction_factor = (right_paddle.height / 2) / ball.MAX_VEL
                y_vel = difference_in_y / reduction_factor
                ball.y_vel = -1 * y_vel

def handle_left_paddle_movement(sensor_value, left_paddle):
    # Adjust the following values based on your sensor's output range
    max_sensor_value = 60  # For analogRead from Arduino (0-1023)
    mid_value = max_sensor_value / 2

    # Dead zone to prevent paddle jitter
    dead_zone = 5  # Adjust as needed

    # Calculate velocity based on sensor input
    if sensor_value > mid_value + dead_zone:
        velocity = left_paddle.VEL
    elif sensor_value < mid_value - dead_zone:
        velocity = -left_paddle.VEL
    else:
        velocity = 0

    # Move paddle
    if 0 <= left_paddle.y + velocity <= HEIGHT - left_paddle.height:
        left_paddle.move(velocity)

def handle_right_paddle_ai(ball, right_paddle):
    # Simple AI that moves the right paddle based on the ball's y position
    if ball.y < right_paddle.y + right_paddle.height / 2 and right_paddle.y - right_paddle.VEL >= 0:
        right_paddle.move(-right_paddle.VEL)
    elif ball.y > right_paddle.y + right_paddle.height / 2 and right_paddle.y + right_paddle.VEL + right_paddle.height <= HEIGHT:
        right_paddle.move(right_paddle.VEL)

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

def main():
    run = True
    clock = pygame.time.Clock()

    # Initialize the BLEHandler
    BLE_DEVICE_ADDRESS = "96:18:FC:FA:30:FA"  # Replace with your device's address
    SENSOR_CHARACTERISTIC_UUID = "12345678-1234-5678-1234-56789abcdef1"  # Replace with your characteristic UUID
    ble_handler = BLEHandler(BLE_DEVICE_ADDRESS, SENSOR_CHARACTERISTIC_UUID)
    print("Connecting to BLE device...")
    ble_handler.start()
    print("Connected to BLE device.")

    left_paddle = Paddle(10, HEIGHT//2 - PADDLE_HEIGHT //
                         2, PADDLE_WIDTH, PADDLE_HEIGHT)
    right_paddle = Paddle(WIDTH - 10 - PADDLE_WIDTH, HEIGHT //
                          2 - PADDLE_HEIGHT//2, PADDLE_WIDTH, PADDLE_HEIGHT)
    ball = Ball(WIDTH // 2, HEIGHT // 2, BALL_RADIUS)

    left_score = 0
    right_score = 0

    while run:
        clock.tick(FPS)
        draw(WIN, [left_paddle, right_paddle], ball, left_score, right_score)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

        # Read sensor data from BLE
        sensor_value = ble_handler.get_value()
        if sensor_value is not None:
            handle_left_paddle_movement(sensor_value, left_paddle)

        # Control right paddle with AI
        handle_right_paddle_ai(ball, right_paddle)

        ball.move()
        handle_collision(ball, left_paddle, right_paddle)

        if ball.x < 0:
            right_score += 1
            ball.reset()
        elif ball.x > WIDTH:
            left_score += 1
            ball.reset()

        won = False
        if left_score >= WINNING_SCORE:
            won = True
            win_text = "Left Player Won!"
        elif right_score >= WINNING_SCORE:
            won = True
            win_text = "Right Player Won!"

        if won:
            text = SCORE_FONT.render(win_text, 1, WHITE)
            WIN.blit(text, (WIDTH//2 - text.get_width() //
                            2, HEIGHT//2 - text.get_height()//2))
            pygame.display.update()
            pygame.time.delay(5000)
            ball.reset()
            left_paddle.reset()
            right_paddle.reset()
            left_score = 0
            right_score = 0

    pygame.quit()
    print("Disconnecting from BLE device...")
    ble_handler.stop()
    print("Disconnected from BLE device.")

if __name__ == '__main__':
    main()
