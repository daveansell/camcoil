class coil():
	def __init__( self, **config):
		conf={
			'spindleAxis' : "Y",
			'spindleRot' : 100,
			'xAxis' : "X",
			'wireWidth' : 1.0,
		}
		self.x = 0.0
		self.theta = 0.0
		for c in config:
			if c in conf:
				conf[c]=config[c]
			else:
				print str(c)+" is not a normal config"
		for c in conf:
			setattr(self, c, conf[c])
		self.commands = []

	def add_turns( self, numturns, xdir, tdir):
#		print self.theta
		slope = float(self.wireWidth)/self.spindleRot
		self.x += float(self.wireWidth) * numturns * xdir
		self.theta += float(self.spindleRot) * numturns * tdir
		self.commands.append({
			'cmd':'go', 
			'x':self.x,#+float(self.wireWidth)*numturns, 
			'theta':self.theta,#+float(self.spindleRot)*numturns*tdir
		})
		  
	def add_coil( self, numturns, tdir, xstart, xend, **config ):
		if 'freeStanding' in config:
			freeStanding=True
		else:
			freeStanding=False
		turnsleft = numturns
		self.move(xstart)
		length = abs(float(xend)-xstart)
		layerTurns = length/self.wireWidth
		if(xstart>xend):
			xdir = -1
		else:
			xdir = 1
#		print "layerTurns="+str(layerTurns)+" x="+str(self.x)

		while turnsleft>layerTurns:
			self.add_turns(layerTurns, xdir, tdir)
			xdir*=-1
			turnsleft-=layerTurns
			if freeStanding and layerTurns>1:
				layerTurns-=1
#				print "layerTurns="+str(layerTurns)+" x="+str(self.x)
		self.add_turns(turnsleft, xdir, tdir)

	def move( self, xto):
		self.commands.append(
                        {'cmd':'go', 'x':xto})
		self.x = xto
	def toAngle( self, angle, tdir):
		current = self.theta % self.spindleRot
		print "theta"+str(self.theta)+" current="+str(current)+"angle="+str(angle)
		if(angle-current *tdir >0):
			self.theta +=angle-current
			self.commands.append(
                        {'cmd':'go', 'theta':self.theta})
		else:
			self.theta +=angle-current+self.spindleRot*tdir
			self.commands.append(
                        {'cmd':'go', 'theta':self.theta})

	def render(self):
		for c in self.commands:
			if c['cmd']=='go':
				o='G1'
				if 'x' in c:
					o+=self.xAxis+str(c['x'])
				if 'theta' in c:
					o+=self.spindleAxis + str(c['theta'])
				print o
