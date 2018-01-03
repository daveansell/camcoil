import math
class coil():
	def __init__( self, **config):
		conf={
			'spindleAxis' : "Y",
			'spindleRot' : 1.0,
			'xAxis' : "X",
			'wireWidth' : 1.0,
			'coilRad':10, #if coil is non-circular it is the largest radius (if it has flat sides fudge
			'armCentreRad':50,
			'armLength':15,
			'castorAngleFactor':0.4,
			'feed':500
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

	def add_turns( self, numturns, xdir, tdir, castorDist, mode):
		slope = float(self.wireWidth)/self.spindleRot
		castorTheta = castorDist/slope
		if mode=='simple':
			self.x += float(self.wireWidth) * numturns * xdir
			self.theta += float(self.spindleRot) * numturns * tdir
			self.commands.append({
				'cmd':'go', 
				'x':self.x,#+float(self.wireWidth)*numturns, 
				'theta':self.theta,#+float(self.spindleRot)*numturns*tdir
			})
		elif mode in ['bobbin', 'bobbinStart'] :
			self.theta += min(castorTheta, numturns)*tdir
			self.commands.append({
                                'cmd':'go',
                                'x':self.x,#+float(self.wireWidth)*numturns, 
                                'theta':self.theta,#+float(self.spindleRot)*numturns*tdir
                        })
			self.x += max((float(self.wireWidth) * numturns -castorDist),0) *xdir
                        self.theta += max((float(self.spindleRot) * numturns )-castorTheta,0) *tdir
			self.commands.append({
                                'cmd':'go',
                                'x':self.x,#+float(self.wireWidth)*numturns, 
                                'theta':self.theta,#+float(self.spindleRot)*numturns*tdir
                        })
		if mode in ['bobbin']:
			self.x += castorDist * xdir
			self.commands.append({
                                'cmd':'go',
                                'x':self.x,#+float(self.wireWidth)*numturns, 
                                'theta':self.theta,#+float(self.spindleRot)*numturns*tdir
                        })

	def add_coil( self, numturns, tdir, xstart, xend, **config ):
		if 'mode' in config:
			mode = config['mode']
		else:
			mode = 'bobbin'
		if mode=='freeStanding':
			freeStanding=True
		else:
			freeStanding=False
		if 'coilRad' in config:
			coilRad = config['coilRad']	 #if coil is non-circular it is the largest radius (if it has flat sides fudge
		else:
			coilRad = self.coilRad
		castorAngle = self.castorAngleFactor*self.maxCastorAngle(coilRad*2, self.wireWidth)
		armDist = math.sqrt(self.armCentreRad**2+coilRad**2)-self.armLength
		castorDist = armDist*math.sin(castorAngle/180.0*math.pi)

		turnsleft = numturns
		self.move(xstart)
		if(xstart>xend):
			xdir = -1
		else:
			xdir = 1
		if mode=='bobbin':
			xend-=self.wireWidth*xdir

		length = abs(float(xend)-xstart)
		layerTurns = length/self.wireWidth
#		print "layerTurns="+str(layerTurns)+" x="+str(self.x)

		while turnsleft>layerTurns:
			self.add_turns(layerTurns, xdir, tdir, castorDist, mode)
			xdir*=-1
			turnsleft-=layerTurns
			if freeStanding and layerTurns>1:
				layerTurns-=1
#				print "layerTurns="+str(layerTurns)+" x="+str(self.x)
		if mode=='bobbin':
			self.add_turns(turnsleft, xdir, tdir, castorDist, 'bobbinStart')
		else:
			self.add_turns(turnsleft, xdir, tdir, castorDist, mode)

	def move( self, xto):
		self.commands.append(
                        {'cmd':'go', 'x':xto})
		self.x = xto
	def toAngle( self, angle, tdir):
		current = self.theta % self.spindleRot
		self.commands.append({'cmd':'comment', 'text':"theta"+str(self.theta)+" current="+str(current)+"angle="+str(angle)})
		if(angle-current *tdir >0):
			self.theta +=angle-current
			self.commands.append(
                        {'cmd':'go', 'theta':self.theta})
		else:
			self.theta +=angle-current+self.spindleRot*tdir
			self.commands.append(
                        {'cmd':'go', 'theta':self.theta})

	def render(self):
		output = []
		for c in self.commands:
			if c['cmd']=='go':
				o='G1'
				if 'x' in c:
					o+=self.xAxis+str(round(c['x'],4))
				if 'theta' in c:
					o+=self.spindleAxis + str(round(c['theta'],4))
				if 'feed' in c:
					o+="F"+str(c['feed'])
				else:
					o+="F"+str(self.feed)
			if c['cmd']=='comment':
				o="("+str(c['text'])+")"
			output.append(o)
		return output
	def renderFile(self,filename):
		f = open(filename+".ngc", 'w')
		f.write("\n".join(self.render()))

	def maxCastorAngle(self, dBobbin, dWire):
		return 51.52*dBobbin**-0.41 + 11.31**-0.33 * math.log(dWire)
