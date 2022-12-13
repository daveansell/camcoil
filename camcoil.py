import math
import pprint
class camcoil():
	def __init__( self, **config):
		conf={
			'spindleAxis' : "Y",
			'spindleRot' : 1.0,
			'xAxis' : "X",
			'wireWidth' : 1.0,
			'coilRad':10, #if coil is non-circular it is the largest radius (if it has flat sides fudge
			'armCentreRad':60.0,
			'armLength':10.0,
			'castorAngleFactor':0.4,
			'jumpAngleFactor':1.1,
			'jumpTheta':1.0,
			'feed':500,
                        'prefixGcode':'G10 P0 L20 Y0',
                        'endProportion':0.05,
                        'endSlowdown':0.2,
		}
		self.x = 0.0
		self.theta = 0.0
		for c in config:
			if c in conf:
				conf[c]=config[c]
			else:
				print (str(c)+" is not a normal config")
		for c in conf:
			setattr(self, c, conf[c])
		self.commands = []

	def add_turns( self, numturns, xdir, tdir, castorDist, jumpCastorDist,mode):
		slope = float(self.wireWidth)
		castorTheta = castorDist/slope
                eturns = min(numturns, self.endTurns)
                mturns = numturns - eturns
                print(mode + str(slope))
		if mode=='simple':
			self.moveRel ( float(self.wireWidth) * eturns * xdir,
					 eturns * tdir, self.feed*self.endSlowdown)
			self.moveRel ( float(self.wireWidth) * mturns * xdir,
					 mturns * tdir)

		elif mode in ['bobbin'] :
			self.moveRel (0, min(castorTheta, numturns)*tdir, self.feed*self.endSlowdown)
			self.moveRel ( max((float(self.wireWidth) * mturns -castorDist),0) *xdir,
					 max( mturns -castorTheta,0) *tdir)
                        # slow down the bit at the end
			self.moveRel ( max((float(self.wireWidth) * eturns ),0) *xdir,
					 max( eturns,0) *tdir, feed=self.feed*self.endSlowdown)
			self.moveRel (castorDist * xdir,0, feed=self.feed*self.endSlowdown)
		elif mode in ['bobbinStart'] :
			self.moveRel ( min(1.0, numturns)*slope*xdir, min(1.0, numturns)*tdir)
			self.moveRel ( 0, min(castorTheta, numturns)*tdir)
			self.moveRel (slope*max(0, mturns-1.0-castorTheta)*xdir, 
					max(0, mturns-1.0-castorTheta)*tdir) 
			self.moveRel (slope*max(0, eturns)*xdir, 
					max(0, eturns)*tdir, feed=self.feed*self.endSlowdown) 
			self.moveRel (castorDist * xdir,0)

		if mode in ['freeStandingStart']:
			print min(1.0, numturns)*slope*xdir
			self.moveRel ( min(1.0, numturns)*slope*xdir, min(1.0, numturns)*tdir)
			self.moveRel ( 0, min(castorTheta, numturns)*tdir)
			self.moveRel (slope*max(0, numturns-1.0-castorTheta)*xdir, 
					max(0, numturns-1.0-castorTheta)*tdir) 
		if mode in ['freeStanding']:
			self.moveRel ( (jumpCastorDist-castorDist)*xdir , 0)
			self.moveRel ( 0, self.jumpTheta*tdir)
			self.moveRel ( (-jumpCastorDist+self.jumpTheta*slope)*xdir, 0)
			self.moveRel (0, min(castorTheta, numturns)*tdir)
			self.moveRel (slope*max(0, numturns-self.jumpTheta-castorTheta)*xdir, 
					max(0, numturns-self.jumpTheta-castorTheta)*tdir) 
		

	def moveRel(self, dx, dTheta, feed=None):
		print str(dx)+","+str(dTheta)
		self.x += dx
		self.theta += dTheta
		self.commands.append({
                        'cmd':'go',
                        'x':self.x,#+float(self.wireWidth)*numturns, 
                        'theta':float(self.spindleRot)*self.theta,#+float(self.spindleRot)*numturns*tdir
                        'feed':feed,
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
		maxCastorAngle = self.maxCastorAngle(coilRad*2, self.wireWidth)
		castorAngle = self.castorAngleFactor * maxCastorAngle
		armDist = math.sqrt(self.armCentreRad**2+coilRad**2)-self.armLength
		castorDist = armDist*math.sin(castorAngle/180.0*math.pi)
		
		jumpCastorDist = armDist*math.sin(self.jumpAngleFactor*maxCastorAngle/180.0*math.pi)
		
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
                print ("layerturns = "+str(layerTurns))
                self.endTurns = layerTurns*self.endProportion
#		print "layerTurns="+str(layerTurns)+" x="+str(self.x)
		start=True
		while turnsleft>layerTurns:
			if mode in ['bobbin', 'freeStanding'] and start:
				self.add_turns(layerTurns, xdir, tdir, castorDist, jumpCastorDist, mode+'Start')
				start=False
			else:
				self.add_turns(layerTurns, xdir, tdir, castorDist, jumpCastorDist, mode)
			xdir*=-1
			turnsleft-=layerTurns
			if freeStanding and layerTurns>1:
				layerTurns-=1
#				print "layerTurns="+str(layerTurns)+" x="+str(self.x)
		self.add_turns(turnsleft, xdir, tdir, castorDist, jumpCastorDist, mode)
                pprint.pprint (self.commands)
	def move( self, xto, thetaTo=None, feed=None):
		if thetaTo is None:
			self.commands.append(
                                {'cmd':'go', 'x':xto, 'feed':feed})
		else:
			self.commands.append(
                                {'cmd':'go', 'x':xto, 'theta':thetaTo, 'feed':feed})
			self.theta = thetaTo
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
					o+=self.xAxis+str(round(c['x'],2))
				if 'theta' in c:
					o+=self.spindleAxis + str(round(c['theta'],2))
				if 'feed' in c and c['feed'] is not None:
					o+="F"+str(c['feed'])
				else:
					o+="F"+str(self.feed)
			if c['cmd']=='comment':
				o="("+str(c['text'])+")"
			output.append(o)
		return output
	def renderFile(self,filename):
		f = open(filename+".ngc", 'w')
                f.write(self.prefixGcode+"\n")
		f.write("\n".join(self.render()))

	def maxCastorAngle(self, dBobbin, dWire):
		return 51.52*dBobbin**-0.41 + 11.31**-0.33 * math.log(dWire)
