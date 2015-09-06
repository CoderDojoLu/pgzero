from enum import Enum
import json
import math
import operator

from pygame.math import Vector2

from space import create_star_scape
from actors import Player, Asteroid

WIDTH = 800
HEIGHT = 600


class GameStage(Enum):
    start = 0
    game = 1
    level_complete = 2
    game_over = 3
    leader_board = 4


class GameState():
    stage = GameStage.start
    bullets = []
    asteroids = []
    initials = ''
    level = 1
    score = 0
    lives = 3
    player = None
    leader_board = {}


p = Player(pos=(WIDTH / 2, HEIGHT / 2))

life_pos = 10
life_icons = []
for _ in range(3):
    icon = Actor('player', topleft=(life_pos, 10))
    life_pos += 32
    life_icons.append(icon)

max_distance = min(WIDTH, HEIGHT) * .95
game = GameState()
game.player = p
stars = create_star_scape(WIDTH, HEIGHT)


def create_asteroids():
    game.asteroids = []
    for i in range(2 + game.level):
        game.asteroids.append(Asteroid(space=(WIDTH, HEIGHT)))


def make_vulnerable():
    game.player.invulnerable = False
    clock.unschedule(blink)
    game.player.show = True


def make_invulnerable():
    game.player.invulnerable = True
    clock.schedule_unique(make_vulnerable, 3.0)
    game.player.show = True
    clock.schedule_interval(blink, 0.3)


def update(dt):
    for asteroid in game.asteroids:
        asteroid.move(dt)

    for bullet in game.bullets:
        bullet.exact_pos = bullet.exact_pos - (bullet.velocity * dt)
        c = bullet.collidelist(game.asteroids)
        if c > -1:
            sounds.explosion2.play()
            game.bullets.remove(bullet)
            asteroid = game.asteroids.pop(c)
            game.score += 120.0 / asteroid.mass
            if asteroid.mass <= 1:
                if len(game.asteroids) == 0:
                    game.stage = GameStage.level_complete
                    clock.schedule(next_level, 3.0)
                    return
                continue
            else:
                for i in range(3):
                    a = Asteroid(parent=asteroid)
                    game.asteroids.append(a)
            continue
        if bullet.exact_pos.distance_to(bullet.start_pos) > max_distance:
            game.bullets.remove(bullet)
        bullet.pos = bullet.exact_pos.x % WIDTH, bullet.exact_pos.y % HEIGHT

    if game.stage is GameStage.game:
        if game.player.turn:
            game.player.angle += game.player.turn * dt * 270

        if game.player.thrust:
            ang = math.radians(game.player.angle)
            game.player.velocity += math.sin(ang) * game.player.speed, math.cos(ang) * game.player.speed
        else:
            game.player.velocity *= 0.99
        game.player.exact_pos = game.player.exact_pos - game.player.velocity
        game.player.exact_pos.x %= WIDTH
        game.player.exact_pos.y %= HEIGHT
        game.player.pos = game.player.exact_pos

        if game.lives and not game.player.invulnerable and game.player.collidelist(game.asteroids) > -1:
            sounds.explosion.play()
            game.lives -= 1
            game.player.pos = (WIDTH / 2, HEIGHT / 2)
            game.player.angle = 0
            game.player.velocity = Vector2()
            game.player.invulnerable = True
            game.player.thrust = False
            # rotate_player()
            game.player.exact_pos = game.player.pos
            make_invulnerable()

        if not game.lives:
            game.stage = GameStage.game_over

    if game.stage is GameStage.leader_board and not game.leader_board:
        with open('leaderboard.json', 'r') as lb:
            leader_board = json.load(lb) or []
        max_leaders = {}
        for initial, score in leader_board:
            max_leaders[initial] = max(score, max_leaders.get(initial, 0))
        game.leader_board['max_leaders'] = sorted(max_leaders.items(), key=operator.itemgetter(1), reverse=True)[:15]
        game.leader_board['leader_board'] = sorted(leader_board, key=operator.itemgetter(1), reverse=True)[:15]


def next_level():
    game.level += 1
    start_game(restart_game=False)


def blink():
    game.player.show = not game.player.show


def on_key_down(key):
    if game.stage is GameStage.start:
        if key == keys.SPACE:
            start_game()
    elif game.stage is GameStage.game:
        if key == keys.UP:
            game.player.thrust = True
        if key == keys.LEFT:
            game.player.turn += 1
        if key == keys.RIGHT:
            game.player.turn -= 1
        if key == keys.SPACE and game.lives:
            sounds.fire.play()
            game.bullets.append(game.player.fire())
    elif game.stage is GameStage.game_over:
        if key == keys.BACKSPACE:
            game.initials = game.initials[:-1]
        elif key == keys.RETURN and game.initials:
            with open('leaderboard.json', 'w+') as lb:
                try:
                    leader_board = json.load(lb)
                except ValueError:
                    leader_board = []
                leader_board.append((game.initials, game.score))
                json.dump(leader_board, lb)
            game.leader_board = {}
            game.stage = GameStage.leader_board
        elif len(game.initials) < 3 and keys.A <= key <= keys.Z:
            game.initials += chr(key).upper()
    elif game.stage is GameStage.leader_board:
        if key == keys.SPACE:
            game.stage = GameStage.start


def on_key_up(key):
    if game.stage is GameStage.game:
        if key == keys.UP:
            game.player.thrust = False
        if key == keys.LEFT:
            game.player.turn -= 1
        if key == keys.RIGHT:
            game.player.turn += 1


def start_game(restart_game=True):
    if restart_game:
        game.level = 1
        game.score = 0
        game.initials = ''
    create_asteroids()
    game.lives = 3
    game.player.thrust = False
    game.player.turn = 0
    game.player.angle = 0.0
    game.player.velocity = Vector2(0, 0)
    game.player.pos = (WIDTH / 2, HEIGHT / 2)
    game.player.exact_pos = Vector2(game.player.center)
    game.stage = GameStage.game
    make_invulnerable()


def draw():
    screen.clear()
    screen.blit(stars, (0, 0))
    if game.stage is GameStage.start:
        screen.draw.text('Press SPACE to start', center=(WIDTH / 2, HEIGHT / 2), color='white')
    elif game.stage is GameStage.game:
        if game.player.show:
            game.player.draw()
        for i in range(game.lives):
            life_icons[i].draw()
        screen.draw.text(str(round(game.score)), midtop=(WIDTH / 2, 10))
    elif game.stage is GameStage.level_complete:
        screen.draw.text('LEVEL %s COMPLETE!' % game.level, midbottom=(WIDTH / 2, HEIGHT / 2), fontsize=60)
        screen.draw.text(str(round(game.score)), midtop=(WIDTH / 2, 10))
        screen.draw.text('Next level in 3.. 2.. 1..', midtop=(WIDTH / 2, HEIGHT / 2))
    elif game.stage is GameStage.game_over:
        screen.draw.text('GAME OVER!', midbottom=(WIDTH / 2, HEIGHT / 2), fontsize=60)
        screen.draw.text(str(round(game.score)), midtop=(WIDTH / 2, 10))
        screen.draw.text('Enter Initials:', midtop=(WIDTH / 2, HEIGHT / 2))
        screen.draw.text(game.initials, midtop=(WIDTH / 2, (HEIGHT / 2) + 24))
    elif game.stage is GameStage.leader_board:
        top = 60
        screen.draw.text('High Scores', midtop=(WIDTH / 2, top), fontsize=40)
        top += 40
        max_top = top
        if game.leader_board:
            for initial, score in game.leader_board['leader_board']:
                screen.draw.text('%s %s' % (initial, round(score)), midtop=((WIDTH / 2) - 60, top))
                top += 24

            for initial, score in game.leader_board['max_leaders']:
                screen.draw.text('%s %s' % (initial, round(score)), midtop=((WIDTH / 2) + 60, max_top))
                max_top += 24

        screen.draw.text('Press SPACE to restart', midtop=(WIDTH / 2, top + 40))

    for bullet in game.bullets:
        bullet.draw()
    for asteroid in game.asteroids:
        asteroid.draw()

