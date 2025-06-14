import pygame
import random
import math
import requests
import json
import time
from typing import List, Dict, Tuple, Optional

pygame.init()

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
BROWN = (139, 69, 19)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GRAY = (128, 128, 128)
DARK_GREEN = (0, 100, 0)

class LMStudioAPI:
    def __init__(self, base_url="http://127.0.0.1:1234"):
        self.base_url = base_url
        
    def get_response(self, prompt: str, character_context: str = "") -> str:
        try:
            full_prompt = f"{character_context}\n\nPlayer says: {prompt}\n\nResponse:"
            
            data = {
                "model": "mistral-nemo-instruct-2407",
                "messages": [
                    {"role": "system", "content": character_context},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 150
            }
            
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=data,
                timeout=20
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                return "I'm not sure what to say right now."
                
        except Exception as e:
            return f"Sorry, I can't respond right now."

class Sprite:
    def __init__(self, x: int, y: int, width: int, height: int, color: tuple):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.rect = pygame.Rect(x, y, width, height)
        
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        
    def update_position(self, x: int, y: int):
        self.x = x
        self.y = y
        self.rect.x = x
        self.rect.y = y

class Player:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.width = 32
        self.height = 32
        self.speed = 4
        self.sprite = Sprite(x, y, self.width, self.height, BLUE)
        self.direction = "down"
        
    def update(self, keys):
        old_x, old_y = self.x, self.y
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed
            self.direction = "left"
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed
            self.direction = "right"
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            self.y -= self.speed
            self.direction = "up"
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.y += self.speed
            self.direction = "down"
            
        self.x = max(0, min(SCREEN_WIDTH - self.width, self.x))
        self.y = max(0, min(SCREEN_HEIGHT - self.height, self.y))
        
        self.sprite.update_position(self.x, self.y)
        
    def get_front_position(self) -> Tuple[int, int]:
        if self.direction == "up":
            return (self.x, self.y - 40)
        elif self.direction == "down":
            return (self.x, self.y + 40)
        elif self.direction == "left":
            return (self.x - 40, self.y)
        elif self.direction == "right":
            return (self.x + 40, self.y)
        return (self.x, self.y)
        
    def draw(self, screen):
        self.sprite.draw(screen)

class Villager:
    def __init__(self, x: int, y: int, name: str, backstory: str):
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.width = 32
        self.height = 32
        self.speed = 1
        self.name = name
        self.backstory = backstory
        self.sprite = Sprite(x, y, self.width, self.height, RED)
        self.hp = 10
        self.max_hp = 10
        self.memory = []
        self.current_task = None
        self.target_pos = None
        self.following_player = False
        self.fleeing = False
        self.seeking_help = False
        self.move_timer = 0
        self.move_direction = random.choice(["up", "down", "left", "right"])
        
    def add_memory(self, interaction: str):
        self.memory.append(f"{time.strftime('%H:%M')} - {interaction}")
        if len(self.memory) > 10:
            self.memory.pop(0)
            
    def get_context(self) -> str:
        context = f"You are {self.name}. {self.backstory}\n"
        context += f"Your current HP: {self.hp}/{self.max_hp}\n"
        if self.memory:
            context += "Recent memories:\n" + "\n".join(self.memory[-3:]) + "\n"
        context += "Respond in character as a villager in this game world. Keep responses brief and natural."
        return context
        
    def update(self, player, villagers, obstacles):
        self.move_timer += 1
        
        if self.hp <= 0:
            return
            
        if self.hp <= 4 and not self.fleeing:
            self.fleeing = True
            self.seeking_help = True
            self.add_memory("Started fleeing due to low health!")
            
        if self.fleeing:
            self._flee_behavior(player, obstacles)
        elif self.following_player:
            self._follow_player(player, obstacles)
        elif self.current_task:
            self._execute_task(villagers, obstacles)
        else:
            self._random_walk(obstacles)
            
        self.sprite.update_position(self.x, self.y)
        
    def _random_walk(self, obstacles):
        if self.move_timer > 120:
            self.move_timer = 0
            self.move_direction = random.choice(["up", "down", "left", "right", "stop"])
            
        if self.move_direction == "stop":
            return
            
        old_x, old_y = self.x, self.y
        
        if self.move_direction == "up":
            self.y -= self.speed
        elif self.move_direction == "down":
            self.y += self.speed
        elif self.move_direction == "left":
            self.x -= self.speed
        elif self.move_direction == "right":
            self.x += self.speed
            
        if self._check_collision(obstacles) or self.x < 0 or self.x > SCREEN_WIDTH - self.width or self.y < 0 or self.y > SCREEN_HEIGHT - self.height:
            self.x, self.y = old_x, old_y
            self.move_direction = random.choice(["up", "down", "left", "right"])
            
    def _follow_player(self, player, obstacles):
        dx = player.x - self.x
        dy = player.y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > 50:
            old_x, old_y = self.x, self.y
            if abs(dx) > abs(dy):
                self.x += self.speed if dx > 0 else -self.speed
            else:
                self.y += self.speed if dy > 0 else -self.speed
                
            if self._check_collision(obstacles):
                self.x, self.y = old_x, old_y
                
    def _flee_behavior(self, player, obstacles):
        dx = player.x - self.x
        dy = player.y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 200:
            old_x, old_y = self.x, self.y
            if abs(dx) > abs(dy):
                self.x += -self.speed*2 if dx > 0 else self.speed*2
            else:
                self.y += -self.speed*2 if dy > 0 else self.speed*2
                
            self.x = max(0, min(SCREEN_WIDTH - self.width, self.x))
            self.y = max(0, min(SCREEN_HEIGHT - self.height, self.y))
            
            if self._check_collision(obstacles):
                self.x, self.y = old_x, old_y
        else:
            self.fleeing = False
            
    def _execute_task(self, villagers, obstacles):
        if self.current_task and "go to" in self.current_task.lower():
            if self.target_pos:
                dx = self.target_pos[0] - self.x
                dy = self.target_pos[1] - self.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance < 20:
                    self.current_task = None
                    self.target_pos = None
                    self.add_memory(f"Arrived at destination")
                else:
                    old_x, old_y = self.x, self.y
                    if abs(dx) > abs(dy):
                        self.x += self.speed*2 if dx > 0 else -self.speed*2
                    else:
                        self.y += self.speed*2 if dy > 0 else -self.speed*2
                        
                    if self._check_collision(obstacles):
                        self.x, self.y = old_x, old_y
                        
    def _check_collision(self, obstacles) -> bool:
        temp_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        for obstacle in obstacles:
            if temp_rect.colliderect(obstacle):
                return True
        return False
        
    def take_damage(self):
        self.hp -= 1
        self.add_memory("Was attacked by the player!")
        if self.hp <= 0:
            self.add_memory("Was defeated!")
            
    def draw(self, screen, font):
        if self.hp > 0:
            self.sprite.draw(screen)
            
            name_surface = font.render(self.name, True, BLACK)
            name_rect = name_surface.get_rect(center=(self.x + self.width//2, self.y - 15))
            screen.blit(name_surface, name_rect)
            
            hp_bar_width = 30
            hp_bar_height = 4
            hp_percentage = self.hp / self.max_hp
            hp_bar_x = self.x + (self.width - hp_bar_width) // 2
            hp_bar_y = self.y - 25
            
            pygame.draw.rect(screen, RED, (hp_bar_x, hp_bar_y, hp_bar_width, hp_bar_height))
            pygame.draw.rect(screen, GREEN, (hp_bar_x, hp_bar_y, hp_bar_width * hp_percentage, hp_bar_height))

class House:
    def __init__(self, x: int, y: int, label: str):
        self.x = x
        self.y = y
        self.width = 80
        self.height = 80
        self.label = label
        self.rect = pygame.Rect(x, y, self.width, self.height)
        
    def draw(self, screen, font):
        pygame.draw.rect(screen, BROWN, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)
        
        label_surface = font.render(self.label, True, BLACK)
        label_rect = label_surface.get_rect(center=(self.x + self.width//2, self.y + self.height + 10))
        screen.blit(label_surface, label_rect)

class Tree:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 60
        self.rect = pygame.Rect(x, y, self.width, self.height)
        
    def draw(self, screen):
        pygame.draw.rect(screen, BROWN, (self.x + 15, self.y + 40, 10, 20))
        pygame.draw.circle(screen, DARK_GREEN, (self.x + 20, self.y + 20), 20)

class DialogBox:
    def __init__(self):
        self.active = False
        self.text = ""
        self.input_text = ""
        self.response_text = ""
        self.current_villager = None
        
    def show(self, villager):
        self.active = True
        self.current_villager = villager
        self.text = f"Talking to {villager.name}"
        self.input_text = ""
        self.response_text = ""
        
    def hide(self):
        self.active = False
        self.current_villager = None
        self.text = ""
        self.input_text = ""
        self.response_text = ""
        
    def add_char(self, char):
        if len(self.input_text) < 100:
            self.input_text += char
            
    def remove_char(self):
        if self.input_text:
            self.input_text = self.input_text[:-1]
            
    def draw(self, screen, font):
        if not self.active:
            return
            
        dialog_rect = pygame.Rect(50, SCREEN_HEIGHT - 200, SCREEN_WIDTH - 100, 150)
        pygame.draw.rect(screen, WHITE, dialog_rect)
        pygame.draw.rect(screen, BLACK, dialog_rect, 2)
        
        title_surface = font.render(self.text, True, BLACK)
        screen.blit(title_surface, (dialog_rect.x + 10, dialog_rect.y + 10))
        
        if self.response_text:
            response_lines = self.response_text.split('\n')
            for i, line in enumerate(response_lines[:3]):
                response_surface = font.render(line, True, BLUE)
                screen.blit(response_surface, (dialog_rect.x + 10, dialog_rect.y + 40 + i * 20))
                
        input_surface = font.render(f"You: {self.input_text}|", True, BLACK)
        screen.blit(input_surface, (dialog_rect.x + 10, dialog_rect.y + 110))
        
        instructions = font.render("Type your message and press ENTER to send, ESC to close", True, GRAY)
        screen.blit(instructions, (dialog_rect.x + 10, dialog_rect.y + 130))

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Village AI Demo")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 16)
        
        self.player = Player(100, 100)
        self.dialog_box = DialogBox()
        self.ai_api = LMStudioAPI()
        
        self.houses = [
            House(200, 200, "House 1"),
            House(400, 300, "House 2"),
            House(600, 150, "House 3")
        ]
        
        self.trees = [
            Tree(300, 100),
            Tree(500, 200),
            Tree(150, 300),
            Tree(700, 400),
            Tree(800, 100)
        ]
        
        self.villagers = [
            Villager(250, 100, "Alice", "You are Alice, a friendly baker who loves making bread and chatting about recipes. You're always cheerful and helpful."),
            Villager(450, 200, "Bob", "You are Bob, a grumpy old blacksmith who's seen it all. You don't like being bothered but have a good heart deep down."),
            Villager(350, 400, "Carol", "You are Carol, a curious young scholar who loves learning about everything. You ask lots of questions and share interesting facts."),
            Villager(150, 500, "Dave", "You are Dave, a laid-back farmer who takes life easy. You speak slowly and enjoy talking about the weather and crops.")
        ]
        
        self.obstacles = [house.rect for house in self.houses] + [tree.rect for tree in self.trees]
        
    def handle_talk(self):
        front_x, front_y = self.player.get_front_position()
        front_rect = pygame.Rect(front_x, front_y, 32, 32)
        
        for villager in self.villagers:
            if villager.hp > 0 and front_rect.colliderect(villager.sprite.rect):
                self.dialog_box.show(villager)
                return True
        return False
        
    def handle_attack(self):
        front_x, front_y = self.player.get_front_position()
        front_rect = pygame.Rect(front_x, front_y, 32, 32)
        
        for villager in self.villagers:
            if villager.hp > 0 and front_rect.colliderect(villager.sprite.rect):
                villager.take_damage()
                return True
        return False
        
    def process_dialog_input(self):
        if self.dialog_box.current_villager and self.dialog_box.input_text.strip():
            villager = self.dialog_box.current_villager
            user_input = self.dialog_box.input_text.strip()
            
            villager.add_memory(f"Player said: {user_input}")
            
            if "follow me" in user_input.lower():
                villager.following_player = True
                villager.current_task = None
                villager.add_memory("Started following the player")
                self.dialog_box.response_text = "Okay, I'll follow you!"
                
            elif "stop following" in user_input.lower():
                villager.following_player = False
                villager.add_memory("Stopped following the player")
                self.dialog_box.response_text = "Alright, I'll stay here."
                
            elif "go to house" in user_input.lower():
                house_num = None
                for i in range(1, 4):
                    if f"house {i}" in user_input.lower():
                        house_num = i
                        break
                        
                if house_num:
                    house = self.houses[house_num - 1]
                    villager.current_task = f"go to house {house_num}"
                    villager.target_pos = (house.x + house.width//2, house.y + house.height//2)
                    villager.following_player = False
                    villager.add_memory(f"Ordered to go to house {house_num}")
                    self.dialog_box.response_text = f"I'll head to house {house_num}!"
                else:
                    context = villager.get_context()
                    self.dialog_box.response_text = self.ai_api.get_response(user_input, context)
                    
            elif "attack" in user_input.lower():
                target_name = None
                for v in self.villagers:
                    if v.name.lower() in user_input.lower() and v != villager:
                        target_name = v.name
                        break
                        
                if target_name:
                    villager.add_memory(f"Ordered to attack {target_name}")
                    self.dialog_box.response_text = f"I... I can't attack {target_name}. That's not right!"
                else:
                    context = villager.get_context()
                    self.dialog_box.response_text = self.ai_api.get_response(user_input, context)
                    
            else:
                context = villager.get_context()
                self.dialog_box.response_text = self.ai_api.get_response(user_input, context)
                
            self.dialog_box.input_text = ""
            
    def run(self):
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    
                elif event.type == pygame.KEYDOWN:
                    if self.dialog_box.active:
                        if event.key == pygame.K_ESCAPE:
                            self.dialog_box.hide()
                        elif event.key == pygame.K_RETURN:
                            self.process_dialog_input()
                        elif event.key == pygame.K_BACKSPACE:
                            self.dialog_box.remove_char()
                        else:
                            if event.unicode.isprintable():
                                self.dialog_box.add_char(event.unicode)
                    else:
                        if event.key == pygame.K_e:
                            self.handle_talk()
                        elif event.key == pygame.K_p:
                            self.handle_attack()
                            
            if not self.dialog_box.active:
                keys = pygame.key.get_pressed()
                self.player.update(keys)
                
                for villager in self.villagers:
                    villager.update(self.player, self.villagers, self.obstacles)
                    
            self.screen.fill(GREEN)
            
            for house in self.houses:
                house.draw(self.screen, self.font)
                
            for tree in self.trees:
                tree.draw(self.screen)
                
            self.player.draw(self.screen)
            
            for villager in self.villagers:
                villager.draw(self.screen, self.small_font)
                
            self.dialog_box.draw(self.screen, self.font)
            
            instructions = [
                "Arrow Keys/WASD: Move",
                "E: Talk to villager in front",
                "P: Attack villager in front",
                "Commands: 'follow me', 'stop following', 'go to house X'"
            ]
            
            for i, instruction in enumerate(instructions):
                text_surface = self.small_font.render(instruction, True, BLACK)
                self.screen.blit(text_surface, (10, 10 + i * 20))
                
            pygame.display.flip()
            self.clock.tick(FPS)
            
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()