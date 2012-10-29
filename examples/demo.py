from pypcb import *
stack = Stack(numberOfLayers=4)

card = GtemCard()
card.draw(stack)

StrokeText(Arrow(card.centerLocation(),N),'Mohamed',height=1.5,mirrored=True).draw(stack.bottom[0])

ic = Soic8(card.centerLocation())
ic.draw(stack.bottom,None)

for (number,trace) in enumerate(ic.padTraces()):
    StrokeText(trace[0].endArrow.alongArrow(3.),str(number+1),mirrored=True).draw(stack.bottomSilkScreen[0])



stack.writeOut()