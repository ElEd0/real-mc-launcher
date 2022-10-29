
import uuid
import minecraft_launcher_lib

class LauncherProfile():
	
	
	def __init__(self, id=None, data={}):
		self.isNew = id == None
		self.id = (id if id != None else self.genId())
		self.name = self.get(data, 'name', "")
		self.created = self.get(data, 'created', "1970-01-01T00:00:00.000Z")
		self.lastUsed = self.get(data, 'lastUsed', "1970-01-01T00:00:00.000Z")
		self.lastVersionId = self.get(data, 'lastVersionId', "")
		self.gameDir = self.get(data, 'gameDir', None)
		self.javaDir = self.get(data, 'javaDir', None)
		self.javaArgs = self.get(data, 'javaArgs', None)
		data['resolution'] = self.get(data, 'resolution', {})
		self.width = self.get(data['resolution'], 'width', 854)
		self.height = self.get(data['resolution'], 'height', 480)
		self.type = self.get(data, 'type', "custom")
		self.icon = self.get(data, 'icon', "")
		
		# the following settings are not present in the official MC launcher
		# cause they thought it was a good idea to make them global
		allowedReleaseTypes = self.get(data, 'allowedReleaseTypes', [])
		self.snapshot = "snapshot" in allowedReleaseTypes
		self.beta = "beta" in allowedReleaseTypes
		self.alpha = "alpha" in allowedReleaseTypes
		self.useHopperCrashService = self.get(data, 'useHopperCrashService', False)
		self.launcherVisibility = self.get(data, 'launcherVisibility', 0)
		
	
	def getData(self):
		allowedReleaseTypes = []
		if self.snapshot: allowedReleaseTypes.append("snapshot")
		if self.beta: allowedReleaseTypes.append("beta")
		if self.alpha: allowedReleaseTypes.append("alpha")
		data = {
			'name': self.name,
			'created': self.created,
			'lastUsed': self.lastUsed,
			'lastVersionId': self.lastVersionId,
			'resolution': {
				'width': self.width,
				'height': self.height
			},
			'type': self.type,
			'icon': self.icon,
			'allowedReleaseTypes': allowedReleaseTypes,
			'useHopperCrashService': self.useHopperCrashService,
			'launcherVisibility': self.launcherVisibility
		}
		if self.gameDir != None and len(self.gameDir) != 0:
			data['gameDir'] = self.gameDir
		if self.javaDir != None and len(self.javaDir) != 0:
			data['javaDir'] = self.javaDir
		if self.javaArgs != None and len(self.javaArgs) != 0:
			data['javaArgs'] = self.javaArgs
		return data
	
		
	def genId(self):
		return uuid.uuid4().hex
	
	def get(self, data, key, defValue=""):
		if key in data:
			return data[key]
		return defValue
	
	