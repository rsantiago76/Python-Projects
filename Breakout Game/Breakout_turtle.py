import turtle as t
import random
import math

# -------------------- CONFIG --------------------
WIDTH, HEIGHT = 900, 650
TOP_WALL = HEIGHT // 2 - 30
BOTTOM_WALL = -HEIGHT // 2 + 30

PADDLE_Y = BOTTOM_WALL + 45
PADDLE_W, PADDLE_H = 120, 18
PADDLE_SPEED = 30

BALL_SIZE = 12
BALL_SPEED_START = 6.0
BALL_SPEED_MAX = 14.0

BRICK_COLS = 10
BRICK_ROWS = 6
BRICK_W, BRICK_H = 78, 24
BRICK_GAP_X, BRICK_GAP_Y = 10, 10
BRICK_TOP_MARGIN = 70

LIVES_START = 3

# -------------------- HELPERS --------------------
def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def aabb_collide(ax, ay, aw, ah, bx, by, bw, bh) -> bool:
    """Axis-aligned bounding box collision."""
    return (abs(ax - bx) * 2 < (aw + bw)) and (abs(ay - by) * 2 < (ah + bh))

# -------------------- GAME OBJECTS --------------------
class Paddle(t.Turtle):
    def __init__(self):
        super().__init__(visible=False)
        self.penup()
        self.shape("square")
        self.color("white")
        self.shapesize(stretch_wid=PADDLE_H / 20, stretch_len=PADDLE_W / 20)
        self.goto(0, PADDLE_Y)
        self.showturtle()

    def move_left(self):
        x = self.xcor() - PADDLE_SPEED
        limit = WIDTH // 2 - PADDLE_W // 2 - 12
        self.setx(clamp(x, -limit, limit))

    def move_right(self):
        x = self.xcor() + PADDLE_SPEED
        limit = WIDTH // 2 - PADDLE_W // 2 - 12
        self.setx(clamp(x, -limit, limit))

class Ball(t.Turtle):
    def __init__(self):
        super().__init__(visible=False)
        self.penup()
        self.shape("circle")
        self.color("white")
        self.shapesize(stretch_wid=BALL_SIZE / 20, stretch_len=BALL_SIZE / 20)
        self.dx = 0.0
        self.dy = 0.0
        self.speed_mag = BALL_SPEED_START
        self.stuck = True  # stuck to paddle until launch
        self.showturtle()

    def reset_to_paddle(self, paddle: Paddle):
        self.stuck = True
        self.speed_mag = BALL_SPEED_START
        self.dx = 0.0
        self.dy = 0.0
        self.goto(paddle.xcor(), paddle.ycor() + 20)

    def launch(self):
        if not self.stuck:
            return
        self.stuck = False
        angle = random.uniform(35, 145)  # degrees
        rad = math.radians(angle)
        self.dx = math.cos(rad) * self.speed_mag
        self.dy = math.sin(rad) * self.speed_mag

    def update(self):
        if self.stuck:
            return
        self.goto(self.xcor() + self.dx, self.ycor() + self.dy)

    def speed_up(self, amount=0.25):
        self.speed_mag = min(BALL_SPEED_MAX, self.speed_mag + amount)
        # Re-normalize dx/dy to new speed, preserving direction
        mag = math.hypot(self.dx, self.dy)
        if mag > 0:
            self.dx = (self.dx / mag) * self.speed_mag
            self.dy = (self.dy / mag) * self.speed_mag

class Brick(t.Turtle):
    def __init__(self, x, y, color):
        super().__init__(visible=False)
        self.penup()
        self.shape("square")
        self.color(color)
        self.shapesize(stretch_wid=BRICK_H / 20, stretch_len=BRICK_W / 20)
        self.goto(x, y)
        self.showturtle()

class HUD(t.Turtle):
    def __init__(self):
        super().__init__(visible=False)
        self.penup()
        self.color("white")
        self.goto(-WIDTH//2 + 20, HEIGHT//2 - 45)
        self.score = 0
        self.lives = LIVES_START
        self.level = 1
        self._msg = ""
        self.draw()

    def draw(self, extra=""):
        self.clear()
        txt = f"Score: {self.score}   Lives: {self.lives}   Level: {self.level}"
        self.write(txt, font=("Courier", 16, "bold"))
        if extra:
            m = t.Turtle(visible=False)
            m.penup()
            m.color("white")
            m.goto(0, 0)
            m.write(extra, align="center", font=("Courier", 20, "bold"))

# -------------------- GAME --------------------
class BreakoutGame:
    def __init__(self):
        self.screen = t.Screen()
        self.screen.title("Breakout (Turtle)")
        self.screen.bgcolor("black")
        self.screen.setup(WIDTH, HEIGHT)
        self.screen.tracer(0)

        self.border = t.Turtle(visible=False)
        self.border.penup()
        self.border.color("white")

        self.paddle = Paddle()
        self.ball = Ball()
        self.hud = HUD()
        self.bricks = []

        self.running = True
        self.game_over = False

        self._bind_keys()
        self.reset_round(full_reset=True)

    def _bind_keys(self):
        self.screen.listen()
        self.screen.onkeypress(self.paddle.move_left, "Left")
        self.screen.onkeypress(self.paddle.move_right, "Right")
        self.screen.onkeypress(self.ball.launch, "space")
        self.screen.onkeypress(self.restart, "r")
        self.screen.onkeypress(self.restart, "R")

    def draw_border(self):
        self.border.clear()
        self.border.goto(-WIDTH//2 + 15, TOP_WALL)
        self.border.pendown()
        self.border.goto(WIDTH//2 - 15, TOP_WALL)
        self.border.penup()

        # Side walls (visual only)
        self.border.goto(-WIDTH//2 + 15, TOP_WALL)
        self.border.pendown()
        self.border.goto(-WIDTH//2 + 15, BOTTOM_WALL)
        self.border.penup()
        self.border.goto(WIDTH//2 - 15, TOP_WALL)
        self.border.pendown()
        self.border.goto(WIDTH//2 - 15, BOTTOM_WALL)
        self.border.penup()

    def build_bricks(self):
        for b in self.bricks:
            b.hideturtle()
        self.bricks.clear()

        colors = ["#ff4d4d", "#ff944d", "#ffd24d", "#b3ff66", "#4dd2ff", "#b366ff"]
        start_x = -(BRICK_COLS * BRICK_W + (BRICK_COLS - 1) * BRICK_GAP_X) / 2 + BRICK_W / 2
        start_y = TOP_WALL - BRICK_TOP_MARGIN

        for r in range(BRICK_ROWS):
            y = start_y - r * (BRICK_H + BRICK_GAP_Y)
            for c in range(BRICK_COLS):
                x = start_x + c * (BRICK_W + BRICK_GAP_X)
                brick = Brick(x, y, colors[r % len(colors)])
                self.bricks.append(brick)

    def reset_round(self, full_reset=False):
        self.draw_border()
        if full_reset:
            self.hud.score = 0
            self.hud.lives = LIVES_START
            self.hud.level = 1

        self.build_bricks()
        self.paddle.goto(0, PADDLE_Y)
        self.ball.reset_to_paddle(self.paddle)
        self.game_over = False
        self.hud.draw()

    def next_level(self):
        self.hud.level += 1
        # Slightly increase starting speed each level
        global BALL_SPEED_START
        BALL_SPEED_START = min(10.0, BALL_SPEED_START + 0.5)
        self.build_bricks()
        self.ball.reset_to_paddle(self.paddle)
        self.hud.draw(extra=f"LEVEL {self.hud.level}")

    def restart(self):
        # Reset global start speed to default on restart
        global BALL_SPEED_START
        BALL_SPEED_START = 6.0
        self.reset_round(full_reset=True)

    def paddle_ball_collision(self):
        if self.ball.stuck:
            # keep ball glued to paddle x position
            self.ball.setx(self.paddle.xcor())
            self.ball.sety(self.paddle.ycor() + 20)
            return

        # Ball vs Paddle (AABB)
        if aabb_collide(
            self.ball.xcor(), self.ball.ycor(), BALL_SIZE, BALL_SIZE,
            self.paddle.xcor(), self.paddle.ycor(), PADDLE_W, PADDLE_H
        ) and self.ball.dy < 0:
            # Compute bounce angle based on hit position
            offset = (self.ball.xcor() - self.paddle.xcor()) / (PADDLE_W / 2)
            offset = clamp(offset, -1.0, 1.0)

            # Angle range: 30° to 150° (upward)
            angle = 90 + offset * 60
            rad = math.radians(angle)

            self.ball.dx = math.cos(rad) * self.ball.speed_mag
            self.ball.dy = abs(math.sin(rad) * self.ball.speed_mag)

            self.ball.speed_up(0.15)

            # Nudge ball up to avoid "sticking"
            self.ball.sety(self.paddle.ycor() + 28)

    def wall_collisions(self):
        if self.ball.stuck:
            return

        x, y = self.ball.xcor(), self.ball.ycor()
        half_w = WIDTH // 2 - 15
        # Side walls
        if x >= half_w - BALL_SIZE and self.ball.dx > 0:
            self.ball.dx *= -1
            self.ball.setx(half_w - BALL_SIZE)
        elif x <= -half_w + BALL_SIZE and self.ball.dx < 0:
            self.ball.dx *= -1
            self.ball.setx(-half_w + BALL_SIZE)

        # Top wall
        if y >= TOP_WALL - BALL_SIZE and self.ball.dy > 0:
            self.ball.dy *= -1
            self.ball.sety(TOP_WALL - BALL_SIZE)

        # Bottom (life lost)
        if y <= BOTTOM_WALL - 60:
            self.hud.lives -= 1
            if self.hud.lives <= 0:
                self.game_over = True
                self.hud.draw(extra="GAME OVER\nPress R to Restart")
            else:
                self.hud.draw(extra=f"Life Lost! ({self.hud.lives} left)\nPress Space")
                self.ball.reset_to_paddle(self.paddle)

    def brick_collisions(self):
        if self.ball.stuck:
            return

        bx, by = self.ball.xcor(), self.ball.ycor()
        for brick in self.bricks:
            if not brick.isvisible():
                continue
            if aabb_collide(
                bx, by, BALL_SIZE, BALL_SIZE,
                brick.xcor(), brick.ycor(), BRICK_W, BRICK_H
            ):
                # Decide bounce direction based on overlap
                dx = bx - brick.xcor()
                dy = by - brick.ycor()
                overlap_x = (BRICK_W / 2 + BALL_SIZE / 2) - abs(dx)
                overlap_y = (BRICK_H / 2 + BALL_SIZE / 2) - abs(dy)

                if overlap_x < overlap_y:
                    self.ball.dx *= -1
                else:
                    self.ball.dy *= -1

                brick.hideturtle()
                self.hud.score += 10
                self.ball.speed_up(0.05)
                self.hud.draw()

                break

        # Level complete
        if all(not b.isvisible() for b in self.bricks):
            self.next_level()

    def tick(self):
        if self.game_over:
            self.screen.update()
            self.screen.ontimer(self.tick, 16)
            return

        # Move ball
        self.ball.update()

        # Collisions
        self.paddle_ball_collision()
        self.wall_collisions()
        self.brick_collisions()

        self.screen.update()
        self.screen.ontimer(self.tick, 16)  # ~60 FPS

    def run(self):
        self.tick()
        self.screen.mainloop()

# -------------------- MAIN --------------------
if __name__ == "__main__":
    BreakoutGame().run()