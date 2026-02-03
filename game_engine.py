import random

class RussianRoulette:
    def __init__(self, bullet_position=None):
        self.chambers = 6
        if bullet_position is not None:
             self.bullet_position = bullet_position
        else:
            self.bullet_position = random.randint(0, 5)
        self.current_chamber = 0
        self.game_over = False

    def pull_trigger(self):
        """
        Simula apretar el gatillo.
        Retorna:
            "BANG" si la bala está en la recámara actual.
            "CLICK" si la recámara está vacía.
            "ALREADY_OVER" si el juego ya terminó.
        """
        if self.game_over:
            return "ALREADY_OVER"
        
        result = "CLICK"
        if self.current_chamber == self.bullet_position:
            result = "BANG"
            self.game_over = True
        
        self.current_chamber += 1
        return result

    def get_status(self):
        """
        Retorna el estado actual del revólver.
        """
        return {
            "chamber_index": self.current_chamber,
            "total_chambers": self.chambers,
            "probability_percent": round(100 / (self.chambers - self.current_chamber), 1) if self.current_chamber < self.chambers else 100
        }
