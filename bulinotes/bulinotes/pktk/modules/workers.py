# -----------------------------------------------------------------------------
# PyKritaToolKit
# Copyright (C) 2019-2022 - Grum999
# -----------------------------------------------------------------------------
# SPDX-License-Identifier: GPL-3.0-or-later
#
# https://spdx.org/licenses/GPL-3.0-or-later.html
# -----------------------------------------------------------------------------
# A Krita plugin framework
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# The workers module provides class used to simplify some multithreading tasks
# especially to reproduce python multithreaded map() with Qt
#
# Main class from this module
#
# - WorkerPool
#       main class to manage multithreaded tasks
#
# - Worker:
#       A single worker that will do something in multithreaded process
#       Basically, WorkerPool will instanciate one Worker per thread
#
# -----------------------------------------------------------------------------

from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal,
        QEventLoop,
        QRunnable,
        QThreadPool,
        QTimer
    )

from ..pktk import *
from .timeutils import Timer


class WorkerSignals(QObject):
    processed = Signal(tuple)
    finished = Signal()
    started = Signal()


class WorkerPoolSignals(QObject):
    processed = Signal(tuple)           # an item has been processed
    finished = Signal()                 # pool has finished
    started = Signal()                  # pool has started (all workers started)


class Worker(QRunnable):
    """"A worker designed to process data from WorkerPool

    Not aimed to be instancied directly, just use WorkerPool
    """

    def __init__(self, pool, callback, *callbackArgv):
        """Initialise worker

        The given `callback` will be executed on each item from pool with given optional `*callbackArgv` arguments
        """
        super(Worker, self).__init__()
        self.__workerId = QUuid.createUuid().toString()
        self.__pool = pool
        self.__callback = callback
        self.__callbackArgv = callbackArgv
        self.__nbProcessed = 0
        self.signals = WorkerSignals()

    def id(self):
        """Return worker id"""
        return self.__workerId

    def startEvent(self):
        """Virtual; called when worker start to process"""
        pass

    def stopEvent(self):
        """Virtual; called when worker has finished"""
        pass

    def processEvent(self, itemIndex, item):
        """Virtual; called before callback is executed

        return item
        """
        return item

    def cleanupEvent(self):
        """Virtual; called when all workers have finished, just before workers
        are deleted
        """
        pass

    def nbProcessed(self):
        """Return number of items processed by worker"""
        return self.__nbProcessed

    @pyqtSlot()
    def run(self):
        """Retrieve items from pool and process it

        If there's no more item to process in list, exit
        """
        self.__nbProcessed = 0
        self.startEvent()
        self.signals.started.emit()

        while not self.__pool.stopProcessingAsked():
            # get next item from ppol
            itemIndex, item = self.__pool.getNext()
            if item is None:
                # no more item to process
                break

            # need to understand why without this print statement,
            # UI is unresponsive when long multi-threaded process is running
            # :-/
            #
            # So a "null" print allow to do a print, without printing
            print("\0", sep="", end="", flush=True)

            item = self.processEvent(itemIndex, item)

            if self.__callback is not None:
                result = self.__callback(itemIndex, item, *self.__callbackArgv)
            self.__nbProcessed += 1
            self.signals.processed.emit((itemIndex, result))

        self.stopEvent()
        self.signals.finished.emit()


class WorkerPool(QObject):
    """A worker pool allows to process data using pyqt multithreading
    """
    __MAP_MODE_OFF = 0
    __MAP_MODE_ALL = 1
    __MAP_MODE_NONONE = 2
    __MAP_MODE_AGGREGATE = 3

    def __init__(self, maxWorkerCount=None):
        super(WorkerPool, self).__init__()
        self.__threadpool = QThreadPool()
        # self.__threadpool = QThreadPool.globalInstance()

        if isinstance(maxWorkerCount, int) and maxWorkerCount >= 1 and maxWorkerCount <= self.__threadpool.maxThreadCount():
            self.__maxWorkerCount = maxWorkerCount
        else:
            self.__maxWorkerCount =  self.__threadpool.maxThreadCount()

        self.__mutex = QMutex()
        self.__nbProcessed = 0
        self.__current = 0
        self.__started = 0
        self.__allStarted = False
        self.__size = 0
        self.__nbWorkers = self.__threadpool.maxThreadCount()
        self.__workers = []
        self.__stopProcess = False
        self.__dataList = []
        self.__results = []
        self.__mapResults = WorkerPool.__MAP_MODE_OFF
        self.__workerClass = Worker

        self.signals = WorkerPoolSignals()

    def __onProcessed(self, processedNfo):
        """an item has been processed"""
        self.__nbProcessed += 1
        if self.__mapResults != WorkerPool.__MAP_MODE_OFF:
            index, item = processedNfo
            if self.__mapResults == WorkerPool.__MAP_MODE_ALL and index is not None:
                self.__results[index] = item
            elif self.__mapResults == WorkerPool.__MAP_MODE_NONONE and item is not None:
                self.__results.append(item)
            elif self.__mapResults == WorkerPool.__MAP_MODE_AGGREGATE and isinstance(item, dict):
                for key in item:
                    self.__results[key] += item[key]
        self.signals.processed.emit((processedNfo[0], processedNfo[1], self.__nbProcessed))

    def __onFinished(self):
        """Do something.. ?"""
        self.__started -= 1
        if self.__allStarted and self.__started == 0:
            for worker in self.__workers:
                worker.cleanupEvent()
            self.__workers.clear()
            self.signals.finished.emit()

    def setWorkerClass(self, workerClass=None):
        """Set worker class to use

        if None, set default Worker class
        """
        if workerClass is None:
            self.__workerClass = Worker
        else:
            self.__workerClass = workerClass

    def stopProcessingAsked(self):
        return self.__stopProcess

    def getNext(self):
        """Get next item to process"""
        self.__mutex.lock()

        if self.__current is None:
            self.__mutex.unlock()
            return (None, None)
        returnedIndex = self.__current
        self.__current += 1

        if self.__current >= self.__size:
            self.__current = None

        self.__mutex.unlock()
        return (returnedIndex, self.__dataList[returnedIndex])

    def startProcessing(self, dataList, callback, *callbackArgv):
        """Start all current thread execution"""
        # ensure to stop current processing before creating a new one
        if self.__stopProcess is True:
            return
        else:
            self.stopProcessing()

        if not (isinstance(dataList, list) or isinstance(dataList, set) or isinstance(dataList, tuple)):
            raise EInvalidType('Given `dataList` must be a list')

        self.__size = len(dataList)

        if self.__size == 0:
            return

        self.__dataList = [v for v in dataList]

        if self.__mapResults == WorkerPool.__MAP_MODE_ALL:
            self.__results = [None] * self.__size
        elif self.__mapResults != WorkerPool.__MAP_MODE_AGGREGATE:
            # already initialised by aggregate() method
            self.__results = []

        # if number of items to process is less than number of possible threads,
        # don't use all threads
        self.__nbWorkers = min(self.__size, self.__maxWorkerCount)

        self.__nbProcessed = 0
        self.__started = 0
        self.__current = 0
        self.__workers.clear()

        # for test, force to 1 thread only
        # self.__nbWorkers = 1

        self.__allStarted = False
        # initialise workers
        for index in range(self.__nbWorkers):
            self.__workers.append(self.__workerClass(self, callback, *callbackArgv))
            self.__workers[index].signals.processed.connect(self.__onProcessed)
            self.__workers[index].signals.finished.connect(self.__onFinished)
            self.__workers[index].setAutoDelete(True)

        # start workers
        for index in range(self.__nbWorkers):
            self.__started += 1
            self.__threadpool.start(self.__workers[index])

        self.__allStarted = True
        self.signals.started.emit()
        if self.__started == 0:
            self.__workers.clear()
            self.signals.finished.emit()
            self.__allStarted = False

    def stopProcessing(self):
        """Stop all current thread execution"""
        if self.__started > 0:
            self.__stopProcess = True
            while self.__started > 0:
                # check every 5ms if all thread are finished
                Timer.sleep(5)
            self.__stopProcess = False

    def waitProcessed(self):
        """Wait until all items in pool are processed"""
        # why self.__threadpool.waitForDone() don't work??
        while self.__started > 0:
            Timer.sleep(1)

    def map(self, dataList, callback, *callbackArgv):
        """Apply `callback` function to each item `datalist` list and return a list

        Similar to python map() method, but for Qt threads
            https://docs.python.org/3/library/multiprocessing.html#multiprocessing.pool.Pool.map
        """
        if len(dataList) == 0:
            return []

        self.__mapResults = WorkerPool.__MAP_MODE_ALL
        self.startProcessing(dataList, callback, *callbackArgv)
        self.waitProcessed()
        self.__mapResults = WorkerPool.__MAP_MODE_OFF
        return self.__results

    def mapNoNone(self, dataList, callback, *callbackArgv):
        """Apply `callback` function to each item `datalist` list and return a list
        If callback return None value, value is not added to result

        Similar to python map() method, but for Qt threads
            https://docs.python.org/3/library/multiprocessing.html#multiprocessing.pool.Pool.map
        """
        if len(dataList) == 0:
            return []

        self.__mapResults = WorkerPool.__MAP_MODE_NONONE
        self.startProcessing(dataList, callback, *callbackArgv)
        self.waitProcessed()
        self.__mapResults = WorkerPool.__MAP_MODE_OFF
        return self.__results

    def aggregate(self, dataList, returnedStruct, callback, *callbackArgv):
        """Apply `callback` function to each item `datalist` list and return a dictionary with aggregated
        results
        """
        if len(dataList) == 0:
            return returnedStruct

        self.__mapResults = WorkerPool.__MAP_MODE_AGGREGATE
        self.__results = returnedStruct
        self.startProcessing(dataList, callback, *callbackArgv)
        self.waitProcessed()
        self.__mapResults = WorkerPool.__MAP_MODE_OFF
        return self.__results
