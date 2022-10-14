from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QIntValidator
from PyQt5.QtWidgets import (QApplication, QDialog, QErrorMessage, QMessageBox,
		QFormLayout, QHBoxLayout, QVBoxLayout, QGroupBox,
		QPushButton, QLabel, QComboBox, QCheckBox, QLineEdit)

import os
import minecraft_launcher_lib
from LauncherProfile import LauncherProfile

class ProfileDialog(QDialog):
	profileSaveSignal = pyqtSignal(object)
	profileDeleteSignal = pyqtSignal(object)
	
	def __init__(self, profile, parent=None):
		super(ProfileDialog, self).__init__(parent)
		self.setWindowModality(Qt.ApplicationModal)
		
		self.availableVersions = minecraft_launcher_lib.utils.get_available_versions(minecraft_launcher_lib.utils.get_minecraft_directory())
		
		self.profile = profile
		self.defaultProfile = LauncherProfile()
		
		self.name = QLineEdit()
		self.name.setText(self.profile.name)
		
		self.customGameDir = QCheckBox("Game Directory:")
		self.gameDir = QLineEdit()
		self.gameDir.setText(self.profile.gameDir)
		self.customGameDir.stateChanged.connect(lambda: self.gameDir.setEnabled(self.customGameDir.isChecked()))
		self.customGameDir.setChecked(self.profile.gameDir != self.defaultProfile.gameDir)
		self.customGameDir.stateChanged.emit(self.customGameDir.checkState())
		
		self.customSize = QCheckBox("Resolution:")
		self.width = QLineEdit()
		self.height = QLineEdit()
		onlyInt = QIntValidator()
		self.width.setValidator(onlyInt)
		self.height.setValidator(onlyInt)
		self.width.setText(str(profile.width))
		self.height.setText(str(profile.height))
		self.customSize.stateChanged.connect(lambda: self.width.setEnabled(self.customSize.isChecked()))
		self.customSize.stateChanged.connect(lambda: self.height.setEnabled(self.customSize.isChecked()))
		self.customSize.setChecked(self.profile.width != self.defaultProfile.width or self.profile.height != self.defaultProfile.height)
		self.customSize.stateChanged.emit(self.customSize.checkState())
		sizeWidget = QHBoxLayout()
		sizeWidget.addWidget(self.width)
		sizeWidget.addWidget(QLabel(" X "))
		sizeWidget.addWidget(self.height)
		
		self.customLauncherVisibility = QCheckBox("Launcher Visibility")
		self.launcherVisibility = QComboBox()
		self.launcherVisibility.addItem("Close launcher when game starts")
		self.launcherVisibility.addItem("Keep the launcher open")
		self.launcherVisibility.setCurrentIndex(self.profile.launcherVisibility)
		self.customLauncherVisibility.stateChanged.connect(lambda: self.launcherVisibility.setEnabled(self.customLauncherVisibility.isChecked()))
		self.customLauncherVisibility.setChecked(self.profile.launcherVisibility != self.defaultProfile.launcherVisibility)
		self.customLauncherVisibility.stateChanged.emit(self.customLauncherVisibility.checkState())
		
		# currently not used
		self.crashAssistance = QCheckBox("Automatically ask Mojang for assistance with fixing crashes")
		self.crashAssistance.setChecked(self.profile.useHopperCrashService != self.defaultProfile.useHopperCrashService)
		
		profileInfoLayout = QFormLayout()
		profileInfoLayout.addRow(QLabel("Profile Name:"), self.name)
		profileInfoLayout.addRow(self.customGameDir, self.gameDir)
		profileInfoLayout.addRow(self.customSize, sizeWidget)
		profileInfoLayout.addRow(self.customLauncherVisibility, self.launcherVisibility)
		#profileInfoLayout.addRow(crashAssistance, None)
		
		
		self.enableSnapshots = QCheckBox("Enable snapshots")
		self.enableBeta = QCheckBox("Enable beta versions (2010-2011)")
		self.enableAlpha = QCheckBox("Enable alpha versions (2010)")
		self.enableSnapshots.setChecked(self.profile.snapshot)
		self.enableBeta.setChecked(self.profile.beta)
		self.enableAlpha.setChecked(self.profile.alpha)
		self.enableSnapshots.stateChanged.connect(self.populateVersionBox)
		self.enableBeta.stateChanged.connect(self.populateVersionBox)
		self.enableAlpha.stateChanged.connect(self.populateVersionBox)
		versionLabel = QLabel("Use Version:")
		self.versionBox = QComboBox()
		self.versionBox.setFixedWidth(250)
		versionLayout0 = QHBoxLayout()
		versionLayout0.addWidget(versionLabel)
		versionLayout0.addWidget(self.versionBox)
		versionLayout0.addStretch(1)
		
		versionLayout = QVBoxLayout()
		versionLayout.addWidget(self.enableSnapshots)
		versionLayout.addWidget(self.enableBeta)
		versionLayout.addWidget(self.enableAlpha)
		versionLayout.addLayout(versionLayout0)
		
		
		self.customJavaDir = QCheckBox("Executable:")
		self.javaDir = QLineEdit()
		self.javaDir.setText(self.profile.javaDir)
		self.customJavaDir.stateChanged.connect(lambda: self.javaDir.setEnabled(self.customJavaDir.isChecked()))
		self.customJavaDir.setChecked(self.profile.javaDir != self.defaultProfile.javaDir)
		self.customJavaDir.stateChanged.emit(self.customJavaDir.checkState())
		
		self.customJavaArgs = QCheckBox("JVM arguments:")
		self.javaArgs = QLineEdit()
		self.javaArgs.setText(self.profile.javaArgs)
		self.customJavaArgs.stateChanged.connect(lambda: self.javaArgs.setEnabled(self.customJavaArgs.isChecked()))
		self.customJavaArgs.setChecked(self.profile.javaArgs != self.defaultProfile.javaArgs)
		self.customJavaArgs.stateChanged.emit(self.customJavaArgs.checkState())
		
		javaLayout = QFormLayout()
		javaLayout.addRow(self.customJavaDir, self.javaDir)
		javaLayout.addRow(self.customJavaArgs, self.javaArgs)
		
		
		cancel = QPushButton("Cancel")
		delete = QPushButton("Delete Profile")
		save = QPushButton("Save Profile")
		cancel.clicked.connect(lambda: self.close())
		delete.clicked.connect(self.deleteProfile)
		save.clicked.connect(self.saveProfile)
		if self.profile.isNew: delete.setEnabled(False)
		
		buttonsLayout = QHBoxLayout()
		buttonsLayout.addWidget(cancel)
		buttonsLayout.addStretch(1)
		buttonsLayout.addWidget(delete)
		buttonsLayout.addWidget(save)
		
		profileInfoContainer = QGroupBox("Profile Info")
		profileInfoContainer.setLayout(profileInfoLayout)
		versionContainer = QGroupBox("Version Selection")
		versionContainer.setLayout(versionLayout)
		javaContainer = QGroupBox("Java Settings (Advanced)")
		javaContainer.setLayout(javaLayout)
		
		# main layout
		mainLayout = QVBoxLayout()
		mainLayout.addWidget(profileInfoContainer)
		mainLayout.addWidget(versionContainer)
		mainLayout.addWidget(javaContainer)
		mainLayout.addLayout(buttonsLayout)
		
		self.setLayout(mainLayout)
		self.setWindowIcon(QIcon(os.path.dirname(os.path.realpath(__file__)) + "/img/icon.png"))
		self.setWindowTitle("Profile Editor")
		
		self.populateVersionBox()
	
	
	def populateVersionBox(self):
		self.versionBox.clear()
		i = 0
		selectedIndex = -1
		for version in self.availableVersions:
			if version['type'] == "snapshot" and not self.enableSnapshots.isChecked():
				continue
			if version['type'] == "old_beta" and not self.enableBeta.isChecked():
				continue
			if version['type'] == "old_alpha" and not self.enableAlpha.isChecked():
				continue
			self.versionBox.addItem(version['id'])
			if version['id'] == self.profile.lastVersionId:
				selectedIndex = i
			i += 1
			
		if selectedIndex > -1:
			self.versionBox.setCurrentIndex(selectedIndex)
		
	def deleteProfile(self):
		reply = QMessageBox.question(self, 'Delete profile', 'Are you sure you want to delete profile '+self.profile.name+'?',
			QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
		if reply == QMessageBox.Cancel:
			return
		self.profileDeleteSignal.emit(self.profile)
		self.close()
	
	def saveProfile(self):
		name = str(self.name.text().strip())
		gameDir = str(self.gameDir.text().strip()) if self.customGameDir.isChecked() else self.defaultProfile.gameDir
		width = str(self.width.text().strip()) if self.customSize.isChecked() else self.defaultProfile.width
		height = str(self.height.text().strip()) if self.customSize.isChecked() else self.defaultProfile.height
		launcherVisibility = self.launcherVisibility.currentIndex() if self.customLauncherVisibility.isChecked() else self.defaultProfile.launcherVisibility
		
		snapshot = self.enableSnapshots.isChecked()
		beta = self.enableBeta.isChecked()
		alpha = self.enableAlpha.isChecked()
		version = self.versionBox.currentText()
		
		javaDir = str(self.javaDir.text().strip()) if self.customJavaDir.isChecked() else self.defaultProfile.javaDir
		javaArgs = str(self.javaArgs.text().strip()) if self.customJavaArgs.isChecked() else self.defaultProfile.javaArgs
		
		if (len(name) == 0):
			self.showError("Fill in the profile name")
			return
		if (len(gameDir) == 0):
			self.showError("Invalid Game directory")
			return
		if (len(javaDir) == 0):
			self.showError("Invalid Java directory")
			return
		width = 100 if width == "" else int(width)
		height = 100 if height == "" else int(height)
		if (width < 100):
			self.showError("Screen width must be at least 100")
			return
		if (height < 100):
			self.showError("Screen height must be at least 100")
			return
		
		self.profile.name = name
		self.profile.gameDir = gameDir
		self.profile.width = width
		self.profile.height = height
		self.profile.launcherVisibility = launcherVisibility
		self.profile.lastVersionId = version
		self.profile.javaDir = javaDir
		self.profile.javaArgs = javaArgs
		self.profile.snapshot = snapshot
		self.profile.beta = beta
		self.profile.alpha = alpha
		
		self.profileSaveSignal.emit(self.profile)
		self.close()
		
	def showError(self, msg):
		errorDialog = QErrorMessage(self)
		errorDialog.showMessage(msg)
		errorDialog.exec_()
		
		
		