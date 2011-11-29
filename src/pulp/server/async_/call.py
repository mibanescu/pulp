# -*- coding: utf-8 -*-
#
# Copyright © 2011 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

import copy
import logging
import pickle
from datetime import timedelta
from types import NoneType, TracebackType


_LOG = logging.getLogger(__name__)

# call states ------------------------------------------------------------------

CALL_UNKNOWN = 'unknown'
CALL_WAITING = 'waiting'
CALL_RUNNING = 'running'
CALL_SUSPENDED = 'suspended'
CALL_FINISHED = 'finished'
CALL_ERROR = 'error'
CALL_TIMED_OUT = 'timed out'
CALL_CANCELED = 'canceled'

CALL_STATES = (CALL_UNKNOWN,
               CALL_WAITING,
               CALL_RUNNING,
               CALL_SUSPENDED,
               CALL_FINISHED,
               CALL_ERROR,
               CALL_TIMED_OUT,
               CALL_CANCELED)

CALL_READY_STATES = (CALL_WAITING,)
CALL_INCOMPLETE_STATES = (CALL_WAITING, CALL_RUNNING, CALL_SUSPENDED)
CALL_COMPLETE_STATES = (CALL_FINISHED, CALL_ERROR, CALL_TIMED_OUT, CALL_CANCELED)

# call request class -----------------------------------------------------------

class CallRequest(object):
    """
    Call request class
    Represents an asynchronous call request
    @ivar call: python callable
    @type call: callable
    @ivar args: list of positional arguments for the callable
    @type args: list
    @ivar kwargs: dictionary of keyword arguments for the callable
    @type kwargs: dict
    @ivar resources: dictionary of resources and operations used by the request
    @type resources: dict
    @ivar weight: weight of callable in relation concurrency resources
    @type weight: int
    @ivar timeout: maximum amount of time to allow callable to run
    @type timeout: None or timedelta
    @ivar exec_hooks: callbacks to be executed during lifecycle of callable
    @type exec_hooks: dict
    @ivar ctl_hooks: callbacks used to control the lifecycle of the callable
    @type ctl_hooks: dict
    @ivar tags: list of arbitrary tags
    @type tags: list
    """

    def __init__(self,
                 call,
                 args=None,
                 kwargs=None,
                 resources=None,
                 weight=1,
                 timeout=None,
                 exec_hooks=None,
                 ctl_hooks=None,
                 tags=None):

        assert callable(call)
        assert isinstance(args, (NoneType, tuple, list))
        assert isinstance(kwargs, (NoneType, dict))
        assert isinstance(resources, (NoneType, dict))
        assert isinstance(weight, int)
        assert isinstance(timeout, (NoneType, timedelta))
        assert isinstance(exec_hooks, (NoneType, dict))
        assert isinstance(ctl_hooks, (NoneType, dict))
        assert isinstance(tags, (NoneType, tuple, list))

        self.call = call
        self.args = args or []
        self.kwargs = kwargs or {}
        self.resources = resources or {}
        self.weight = weight
        self.timeout = timeout
        self.exec_hooks = exec_hooks or {}
        self.ctl_hooks = ctl_hooks or {}
        self.tags = tags or []

    def __str__(self):

        def _name():
            name = self.call.__name__
            if hasattr(self.call, 'im_class'):
                class_name = self.call.im_class.__name__
                return '.'.join((class_name, name))
            return name

        def _args():
            return ', '.join([str(a) for a in self.args])

        def _kwargs():
            return ', '.join(['='.join((str(k), str(v)))
                              for k, v in self.kwargs.items()])

        return 'CallRequest: %s(%s, %s)' % (_name(), _args(), _kwargs())

    # call request serialization/deserialization -------------------------------

    _pickled_fields = ('call', 'args', 'kwargs', 'timeout', 'exec_hooks', 'ctl_hooks')
    _copied_fields = ('resources', 'weight', 'tags')

    def serialize(self):
        """
        Serialize the call request into a format that can be stored
        @return: serialized call request
        @rtype: dict
        """

        data = {}

        try:
            for field in self._pickled_fields:
                data[field] = pickle.dumps(getattr(self, field))
            for field in self._copied_fields:
                data[field] = getattr(self, field)

        except Exception, e:
            _LOG.exception(e)
            return None

        return data

    @classmethod
    def deserialize(cls, data):
        """
        Deserialize the data returned from a serialize call into a call request
        @param data: serialized call request
        @type data: dict
        @return: deserialized call request
        @rtype: CallRequest
        """

        constructor_kwargs = copy.copy(data)

        try:
            for field in cls._pickled_fields:
                constructor_kwargs[field] = pickle.loads(data[field])

        except Exception, e:
            _LOG.exception(e)
            return None

        instance = cls(**constructor_kwargs)
        return instance

# call report class ------------------------------------------------------------

class CallReport(object):
    """
    Call report class
    Represents a call request's progress
    @ivar response: state of request in concurrency system
    @type response: str
    @ivar reason: dictionary of resources and operations related to the response
    @type reason: dict
    @ivar state: state of callable in its lifecycle
    @type state: str
    @ivar task_id: identity of task executing call
    @type task_id: str
    @ivar job_id: identy of job the call is a part of
    @type job_id: str
    @ivar progress: dictionary of progress information
    @type progress: dict
    @ivar return_value: return value of the callable, if any
    @type return_value: any
    @ivar exception: exception from callable, if any
    @type exception: Exception
    @ivar traceback: traceback from callable, if any
    @type traceback: TracebackType
    """

    def __init__(self,
                 response=None,
                 reason=None,
                 state=None,
                 task_id=None,
                 job_id=None,
                 progress=None,
                 return_value=None,
                 exception=None,
                 traceback=None):

        assert isinstance(response, (NoneType, basestring))
        assert isinstance(reason, (NoneType, dict))
        assert isinstance(state, (NoneType, basestring))
        assert isinstance(task_id, (NoneType, basestring))
        assert isinstance(job_id, (NoneType, basestring))
        assert isinstance(progress, (NoneType, dict))
        # NOTE return_value can be anything
        assert isinstance(exception, (NoneType, Exception))
        assert isinstance(traceback, (NoneType, TracebackType))

        self.response = response or CALL_UNKNOWN
        self.reason = reason or {}
        self.state = state or CALL_UNKNOWN
        self.task_id = task_id
        self.job_id = job_id
        self.progress = progress or {}
        self.return_value = return_value
        self.exception = exception
        self.traceback = traceback
