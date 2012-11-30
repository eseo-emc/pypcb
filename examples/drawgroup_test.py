from pypcb import *
stack = Stack(numberOfFaces=4)

class MyGroup(DrawGroup):
    margin = 5.0
    
    def __init__(self):
        self.append(Rectangle(startArrow=Arrow(Location(0,0),E),width=1,height=3,gerberLayer=stack[0].copper[0]))
        self.append(Rectangle(startArrow=Arrow(Location(3,0),E),width=1,height=3,gerberLayer=stack[0].copper[0]))

group = MyGroup()
print group
#resonator.topRight = card.groundPlane.bottomRight
group.draw()

stack.writeOut()