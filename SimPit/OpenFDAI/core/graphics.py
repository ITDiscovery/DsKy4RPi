import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

class FDAIScreen:
    def __init__(self, width=800, height=800, fullscreen=False):
        self.width = width
        self.height = height
        self.fullscreen = fullscreen
        
        # Defaults (can be overwritten by main.py)
        self.texture_path = "assets/navball_8k.png"
        self.overlay_color = (1.0, 0.6, 0.0)
        
        self.texture_id = None
        self.quad = None

    def init_display(self):
        pygame.init()
        flags = DOUBLEBUF | OPENGL
        if self.fullscreen:
            flags = flags | FULLSCREEN
            
        pygame.display.set_mode((self.width, self.height), flags)
        # ... rest of init_display is the same ...
        self._load_texture(self.texture_path) # Use the variable!
    def init_display(self):
        pygame.init()
        # OPENGL | DOUBLEBUF are critical for smooth 3D
        pygame.display.set_mode((self.width, self.height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("OpenFDAI - Orbiter 2024")

        # Camera Setup
        gluPerspective(45, (self.width / self.height), 0.1, 50.0)
        glTranslatef(0.0, 0.0, -3.5) # Zoom level
        
        # Lighting & Textures
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)
        self._load_texture("assets/navball_8k.png")
        
        # Create Sphere
        self.quad = gluNewQuadric()
        gluQuadricTexture(self.quad, GL_TRUE)

    def _load_texture(self, path):
        img = pygame.image.load(path)
        texture_data = pygame.image.tostring(img, "RGB", 1)
        w, h = img.get_rect().size
        
        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, w, h, 0, GL_RGB, GL_UNSIGNED_BYTE, texture_data)
        
        # Linear filtering for smooth pixels when rotating
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    def _draw_overlay(self):
        """Draws the static 'Airplane' symbol on top of the 3D ball."""
        # 1. Switch to 2D Orthographic Mode
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, self.width, 0, self.height)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # 2. Disable 3D features so lines draw flat and bright
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_TEXTURE_2D)
        
        # 3. Define the Center
        cx, cy = self.width / 2, self.height / 2
        size = 150 # Scale of the indicator
        wing_w = 120
        wing_h = 20
        
        # 4. Set Color (NASA Orange/Yellow)
        glColor3f(1.0, 0.6, 0.0) 
        glLineWidth(4.0)
        
        # 5. Draw the Shape (The "W" or Airplane Wings)
        glBegin(GL_LINES)
        
        # Left Wing
        glVertex2f(cx - size, cy)
        glVertex2f(cx - wing_h, cy)
        
        # Right Wing
        glVertex2f(cx + wing_h, cy)
        glVertex2f(cx + size, cy)
        
        # Vertical Tail/Pointer (Top)
        glVertex2f(cx, cy + size * 0.8)
        glVertex2f(cx, cy + wing_h)

        # Center Dot (Optional, helpful for precision)
        # We simulate a dot with a tiny cross
        d = 5
        glVertex2f(cx - d, cy); glVertex2f(cx + d, cy)
        glVertex2f(cx, cy - d); glVertex2f(cx, cy + d)
        
        glEnd()
        
        # 6. Restore 3D Mode for next frame
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_DEPTH_TEST)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    def draw(self, pitch, yaw, roll):
        # 1. Handle Window Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False

        # 2. Clear Screen
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # --- RESET COLOR TO WHITE HERE ---
        # This ensures the texture is drawn with its original colors
        glColor3f(1.0, 1.0, 1.0) 
        
        # 3. Rotate Sphere
        glPushMatrix()
        glRotate(roll,  0, 0, 1)
        glRotate(pitch, 1, 0, 0)
        glRotate(yaw,   0, 1, 0)
        
        # 1. Stand the ball up (Fixes "Looking at North Pole")
        glRotate(-90, 1, 0, 0)
        
        gluSphere(self.quad, 1.2, 64, 64)
        glPopMatrix()
        
        # 4. Draw Overlay (This will set the color to Orange again for the UI)
        self._draw_overlay()
        
        pygame.display.flip()
        return True