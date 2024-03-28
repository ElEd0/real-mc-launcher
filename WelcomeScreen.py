from PyQt5.QtCore import QDir
from PyQt5.QtWidgets import (QHBoxLayout, QVBoxLayout, QFrame, QScrollArea,
		QWidget, QPushButton, QLabel)

import os
import minecraft_launcher_lib

class QLink(QLabel):
	def __init__(self, text, link):
		super().__init__("<a href=" + link + ">" + text + "</a>")
		self.setOpenExternalLinks(True)

class WelcomeScreen(QScrollArea):
	
	def __init__(self, parent=None):
		super(WelcomeScreen, self).__init__(parent)
		
		QDir.addSearchPath('images', os.path.dirname(os.path.realpath(__file__)) + "/img")
		
		self.setObjectName("body")
		self.setStyleSheet("""
			QFrame {
				background-image: url(images:bg_main.png);
			}
			QLabel {
				color: white;
				background: rgba(0, 0, 0, 0);
			}
			QLabel#header {
				font-size: 22px;
				font-weight: bold;
			}
			QLabel#subheader {
				font-size: 16px;
				font-weight: bold;
			}
			QLabel#subsubheader {
				font-size: 14px;
				font-weight: bold;
			}
		""")
		
		welcome = QLabel("Welcome to REAL Minecraft Launcher")
		welcome.setObjectName("header")
		description = QLabel("A FOSS minecraft launcher designed from the ground up to mimic the old launcher")
		description.setObjectName("description")
		
		featuresHeader = QLabel("Main features")
		featuresHeader.setObjectName("subheader")
		features = QLabel((" · Simple and intuitive UI\n"
						  " · Old-style profiles compatible with new launcher (official)\n"
						  " · Open multiple game instances\n"
						  " · Free of microsoft adware, spyware, bloatware and other BS\n"))
		
		changelogHeader = QLabel("Launcher changelog")
		changelogHeader.setObjectName("subheader")
		
		changelog = {
			"1.1.0": [
				"Detached Minecraft process (Linux)",
				"Delete profile button"
			],
			"1.0.0": [
				"First functional pre-release"
			]
		}
		
		left = QVBoxLayout()
		left.addWidget(welcome)
		left.addWidget(description)
		left.addWidget(featuresHeader)
		left.addWidget(features)
		left.addWidget(changelogHeader)
		
		for sub in changelog:
			subLabel = QLabel(sub)
			subLabel.setObjectName("subsubheader")
			left.addWidget(subLabel)
			for entry in changelog[sub]:
				entryLabel = QLabel(" · " + entry)
				left.addWidget(entryLabel)
		
		left.addStretch()
		
		
		linksLabel = QLabel("Links")
		linksLabel.setObjectName("subheader")
		
		repo = QLink("Github", "https://github.com/ElEd0/real-mc-launcher")
		ed0es = QLink("My webpage", "https://ed0.es")
		mcLauncherLib = QLink("JakobDev's minecraft-launcher-lib", "https://gitlab.com/JakobDev/minecraft-launcher-lib")
		mcLauncherApi = QLink("Tomsik68's mclauncher-api", "https://github.com/tomsik68/mclauncher-api/wiki")
		minecraftnet = QLink("Minecraft.net", "https://www.minecraft.net")
		
		right = QVBoxLayout()
		right.addWidget(linksLabel)
		right.addWidget(repo)
		right.addWidget(ed0es)
		right.addWidget(mcLauncherLib)
		right.addWidget(mcLauncherApi)
		right.addWidget(minecraftnet)
		right.addStretch()
		
		mainLayout = QHBoxLayout()
		mainLayout.addLayout(left)
		mainLayout.addStretch()
		mainLayout.addLayout(right)
		
		qFrame = QFrame()
		qFrame.setLayout(mainLayout)
		self.setWidget(qFrame)
		
		
		