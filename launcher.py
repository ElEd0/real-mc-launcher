from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QThread, QProcess, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QDialog, QWidget, QErrorMessage, QMessageBox,
		QHBoxLayout, QVBoxLayout, QGroupBox,
		QPushButton, QLabel, QComboBox, QPlainTextEdit, QCheckBox,
		QTabWidget, QLineEdit, QProgressBar,
		QSystemTrayIcon, QMenu)

import minecraft_launcher_lib, requests
import sys, os, json
from datetime import datetime

from LauncherProfile import LauncherProfile
from ProfileDialog import ProfileDialog
from WelcomeScreen import WelcomeScreen


class GameOutputWidget(QPlainTextEdit):
	def __init__(self):
		super().__init__()
		self.setReadOnly(True)
		self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
		self.isRunning = False

	def onProcessRead(self):
		self.log(bytes(self.process.readAll()).decode())
		
	def onProcessFinished(self):
		self.setRunning(False)
		self.log("Minecraft process finished\n")
	
	def log(self, output):
		cursor = self.textCursor()
		cursor.movePosition(cursor.MoveOperation.End)
		cursor.insertText(output)
		cursor.movePosition(cursor.MoveOperation.End)
		self.ensureCursorVisible()
		
	def setRunning(self, running):
		self.isRunning = running
		
	def execute_command(self, command, arguments):
		self.setPlainText("")
		
		self.process = QProcess()
		self.process.finished.connect(self.onProcessFinished)
		self.process.readyRead.connect(self.onProcessRead)
		self.process.start(command, arguments)
		self.setRunning(True)
		self.log("Minecraft process started\n")
		'''
		self.gameThread = GameThread(self, arguments)
		self.gameThread.outputSignal.connect(lambda output: self.display_output(output))
		self.gameThread.finished.connect(lambda: self.setRunning(False))
		self.gameThread.start()
		self.setRunning(True)

class GameThread(QThread):
	outputSignal = pyqtSignal(str)

	def __init__(self, parent, arguments) -> None:
		QThread.__init__(self)
		self.arguments = arguments
		self.parent = parent

	def run(self) -> None:
		self.process = QProcess()
		self.process.finished.connect(lambda: self.finished.emit())
		self.process.readyRead.connect(lambda: self.outputSignal.emit(bytes(self.process.readAll()).decode()))
		self.process.start("java", self.arguments)
		#print(' '.join(self.arguments))
		self.process.waitForFinished(-1)
		'''


class InstallThread(QThread):
	progress_max = pyqtSignal("int")
	progress = pyqtSignal("int")
	text = pyqtSignal("QString")
	errorSignal = pyqtSignal(str)

	def __init__(self) -> None:
		QThread.__init__(self)
		self._callback_dict = {
			"setStatus": lambda text: self.text.emit(text),
			"setMax": lambda max_progress: self.progress_max.emit(max_progress),
			"setProgress": lambda progress: self.progress.emit(progress),
		}

	def set_data(self, version: str, directory) -> None:
		self._version = version
		self._directory = directory

	def run(self) -> None:
		try:
			minecraft_launcher_lib.install.install_minecraft_version(self._version, self._directory, callback=self._callback_dict)
		except Error as e:
			self.errorSignal.emit(str(e))

class CloseDialog(QDialog):
	closeSignal = pyqtSignal(bool)
	
	def __init__(self, parent, runningInstances):
		super(CloseDialog, self).__init__(parent)
		self.setWindowModality(PyQt5.Qt.ApplicationModal)
		
		msg = ("ATTENTION! You are running minecraft instances, if you close the launcher the instances will close.\n"
		"Do you wish to end this instances or minimize the launcher to the system tray?\n\n"
		"Running instances:\n")
		label = QLabel(msg)
		
		instances = QPlainTextEdit()
		instances.setReadOnly(True)
		for inst in runningInstances:
			instances.appendPlainText(inst)
		
		cancel = QPushButton("Cancel")
		close = QPushButton("Close instances")
		minimize = QPushButton("Minimize to tray")
		cancel.clicked.connect(lambda: self.close())
		close.clicked.connect(lambda: self.closeDialog(True))
		minimize.clicked.connect(lambda: self.closeDialog(False))
		
		buttons = QHBoxLayout()
		buttons.addWidget(cancel)
		buttons.addStretch(1)
		buttons.addWidget(close)
		buttons.addWidget(minimize)
		
		mainLayout = QVBoxLayout()
		mainLayout.addWidget(label)
		mainLayout.addWidget(instances)
		mainLayout.addLayout(buttons)
		
		self.setLayout(mainLayout)
		self.setWindowIcon(QIcon(os.path.dirname(os.path.realpath(__file__)) + "/img/icon.png"))
		self.setWindowTitle("ATTENTION! Running instances")
		
	def closeDialog(self, closeLauncher):
		self.closeSignal.emit(closeLauncher)
		self.close()
		

class CheckNetworkThread(QThread):

	def __init__(self, callback) -> None:
		QThread.__init__(self)
		self.callback = callback

	def run(self) -> None:
		try:
			import socket
			socket.create_connection(("1.1.1.1", 53))
			self.callback(True)
		except Error as e:
			self.callback(False)

			
class MainWindow(QDialog):
	def __init__(self, parent=None):
		super(MainWindow, self).__init__(parent)
		
		self.hasInternet = False
		self.minecraftDir = minecraft_launcher_lib.utils.get_minecraft_directory()
		
		# get saved data
		self.launcherSettings = {
			"useMSA": False,
			"playerName": "",
			"uuid": "",
			'selectedProfileId': None
		}
		if (os.path.exists(self.minecraftDir + "/real_mc_launcher.json")):
			with open(self.minecraftDir + "/real_mc_launcher.json") as f:
				self.launcherSettings = self.launcherSettings | json.loads(f.read())
				f.close()
			
		
		self.tabs = QTabWidget()
		tab1 = WelcomeScreen()
		
		self.launcherLog = QPlainTextEdit()
		self.launcherLog.setReadOnly(True)
		self.launcherLog.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
		
		self.tabs.addTab(tab1, "Welcome")
		self.tabs.addTab(self.launcherLog, "Launcher log")
		
		self.installationProgress = QProgressBar()
		self.installationProgress.setTextVisible(True)
		self.installationProgress.hide()
		
		# PROFILES
		self.profileComboBox = QComboBox()
		
		self.newProfileButton = QPushButton("New Profile")
		self.editProfileButton = QPushButton("Edit Profile")
		
		def newProfile():
			curr = self.getSelectedProfile()
			new = None
			if curr is None:
				new = LauncherProfile()
			else:
				new = LauncherProfile(None, curr.getData())
				new.name = "Copy of " + new.name
			self.openProfileEditor(new)
		
		self.newProfileButton.clicked.connect(newProfile)
		self.editProfileButton.clicked.connect(lambda: self.openProfileEditor(self.getSelectedProfile()))
		
		
		profileLayout0 = QHBoxLayout()
		profileLayout0.addWidget(self.profileComboBox)
		profileLayout1 = QHBoxLayout()
		profileLayout1.addWidget(self.newProfileButton)
		profileLayout1.addWidget(self.editProfileButton)
		profileLayout = QVBoxLayout()
		profileLayout.addLayout(profileLayout0)
		profileLayout.addLayout(profileLayout1)
		
		profileContainer = QGroupBox("Profile")
		profileContainer.setLayout(profileLayout)
		profileContainer.setFixedWidth(270)
		
		# PLAY BUTTON
		self.playButton = QPushButton("Play Offline")
		self.playButton.setFixedSize(230, 60)
		self.playButton.clicked.connect(lambda: self.play(False, not self.hasInternet))
		
		self.playOpts = QPushButton()
		self.playOpts.setFixedSize(20, 60)
		self.playOpts.setEnabled(False)
		
		def _play_opts_triggered(opt):
			text = opt.text()
			if text == "Force Install":
				self.play(True, False)
			elif text == "Force Offline":
				self.play(False, True)
		
		self.playOptsMenu = QMenu()
		self.playOptsMenu.addAction("Force Install").setIconVisibleInMenu(False)
		self.playOptsMenu.addAction("Force Offline").setIconVisibleInMenu(False)
		self.playOptsMenu.triggered.connect(_play_opts_triggered)
		self.playOpts.setMenu(self.playOptsMenu)
		
		playLayout = QHBoxLayout()
		playLayout.addWidget(self.playButton)
		playLayout.addWidget(self.playOpts)
		playLayout.setSpacing(0)
		playLayout.setContentsMargins(0, 0, 0, 0)
		
		# ACCOUNT - login
		self.loginButton = QPushButton("Login")
		self.rememberCheckBox = QCheckBox("Remember login")
		
		loginLayout = QVBoxLayout()
		loginLayout.addWidget(self.loginButton)
		loginLayout.addWidget(self.rememberCheckBox)
		
		self.loginContainer = QWidget()
		self.loginContainer.setLayout(loginLayout)
		self.loginContainer.hide()
		
		
		# ACCOUNT - logged
		welcomeLabel = QLabel("Welcome <b>Ed0</b>!\nReady to play")
		logoutButton = QPushButton("Logout")
		
		loggedLayout = QVBoxLayout()
		loggedLayout.addWidget(welcomeLabel)
		loggedLayout.addWidget(logoutButton)
		
		self.loggedContainer = QWidget()
		self.loggedContainer.setLayout(loggedLayout)
		self.loggedContainer.hide()
		
		
		# ACCOUNT - noPremium
		playerLabel = QLabel("Player")
		self.playerField = QLineEdit()
		self.playerField.setText(self.launcherSettings['playerName'])
		
		noPremiumLayout = QHBoxLayout()
		noPremiumLayout.addWidget(playerLabel)
		noPremiumLayout.addWidget(self.playerField)
		
		self.noPremiumContainer = QWidget()
		self.noPremiumContainer.setLayout(noPremiumLayout)
		
		
		# ACCOUNT
		self.useMsAccount = QCheckBox("Use Microsoft account")
		self.useMsAccount.setChecked(self.launcherSettings['useMSA'])
		self.useMsAccount.stateChanged.connect(self.changeAccountType)
		self.useMsAccount.setEnabled(False)
		
		accountLayout = QVBoxLayout()
		accountLayout.addWidget(self.useMsAccount)
		accountLayout.addWidget(self.loginContainer)
		accountLayout.addWidget(self.loggedContainer)
		accountLayout.addWidget(self.noPremiumContainer)
		
		accountContainer = QGroupBox("Account")
		accountContainer.setLayout(accountLayout)
		accountContainer.setFixedWidth(270)
		
		
		# bottom container
		bottomContainer = QHBoxLayout()
		bottomContainer.addWidget(profileContainer)
		bottomContainer.addStretch()
		bottomContainer.addLayout(playLayout)
		bottomContainer.addStretch()
		bottomContainer.addWidget(accountContainer)
		
		# main layout
		mainLayout = QVBoxLayout()
		mainLayout.addWidget(self.tabs)
		mainLayout.addWidget(self.installationProgress)
		mainLayout.addLayout(bottomContainer)
		
		icon = QIcon(os.path.dirname(os.path.realpath(__file__)) + "/img/icon.png")
		
		self.setLayout(mainLayout)
		self.setWindowIcon(icon)
		self.setWindowTitle("Real MC Launcher INDEV 1.0")
		
		# system tray icon
		self.sysTray = QSystemTrayIcon(self)
		self.sysTray.setIcon(icon)
		
		def _tray_icon_activated(reason):
			self.show()
			self.sysTray.hide()
		self.sysTray.activated.connect(_tray_icon_activated)
		
		
		# load account
		self.changeAccountType()
		
		# load profiles
		self.loadProfiles(self.launcherSettings['selectedProfileId'])
		
		# check internet connection
		def _on_network_status(hasInternet):
			self.hasInternet = hasInternet
			if hasInternet:
				self.playButton.setText("Play")
				self.playOpts.setEnabled(True)
		self.check = CheckNetworkThread(_on_network_status)
		self.check.start()
		
	
	def openProfileEditor(self, profile):
		if profile == None: profile = LauncherProfile()
			
		def on_profile_save(profile):
			self.saveProfile(profile)
			self.loadProfiles(profile.id)
			
		def on_profile_delete(profile):
			self.deleteProfile(profile)
			self.loadProfiles(None)
			
		profileEditor = ProfileDialog(profile)
		profileEditor.profileSaveSignal.connect(on_profile_save)
		profileEditor.profileDeleteSignal.connect(on_profile_delete)
		profileEditor.show()
		
	def getSelectedProfile(self):
		selectedIndex = self.profileComboBox.currentIndex()
		if selectedIndex < 0:
			return None
		return self.launcherProfiles[selectedIndex]
		
	def saveProfile(self, profile):
		launcherProfiles = {}
		if (os.path.exists(self.minecraftDir + "/launcher_profiles.json")):
			with open(self.minecraftDir + "/launcher_profiles.json") as f:
				launcherProfiles = json.loads(f.read())
				f.close()
		if 'profiles' not in launcherProfiles:
			launcherProfiles['profiles'] = {}
		launcherProfiles['profiles'][profile.id] = profile.getData()
		
		os.makedirs(self.minecraftDir, 0o777, True)
		f = open(self.minecraftDir + "/launcher_profiles.json", "w")
		f.write(json.dumps(launcherProfiles, indent=4))
		f.close()
		
	def deleteProfile(self, profile):
		if (os.path.exists(self.minecraftDir + "/launcher_profiles.json")):
			with open(self.minecraftDir + "/launcher_profiles.json") as f:
				launcherProfiles = json.loads(f.read())
				f.close()
				if 'profiles' in launcherProfiles:
					launcherProfiles['profiles'].pop(profile.id)
					os.makedirs(self.minecraftDir, 0o777, True)
					f = open(self.minecraftDir + "/launcher_profiles.json", "w")
					f.write(json.dumps(launcherProfiles, indent=4))
					f.close()
		
		
	def loadProfiles(self, selectedId):
		self.launcherProfiles = []
		if (os.path.exists(self.minecraftDir + "/launcher_profiles.json")):
			with open(self.minecraftDir + "/launcher_profiles.json") as f:
				storedProfiles = json.loads(f.read())['profiles']
				f.close()
			for profileId in storedProfiles:
				profileData = storedProfiles[profileId]
				if ('type' in profileData and profileData['type'] == "custom"):
					self.launcherProfiles.append(LauncherProfile(profileId, profileData))
		
		selectedIndex = -1
		self.profileComboBox.clear()
		for i in range(len(self.launcherProfiles)):
			launcherProfile = self.launcherProfiles[i]
			if launcherProfile.id == selectedId:
				selectedIndex = i
			name = launcherProfile.name
			self.profileComboBox.addItem(name)
		if selectedIndex > -1:
			self.profileComboBox.setCurrentIndex(selectedIndex)
		
		self.log("Loaded " + str(len(self.launcherProfiles)) + " profiles")
		
	def play(self, forceInstall=False, forceOffline=False):
		
		if forceInstall:
			reply = QMessageBox.question(self, 'Force Install', (
				'If you force the re-installation any running instances will crash!\n'
				'Make sure you save and close any running instance\n'
				'Are you sure you want to continue?'),
				QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
			if reply == QMessageBox.Cancel:
				return
		
		selectedProfile = self.getSelectedProfile()
		if selectedProfile == None:
			errorDialog = QErrorMessage()
			errorDialog.showMessage("No profile selected, please create one.")
			errorDialog.exec_()
			return
		
		self.launcherSettings['selectedProfileId'] = selectedProfile.id
		
		options = {}
		useMSA = self.useMsAccount.isChecked()
		
		self.log("Using MSA: " + str(useMSA))
		if (useMSA):
			self.log("UNIMPLEMENTED")
			# TODO ms auth
		else:
			playerName = str(self.playerField.text().strip())
			if (len(playerName) == 0):
				errorDialog = QErrorMessage()
				errorDialog.showMessage("You must set a Player name!")
				errorDialog.exec_()
				return
			
			playerUuid = self.launcherSettings['uuid']
			if not forceOffline:
				uuidR = requests.get("https://api.mojang.com/users/profiles/minecraft/" + playerName).text
				if len(uuidR) != 0:
					uuidJ = json.loads(uuidR)
					playerUuid = uuidJ['id']
				
			self.log("Player: " + playerName + " (UUID: " + playerUuid + ")")
			self.launcherSettings['playerName'] = playerName
			self.launcherSettings['uuid'] = playerUuid
			options['username'] = playerName
			options['uuid'] = playerUuid
		
		# save settings with playerName, UUID and selectedProfileId
		self.saveLauncherSettings()
		
		if selectedProfile.gameDir != None:
			options['gameDirectory'] = selectedProfile.gameDir
		if selectedProfile.javaDir != None:
			options['executablePath'] = selectedProfile.javaDir
		if selectedProfile.javaArgs != None:
			options['jvmArguments'] = selectedProfile.javaArgs.split()
		options['customResolution'] = True
		options['resolutionWidth'] = str(selectedProfile.width)
		options['resolutionHeight'] = str(selectedProfile.height)
		
		self.playButton.setEnabled(False)
		self.playOpts.setEnabled(False)
		
		
		def _install_thread_finished() -> None:
			command = minecraft_launcher_lib.command.get_minecraft_command(selectedProfile.lastVersionId, self.minecraftDir, options)

			self.log("Launching Minecraft ("+selectedProfile.lastVersionId+")...")
		
			arguments = command[1:]
			command = options['executablePath'] if 'executablePath' in options else 'java'
		
			gameLog = GameOutputWidget()
			gameLog.execute_command(command, arguments)
			index = self.tabs.addTab(gameLog, selectedProfile.name)
			self.tabs.setCurrentIndex(index)
			self.playButton.setEnabled(True)
			self.playOpts.setEnabled(True)
			
		versionInstalled = False
		for version in minecraft_launcher_lib.utils.get_installed_versions(self.minecraftDir):
			if version['id'] == selectedProfile.lastVersionId:
				versionInstalled = True
				break
			
		if forceInstall or not versionInstalled:
			self.log("Installing Minecraft ("+selectedProfile.lastVersionId+")...")
			self._install_thread = InstallThread()
			self._install_thread.progress_max.connect(lambda maximum: self.installationProgress.setMaximum(maximum))
			self._install_thread.progress.connect(lambda value: self.installationProgress.setValue(value))
			self._install_thread.text.connect(lambda text: self.installationProgress.setFormat(text))
			self._install_thread.errorSignal.connect(lambda error: self.log(error, "error"))
			
			self._install_thread.finished.connect(_install_thread_finished)
			self._install_thread.set_data(selectedProfile.lastVersionId, self.minecraftDir)
			self._install_thread.start()
			self.installationProgress.show()
		else:
			_install_thread_finished()
				
	def changeAccountType(self):
		if (self.useMsAccount.isChecked()):
			self.loginContainer.show()
			self.noPremiumContainer.hide()
		else:
			self.loginContainer.hide()
			self.noPremiumContainer.show()
		self.launcherSettings['useMSA'] = self.useMsAccount.isChecked()
		self.saveLauncherSettings()
	
	def saveLauncherSettings(self):
		os.makedirs(self.minecraftDir, 0o777, True)
		f = open(self.minecraftDir + "/real_mc_launcher.json", "w")
		f.write(json.dumps(self.launcherSettings, indent=4))
		f.close()
		
	def log(self, msg, type="info"):
		msg = "{:[%Y-%m-%d %I:%M:%S]} [{}]: {} ".format(datetime.now(), type, msg)
		print(msg)
		if type == "error":
			self.launcherLog.appendHtml("<span style='color: red;'>" + msg + "</span>")
		else:
			self.launcherLog.appendPlainText(msg)
	
	ignoreCloseEvent = False
	def closeEvent(self, event):
		if self.ignoreCloseEvent:
			event.accept()
			return
		runningTabs = []
		for i in range(self.tabs.count()):
			tab = self.tabs.widget(i)
			if not isinstance(tab, GameOutputWidget):
				continue
			if tab.isRunning:
				runningTabs.append(self.tabs.tabText(i))
		
		if len(runningTabs) == 0:
			event.accept()
			sys.exit()
		else:
			event.ignore()
			def on_close_signal(close):
				if close:
					# we cant use event.accept() cause we already ignored it
					self.ignoreCloseEvent = True
					self.close()
					sys.exit()
				else:
					self.sysTray.show()
					self.hide()
					
			closeDialog = CloseDialog(self, runningTabs)
			closeDialog.closeSignal.connect(on_close_signal)
			closeDialog.show()

if __name__ == '__main__':
	app = QApplication([])
	# this allows us to call self.hide() without terminating the app
	# side effect of this is we have to close by calling sys.exit()
	app.setQuitOnLastWindowClosed(False)

	mainWindow = MainWindow()
	mainWindow.show()
		
	sys.exit(app.exec_())
	
	
	
	
	
		

