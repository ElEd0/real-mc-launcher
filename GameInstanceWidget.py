from PyQt5.QtCore import QThread, QProcess, pyqtSignal
from PyQt5.QtWidgets import QPlainTextEdit

import os, platform, tempfile, threading

class GameInstanceWidget(QPlainTextEdit):
	def __init__(self):
		super().__init__()
		self.setReadOnly(True)
		self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
		self.startDetached = platform.system() != "Windows"
		self.isRunning = False
		self.gameThread = None

	def onProcessRead(self):
		self.log(bytes(self.process.readAll()).decode())
		
	def onProcessFinished(self, exitCode):
		self.isRunning = False
		self.log("Minecraft process finished (" + str(exitCode) + ")\n")
	
	def log(self, output):
		cursor = self.textCursor()
		cursor.movePosition(cursor.MoveOperation.End)
		cursor.insertText(output)
		cursor.movePosition(cursor.MoveOperation.End)
		self.ensureCursorVisible()
		
	def execute_command(self, command, arguments):
		self.setPlainText("")
		
		if self.startDetached:
			self.gameThread = GameThread(command, arguments)
			self.gameThread.outputSignal.connect(lambda output: self.log(output))
			self.gameThread.finishedSignal.connect(self.onProcessFinished)
			self.gameThread.start()
		else:
			self.process = QProcess()
			self.process.readyRead.connect(lambda: self.log(bytes(self.process.readAll()).decode()))
			self.process.finished.connect(self.onProcessFinished)
			self.process.start(command, arguments)
		self.isRunning = True
		
	def stopThread(self):
		if self.gameThread != None:
			self.gameThread.stop()

class GameThread(QThread):
	outputSignal = pyqtSignal(str)
	finishedSignal = pyqtSignal(int)

	def __init__(self, command, arguments) -> None:
		QThread.__init__(self)
		self.command = command
		self.arguments = arguments
		self.fifo = None
		self.mustStop = False

	def run(self) -> None:
		
		try:
			separator = "\\" if platform.system() == "Windows" else "/" 
			self.pipePath = tempfile._get_default_tempdir() + separator + next(tempfile._get_candidate_names())
			
			self.arguments.append(">" + self.pipePath) # redirect stdout to pipe
			self.arguments.append("2>&1") # redirect stderr to stdout
			
			if platform.system() == "Windows":
				# TODO make windows named pipe
				self.arguments.append(" & del " + self.pipePath)
			else:
				os.mkfifo(self.pipePath) # this only works on Linux
				self.arguments.append("; rm " + self.pipePath)
			
			# Previous implementation used QProcess but QProcess sucks hard:
			# Using basic daemon thread and os.system() to spawn the minecraft instance 
			# we can detach the process without it blocking untill stdout is being read
			# We can also append and extra command at the end
			# so the pipe gets deleted when the minecraft instance quits
			
			finalCommand = self.command + " " + ' '.join(self.arguments)
			
			class GameDaemonThread(threading.Thread):
				def run(self):
					os.system(finalCommand)

			gameDaemon = GameDaemonThread()
			gameDaemon.daemon = True
			gameDaemon.start()
			
			with open(self.pipePath, "r") as fifo:
				self.fifo = fifo
				for line in self.fifo:
					if self.mustStop:
						break
					self.outputSignal.emit(line)
			
			self.fifo.close()
			self.finishedSignal.emit(0)
			
		except Exception as e:
			self.outputSignal.emit(str(e))
			self.finishedSignal.emit(1)
		
	def stop(self):
		self.mustStop = True
		if self.fifo != None:
			try:
				# write to pipe to unlock reading loop
				with open(self.pipePath, "w") as fifo:
					fifo.write("Closing")
					fifo.flush()
					fifo.close()
			except Exception as e:
				pass
		self.quit()
 
