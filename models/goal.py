from dataclasses import dataclass
 

@dataclass
class Goal:
    calorie_goal: int
    protein_goal: int
    carbs_goal: int
    fats_goal: int
 
def progress_percentage(self, current):
    return min((current / self.calorie_goal) * 100, 100)