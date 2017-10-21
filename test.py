class Pony:
	def cooler(self):
		return '20%'

	def pony(self, func):
		print(func(), self.cooler())

	@self.pony
	def rainbow(self):
		return 'Rainbow Dash'
