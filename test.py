import coil

c = coil.coil(wireWidth=0.6)

c.add_coil(100, 1, 0.0, 4.0, freeStanding=True, wireWidth=0.63, mode='bobbin')
#c.toAngle( 0.5, 1)
#c.toAngle( 0, 1)
c.renderFile('test')
