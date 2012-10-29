from pypcb import *
copper =  GerberFile('Copper')
numberOfHoles = 0

def sierpinsky(center=Location(0,0),width=10.,recursions=1):
    global numberOfHoles
    for x in [-1,0,1]:
        for y in [-1,0,1]:
            if x == 0 and y == 0:
                numberOfHoles += 1
            else:
                subCenter = Location(x,y)*width/3+center
                if recursions == 0:
                    Square(subCenter,width/3).draw(copper[0])
                else:
                    sierpinski(subCenter,width/3,recursions-1)
                

sierpinsky(recursions=2)
copper.writeOut()
print 'Drew Sierpinski carpet with {n} holes'.format(n=numberOfHoles)

