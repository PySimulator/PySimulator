#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Copyright (C) 2011-2014 German Aerospace Center DLR
(Deutsches Zentrum fuer Luft- und Raumfahrt e.V.),
Institute of System Dynamics and Control
All rights reserved.

This file is part of PySimulator.

PySimulator is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

PySimulator is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with PySimulator. If not, see www.gnu.org/licenses.
'''

from PySide import QtCore, QtGui
import Queue


class inputLine(QtGui.QLineEdit):
    commandEntered = QtCore.Signal(str)

    def __init__(self, parent=None):
        QtGui.QLineEdit.__init__(self, parent)

        self.history = list()
        self.current = -1

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Up:
            self.current = (self.current + 1) % len(self.history)
            self.setText(self.history[len(self.history) - self.current - 1])
            event.accept()
        elif event.key() == QtCore.Qt.Key_Down:
            self.current = (self.current - 1) % len(self.history)
            self.setText(self.history[len(self.history) - self.current - 1])
            event.accept()
        elif event.key() == QtCore.Qt.Key_Return:
            self.history.append(self.text())
            self.commandEntered.emit(self.text())
            self.clear()
            self.current = -1
            event.accept()
        else:
            QtGui.QLineEdit.keyPressEvent(self, event)


class WindowConsole(QtGui.QWidget):
    ''' Class to write stdout prints to the QTextEdit textField  '''
    env_local = dict()
    echo = True
    buffer = Queue.Queue()

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setLayout(QtGui.QGridLayout(self))
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.out = QtGui.QTextEdit(self)
        self.layout().addWidget(self.out, 0, 0)
        self.out.setStyleSheet("QTextEdit { background-color: white; color: black; font-weight: normal; }")
        self.out.setReadOnly(True)
        self.input = inputLine()
        self.layout().addWidget(self.input, 1, 0)
        self.input.commandEntered.connect(self.commandEntered)
        self.consoleAccessMutex = QtCore.QMutex()

    '''
    def addCommand(self, name, function):
        self.env_global[name] = function
    '''

    def scrollDown(self):
        sb = self.out.verticalScrollBar()
        sb.setValue(sb.maximum())

    def commandEntered(self, command):
        if len(command) == 0:
            return
        if self.echo:
            print(">> " + command)
        try:
            bcode = compile(command, '<string>', 'exec')
            exec(bcode, self.env_local)  # , self.env_global)
        except Exception as e:
            print e

    def write(self, text):
        self.buffer.put(text)
        self.update()
        return

    def paintEvent(self, event):
        if self.buffer.empty():
            return
        cursor = self.out.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)
        self.out.setTextCursor(cursor)
        while not self.buffer.empty():
            self.out.insertPlainText(self.buffer.get())
        self.scrollDown()
