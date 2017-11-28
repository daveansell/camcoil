import coil

c = coil.coil(wireWidth=0.6)

c.add_coil(1000, 1, 50, 80, freeStanding=True)
c.toAngle( 50, 1)
c.toAngle( 0, 1)
c.render()
