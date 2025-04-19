import sys
import os
import subprocess
import shutil
import webbrowser
import re
from datetime import datetime
import io
import signal
import json

try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'])
    import requests

import zipfile
try:
    from PySide6.QtWidgets import QApplication, QWizard, QWizardPage, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QFileDialog, QTextEdit, QComboBox, QMessageBox, QProgressBar, QCheckBox
    from PySide6.QtGui import QPalette, QColor, QIcon
    from PySide6.QtCore import Qt, QProcess, QTimer
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'PySide6'])
    from PySide6.QtWidgets import QApplication, QWizard, QWizardPage, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QFileDialog, QTextEdit, QComboBox, QMessageBox, QProgressBar, QCheckBox
    from PySide6.QtGui import QPalette, QColor, QIcon
    from PySide6.QtCore import Qt, QProcess, QTimer

try:
    import psutil
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psutil'])
    import psutil

HASHCAT_DOWNLOAD_PAGE = 'https://hashcat.net'

class HashcatWizard(QWizard):
    def config_path(self):
        return os.path.join(os.path.expanduser('~'), '.wifycat_config.json')
    def load_config(self):
        try:
            with open(self.config_path(), 'r') as f:
                data = json.load(f)
                path = data.get('exe_path')
                if path and os.path.exists(path):
                    self.exe_path = path
                hf = data.get('hash_file')
                self.hash_file = hf if hf and os.path.exists(hf) else ''
                wf = data.get('wordlist_file')
                self.wordlist_file = wf if wf and os.path.exists(wf) else ''
        except:
            pass
    def save_config(self):
        try:
            with open(self.config_path(), 'w') as f:
                json.dump({'exe_path': self.exe_path, 'hash_file': getattr(self, 'hash_file', ''), 'wordlist_file': getattr(self, 'wordlist_file', '')}, f)
        except:
            pass
    def set_hashcat_path(self, path):
        self.exe_path = path
        self.hashcatPathLine.setText(path)
        self.save_config()

    def __init__(self):
        super().__init__()
        self.setWindowTitle('WifyCat')
        self.setWizardStyle(QWizard.ModernStyle)
        self.exe_path = None
        self.load_config()
        self.setOption(QWizard.NoBackButtonOnLastPage, True)
        self.setOption(QWizard.NoCancelButtonOnLastPage, True)
        self.addPage(self.create_hashcat_page())
        self.addPage(self.create_hash_page())
        self.addPage(self.create_wordlist_page())
        self.addPage(self.create_rule_page())
        self.addPage(self.create_output_page())
        self.addPage(self.create_settings_page())
        self.addPage(self.create_summary_page())
        self.currentIdChanged.connect(self.on_page_changed)

    def create_hashcat_page(self):
        page = QWizardPage()
        page.setTitle('Hashcat Setup')
        layout = QVBoxLayout()
        btnInstall = QPushButton('Install Hashcat')
        btnInstall.clicked.connect(self.install_hashcat)
        btnLocate = QPushButton('Locate Hashcat')
        btnLocate.clicked.connect(self.locate_hashcat)
        self.hashcatPathLine = QLineEdit()
        self.hashcatPathLine.setReadOnly(True)
        if self.exe_path:
            self.hashcatPathLine.setText(self.exe_path)
        layout.addWidget(btnInstall)
        layout.addWidget(btnLocate)
        layout.addWidget(QLabel('Hashcat Executable Path:'))
        layout.addWidget(self.hashcatPathLine)
        page.setLayout(layout)
        return page

    def create_hash_page(self):
        page = QWizardPage()
        page.setTitle('Select Hash File')
        layout = QHBoxLayout()
        self.hashLine = QLineEdit()
        if getattr(self, 'hash_file', ''):
            self.hashLine.setText(self.hash_file)
        btnBrowse = QPushButton('Browse')
        btnBrowse.clicked.connect(self.browse_hash)
        layout.addWidget(QLabel('Hash File:'))
        layout.addWidget(self.hashLine)
        layout.addWidget(btnBrowse)
        page.setLayout(layout)
        return page

    def create_wordlist_page(self):
        page = QWizardPage()
        page.setTitle('Select Wordlist')
        layout = QHBoxLayout()
        self.wordLine = QLineEdit()
        if getattr(self, 'wordlist_file', ''):
            self.wordLine.setText(self.wordlist_file)
        btnBrowse = QPushButton('Browse')
        btnBrowse.clicked.connect(self.browse_wordlist)
        layout.addWidget(QLabel('Wordlist:'))
        layout.addWidget(self.wordLine)
        layout.addWidget(btnBrowse)
        page.setLayout(layout)
        return page

    def create_rule_page(self):
        page = QWizardPage()
        page.setTitle('Select Rule')
        layout = QVBoxLayout()
        self.ruleCombo = QComboBox()
        self.ruleCombo.setMaxVisibleItems(8)
        layout.addWidget(QLabel('Rule File:'))
        layout.addWidget(self.ruleCombo)
        page.setLayout(layout)
        return page

    def create_output_page(self):
        page = QWizardPage()
        page.setTitle('Select Output Destination')
        layout = QHBoxLayout()
        self.outputLine = QLineEdit()
        if getattr(self, 'hash_file', ''):
            name = os.path.splitext(os.path.basename(self.hash_file))[0]
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_output = os.path.join(os.path.dirname(self.hash_file), f"{name}_{ts}.txt")
            self.outputLine.setText(default_output)
        btnBrowseOutput = QPushButton('Browse')
        btnBrowseOutput.clicked.connect(self.browse_output)
        layout.addWidget(QLabel('Output File:'))
        layout.addWidget(self.outputLine)
        layout.addWidget(btnBrowseOutput)
        page.setLayout(layout)
        return page

    def create_settings_page(self):
        page = QWizardPage()
        page.setTitle('Attack Settings')
        layout = QVBoxLayout()
        hl0 = QHBoxLayout()
        hl0.addWidget(QLabel('Hash Mode:'))
        self.hashModeCombo = QComboBox()
        self.hashModeCombo.addItem('Auto-detect', '')
        self.hashModeCombo.addItem('WPA/WPA2 (HCCAPX) 2500', '2500')
        self.hashModeCombo.addItem('WPA3 (22000)', '22000')
        self.hashModeCombo.addItem('MD5 (0)', '0')
        self.hashModeCombo.addItem('SHA1 (100)', '100')
        hl0.addWidget(self.hashModeCombo)
        layout.addLayout(hl0)
        hl = QHBoxLayout()
        hl.addWidget(QLabel('Attack Mode:'))
        self.modeCombo = QComboBox()
        for name, val in [('Straight','0'),('Combination','1'),('Brute Force','3'),('Hybrid WL+Mask','6'),('Hybrid Mask+WL','7')]:
            self.modeCombo.addItem(name, val)
        hl.addWidget(self.modeCombo)
        layout.addLayout(hl)
        hl2 = QHBoxLayout()
        hl2.addWidget(QLabel('Workload Profile:'))
        self.workloadCombo = QComboBox()
        for i in range(1,5):
            self.workloadCombo.addItem(str(i), str(i))
        hl2.addWidget(self.workloadCombo)
        layout.addLayout(hl2)
        self.optimizedCheck = QCheckBox('Use optimized kernel')
        layout.addWidget(self.optimizedCheck)
        self.cpuOnlyCheck = QCheckBox('CPU-only mode')
        layout.addWidget(self.cpuOnlyCheck)
        layout.addWidget(QLabel('Additional args:'))
        self.extraArgsLine = QLineEdit()
        self.extraArgsLine.setPlaceholderText('e.g. --session mysession --restore')
        layout.addWidget(self.extraArgsLine)
        page.setLayout(layout)
        return page

    def create_summary_page(self):
        page = QWizardPage()
        page.setTitle('Summary and Run')
        layout = QVBoxLayout()
        self.summaryText = QTextEdit()
        self.summaryText.setReadOnly(True)
        self.runButton = QPushButton('Run Attack')
        self.runButton.clicked.connect(self.start_attack)
        self.pauseButton = QPushButton('Pause')
        self.pauseButton.clicked.connect(self.pause_attack)
        self.pauseButton.hide()
        self.playButton = QPushButton('Resume')
        self.playButton.clicked.connect(self.resume_attack)
        self.playButton.hide()
        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 100)
        self.progressBar.hide()
        self.etaLabel = QLabel('ETA: --')
        layout.addWidget(self.summaryText)
        layout.addWidget(self.progressBar)
        layout.addWidget(self.etaLabel)
        layout.addWidget(self.runButton)
        layout.addWidget(self.pauseButton)
        layout.addWidget(self.playButton)
        page.setLayout(layout)
        page.setFinalPage(False)
        return page

    def install_hashcat(self):
        self.hashcatPathLine.setText('Opening download page...')
        webbrowser.open(HASHCAT_DOWNLOAD_PAGE)

    def locate_hashcat(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Locate hashcat.exe', '', 'Executable (hashcat.exe)')
        if path:
            self.set_hashcat_path(path)

    def browse_hash(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Select Hash File', '', 'All Files (*.*)')
        if path:
            self.hashLine.setText(path)
            self.hash_file = path
            self.save_config()
            name = os.path.splitext(os.path.basename(path))[0]
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_output = os.path.join(os.path.dirname(path), f"{name}_{ts}.txt")
            self.outputLine.setText(default_output)
            self.next()

    def browse_wordlist(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Select Wordlist', '', 'Text Files (*.txt);;All Files (*.*)')
        if path:
            self.wordLine.setText(path)
            self.wordlist_file = path
            self.save_config()
            self.next()

    def browse_output(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Select Output File', '', 'All Files (*.*)')
        if path:
            self.outputLine.setText(path)
            self.next()

    def on_page_changed(self, id):
        if id == 3:
            self.load_rules()
        if id == 6:
            summary = f"Hashcat: {self.exe_path}\nHash Mode: {self.hashModeCombo.currentText()}\nHash file: {self.hashLine.text()}\nWordlist: {self.wordLine.text()}\nRule: {self.ruleCombo.currentData()}\nOutput: {self.outputLine.text()}\nAttack Mode: {self.modeCombo.currentText()}\nWorkload: {self.workloadCombo.currentText()}\nOptimized: {'Yes' if self.optimizedCheck.isChecked() else 'No'}\nCPU only: {'Yes' if self.cpuOnlyCheck.isChecked() else 'No'}\nAdditional args: {self.extraArgsLine.text()}"
            self.summaryText.setPlainText(summary)

    def load_rules(self):
        self.ruleCombo.clear()
        if not self.exe_path:
            return
        root = os.path.dirname(self.exe_path)
        rules = []
        for dirpath, _, files in os.walk(root):
            for f in files:
                if f.endswith('.rule'):
                    rules.append(os.path.join(dirpath, f))
        rules.sort()
        self.ruleCombo.addItem('None', '')
        descriptions = {
            'best64.rule': '64 most effective rules',
            'combinator.rule': 'concatenates all words',
            'd3ad0ne.rule': 'D3ad0ne rule set',
            'dive.rule': 'Dive rule set',
            'generated.rule': 'Generated rule set',
            'hashcat.rule': 'Default hashcat rules',
            'hybrid1.rule': 'Hybrid rule 1',
            'hybrid2.rule': 'Hybrid rule 2',
            'one.rule': 'One rule set',
            'rockyou-30000.rule': 'RockYou 30k rules',
            'toggle.rule': 'Toggle case rule set'
        }
        for rule in rules:
            name = os.path.basename(rule)
            desc = descriptions.get(name, '')
            display = f"{name} - {desc}" if desc else name
            self.ruleCombo.addItem(display, rule)

    def find_executable(self, root):
        for dirpath, _, files in os.walk(root):
            if 'hashcat.exe' in files:
                return os.path.join(dirpath, 'hashcat.exe')
        return None

    def detect_hash_mode(self):
        path = self.hashLine.text()
        ext = os.path.splitext(path)[1].lower()
        mapping = {'.hc22000': '22000', '.hccapx': '2500'}
        return mapping.get(ext, '2500')

    def supports_optimized(self, mode):
        root = os.path.dirname(self.exe_path)
        opt_kernel = os.path.join(root, 'OpenCL', f'm{mode}-optimized.cl')
        return os.path.exists(opt_kernel)

    def run_hashcat(self):
        if not self.exe_path:
            return
        mode = self.detect_hash_mode()
        cmd = [self.exe_path, '-a', '0']
        if self.supports_optimized(mode):
            cmd += ['-O']
        cmd += ['-w', '4', '-m', mode]
        rule = self.ruleCombo.currentData()
        if rule:
            cmd += ['-r', rule]
        cmd += [self.hashLine.text(), self.wordLine.text()]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=os.path.dirname(self.exe_path), text=True)
        out, _ = process.communicate()
        if "OpenCL" in out and "No such file or directory" in out:
            QMessageBox.warning(self, 'OpenCL Error', 'OpenCL runtime not found. Trying CPU-only mode...')
            fallback_cmd = [self.exe_path, '-D', '1', '-a', '0', '-m', mode]
            rule = self.ruleCombo.currentData()
            if rule:
                fallback_cmd += ['-r', rule]
            fallback_cmd += [self.hashLine.text(), self.wordLine.text()]
            fallback_proc = subprocess.Popen(fallback_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=os.path.dirname(self.exe_path), text=True)
            cpu_out, _ = fallback_proc.communicate()
            QMessageBox.information(self, 'CPU Fallback Output', cpu_out)
            return
        QMessageBox(self).information(self, 'Hashcat Output', out)

    def start_attack(self):
        if not self.exe_path:
            return
        self.runButton.setEnabled(False)
        self.runButton.hide()
        self.pauseButton.show()
        self.playButton.hide()
        self.summaryText.clear()
        self.progressBar.show()
        self.process = QProcess(self)
        self.process.setWorkingDirectory(os.path.dirname(self.exe_path))
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyRead.connect(self.on_ready_read)
        self.process.finished.connect(self.on_finished)
        mode = self.modeCombo.currentData()
        args = ['-a', mode]
        if self.optimizedCheck.isChecked():
            args += ['-O']
        workload = self.workloadCombo.currentData()
        args += ['-w', workload]
        if self.cpuOnlyCheck.isChecked():
            args += ['-D', '1']
        hashmode = self.hashModeCombo.currentData() or self.detect_hash_mode()
        args += ['-m', hashmode]
        rule = self.ruleCombo.currentData()
        if rule:
            args += ['-r', rule]
        extra = self.extraArgsLine.text().strip()
        if extra:
            args += extra.split()
        output = self.outputLine.text()
        if output:
            args += ['-o', output]
        args += ['--status', '--status-timer', '2']
        args += [self.hashLine.text(), self.wordLine.text()]
        self.process.start(self.exe_path, args)
        self.statusTimer = QTimer(self)
        self.statusTimer.setInterval(5000)
        self.statusTimer.timeout.connect(self.send_status)
        self.statusTimer.start()
        self.send_status()

    def on_ready_read(self):
        data = bytes(self.process.readAll()).decode(errors='ignore')
        self.summaryText.append(data)
        for line in data.splitlines():
            if line.startswith('Progress'):
                m = re.search(r'\((?P<p>[0-9]+(?:\.[0-9]+)?)%\)', line)
                if m:
                    self.progressBar.setValue(int(float(m.group('p'))))
            if line.startswith('Time.Estimated'):
                m = re.search(r'\((?P<e>[^)]+)\)', line)
                if m:
                    self.etaLabel.setText(f"ETA: {m.group('e')}")

    def on_finished(self, exitCode, exitStatus):
        self.progressBar.hide()
        self.pauseButton.hide()
        self.playButton.hide()
        self.runButton.show()
        self.runButton.setEnabled(True)
        self.summaryText.append(f"Finished with exit code {exitCode}")
        self.statusTimer.stop()

    def send_status(self):
        if self.process.state() != QProcess.NotRunning:
            self.process.write(b"s\r\n")

    def pause_attack(self):
        if self.process and self.process.state() != QProcess.NotRunning:
            pid = int(self.process.processId())
            if os.name == 'nt':
                psutil.Process(pid).suspend()
            else:
                os.kill(pid, signal.SIGSTOP)
        self.pauseButton.hide()
        self.playButton.show()
        self.statusTimer.stop()

    def resume_attack(self):
        if self.process and self.process.state() != QProcess.NotRunning:
            pid = int(self.process.processId())
            if os.name == 'nt':
                psutil.Process(pid).resume()
            else:
                os.kill(pid, signal.SIGCONT)
        self.playButton.hide()
        self.pauseButton.show()
        self.statusTimer.start()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'wifycat.png')))
    app.setStyle('Fusion')
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53,53,53))
    palette.setColor(QPalette.WindowText, QColor(255,255,255))
    palette.setColor(QPalette.Base, QColor(25,25,25))
    palette.setColor(QPalette.AlternateBase, QColor(53,53,53))
    palette.setColor(QPalette.ToolTipBase, QColor(255,255,255))
    palette.setColor(QPalette.ToolTipText, QColor(255,255,255))
    palette.setColor(QPalette.Text, QColor(255,255,255))
    palette.setColor(QPalette.Button, QColor(53,53,53))
    palette.setColor(QPalette.ButtonText, QColor(255,255,255))
    palette.setColor(QPalette.BrightText, QColor(255,0,0))
    palette.setColor(QPalette.Link, QColor(42,130,218))
    palette.setColor(QPalette.Highlight, QColor(42,130,218))
    palette.setColor(QPalette.HighlightedText, QColor(0,0,0))
    app.setPalette(palette)
    wizard = HashcatWizard()
    wizard.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'wifycat.png')))
    wizard.show()
    sys.exit(app.exec()) 