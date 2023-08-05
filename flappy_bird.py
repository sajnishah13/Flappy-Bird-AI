import pygame
import neat
import time
import os
import random

pygame.font.init()

# CONSTANTS for window width and height
WIN_WIDTH = 500
WIN_HEIGHT = 800

# import images of birds and scale so 2x bigger
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(
    os.path.join("imgs", "bird1.png"))),
    pygame.transform.scale2x(pygame.image.load(
        os.path.join("imgs", "bird2.png"))),
    pygame.transform.scale2x(pygame.image.load(
        os.path.join("imgs", "bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(
    os.path.join("imgs", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(
    os.path.join("imgs", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(
    os.path.join("imgs", "bg.png")))

STAT_FONT = pygame.font.SysFont("comicsans", 50)



class Bird:
    """bird class representing the flappy bird"""
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25  # how much the bird tilts
    ROT_VEL = 20  # how much we are going to rotate bird in each frame
    ANIMATION_TIME = 5  # how long we shoe each bird animation

    def __init__(self, x, y):
        """
        Initialize the object
        :param x: starting x pos (int)
        :param y: starting y pos (int)
        :return: None
        """
        self.x = x
        self.y = y
        # how much bird is tilted - starts off as 0
        self.tilt = 0
        # physics of bird
        self.tick_count = 0
        # velocity of bird
        self.vel = 0
        # height of bird
        self.height = self.y
        # what image we are showing for bird
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        """
        make the bird jump
        :return: None
        """
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y  # where bird originally jumped from

    def move(self):
        """
        make the bird move
        :return: None
        """
        self.tick_count += 1  # tracks how many moves since last jump
        d = self.vel * self.tick_count + 1.5 *(self.tick_count)** 2  # how many pixels moved up or down each frame

        # terminal velocity
        if d >= 16:
            d = (d/abs(d))*16

        if d < 0:
            d -= 2

        self.y = self.y + d

        # once bird reaches the original jump point on downfall or when moving up, change direction of tilt
        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL  # looks like nose diving on downfall - tilt down

    def draw(self, win):
        """
        draw the bird
        :param win: pygame window or surface
        :return: None
        """
        # to animate a bird, need to keep track of how many times we have shown a tick for
        self.img_count += 1

        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        # when a bird is nosediving it shouldnt be flapping
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME * 2

        # tilt the bird
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
        """
        gets the mask for the current image of the bird
        :return: mask
        """
        return pygame.mask.from_surface(self.img)


class Pipe:
    """
    represents a pipe object
    """
    GAP = 200  # space inbetween pipes
    VEL = 5  # how fast the pipes move

    def __init__(self, x):
        """
        initialise pipe object
        :param x: int
        :return: None
        """
        self.x = x
        self.height = 0
        self.gap = 100

        # where top and bottom of the pipe is
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False  # for collision detection
        self.set_height()

    def set_height(self):
        """
        set the height of the pipe, from the top of the screen
        :return: None
        """
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        """
        Move pipe based on vel
        :return: None
        """
        self.x -= self.VEL

    def draw(self, win):
        """
        draw both top and bottom of the pipe
        :param win: pygame window / surface
        :return: None
        """
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    # pixel perfect collision
    def collide(self, bird):
        """
        returns if a point is colliding with the pipe
        :param bird: Bird object
        :return: Bool
        """
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        # work with the top left corners of all masks
        top_offset = (self.x - bird.x, self.top - round(bird.y))  # how far the masks are from each other
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)  # point of overlap bettwen bird and bottom pipe
        # if they do not collide, function returns None
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point:
            # collision happened
            return True
        return False


class Base:
    """
    represents the moving floor of the game
    """
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        """
        Initialize the object
        :param y: int
        :return: None
        """
        self.y = y
        # 2 x positions, one on screen and one directly behind
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        """
        move the base images with the velocity at the same time
        :return: None
        """
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        # check if x1 image is off the screen completely
        if self.x1 + self.WIDTH < 0:
            # if off the screen, cycle the image back around behind the other image
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        """
        Draw the floor. This is 2 images that move together
        :param win: the pygame surface/window
        :return: None
        """
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def draw_window(win, birds, pipes, base, score):
    """
    draws the windows for the main game loop
    :param win: pygame window surface
    :param birds: List of bird objects
    :param pipes: List of pipes
    :param base: Base object
    :param score: score of the game (int)
    :return: None
    """
    win.blit(BG_IMG, (0, 0))
    for pipe in pipes:
        pipe.draw(win)

    text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))
    base.draw(win)
    for bird in birds:
        bird.draw(win)
    pygame.display.update()


def main(genomes, config):
    """
    runs the simulation of the current population of birds and sets their fitness based on the distance they reach in the game
    :param genomes:
    :param config:
    :return:
    """

    # create lists holding teh genome itself, the neural network associated with the genome and the distance they reach in the game
    nets = []
    ge = []
    birds = []

    # setting up neural network for genomes
    for _, g in genomes:
        g.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        ge.append(g)

    base = Base(730)
    pipes = [Pipe(600)]
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

    score = 0

    # setting the tick rate for how fast the while loop is running so it is at a consistent rate
    clock = pygame.time.Clock()

    run = True
    while run and len(birds) > 0:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > birds[0].x + pipes[0].PIPE_TOP.get_width():  # determine whether to use the first or second
                pipe_ind = 1                                                                # pipe on the screen for neural network input

        for x, bird in enumerate(birds):  # give each bird a fitness of 0.1 for each frame it stays alive
            ge[x].fitness += 0.1
            bird.move()
            output = nets[birds.index(bird)].activate(
                (bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))
            if output[0] > 0.5:
                bird.jump()

        rem = []
        add_pipe = False
        for pipe in pipes:
            pipe.move()
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    ge[x].fitness -= 1  # when bird hits pipe, decrements fitness score
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)

            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:  # if pipe off the screen
                rem.append(pipe)


        if add_pipe:
            score += 1
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(600))

        for r in rem:
            pipes.remove(r)
            
        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        base.move()
        draw_window(win, birds, pipes, base, score)


# setting up neat
def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet,
                                neat.DefaultStagnation, config_path)
    p = neat.Population(config)  # generate a population
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # setting a fitness function - determined by how far a bird moves in the game
    winner = p.run(main, 50)

    # show final stats
    print('\nBest genome:\n{!s}'.format(winner))


if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)
