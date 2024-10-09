import pygame
from communication_handler import CommunicationHandler  # Import the communication handler

# Initialize Pygame
pygame.init()

WIDTH, HEIGHT = 1200, 900
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong")

FPS = 60

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
            win, self.COLOR, (self.x, self.y, self.width, self.height))

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
    max_sensor_value = 1023  # For analogRead from Arduino (0-1023)
    mid_value = max_sensor_value // 2

    # Calculate velocity based on sensor input
    dead_zone = 50  # Adjust dead zone as needed
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

def main():
    run = True
    clock = pygame.time.Clock()

    # Initialize the communication handler
    MODE = 'BLE'  # Set to 'BLE' or 'SERIAL'
    comm_handler = CommunicationHandler(mode=MODE)
    if MODE == 'SERIAL':
        comm_handler.serial_port = 'COM6'  # Replace with your serial port
        comm_handler.baudrate = 9600
    elif MODE == 'BLE':
        comm_handler.device_address = '96:18:FC:FA:30:FA'  # Replace with your BLE device address
        comm_handler.ble_characteristic_uuid = '12345678-1234-5678-1234-56789abcdef1'  # Replace with your characteristic UUID

    comm_handler.start()  # Start reading data

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

        # Read sensor data from comm_handler
        sensor_value = comm_handler.get_sensor_value()
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
    comm_handler.stop()  # Stop reading data when quitting the game

if __name__ == '__main__':
    main()
